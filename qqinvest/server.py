#!/usr/bin/env python3.13
"""
qqinvest Web Server — AI 投研网站后端

FastAPI + SQLite 任务队列，子进程调用 run_round1.py / run_round2.py

启动：
  cd qqinvest && python3.13 server.py
  # 访问 http://localhost:8080
"""

import asyncio
import json
import logging
import os
import queue
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── 路径配置 ─────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DB_PATH = ROOT / "jobs.db"
REPORTS_DIR = ROOT / "reports"
TRADING_AGENTS_DIR = ROOT  # run_demo_cli.py lives in the same dir

# ── Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("server")

# ── FastAPI app ───────────────────────────────────────
app = FastAPI(title="qqinvest AI 投研")

# ── SSE 队列注册表（job_id → Queue）──────────────────
sse_queues: dict[str, queue.Queue] = {}


# ── SQLite 初始化 ─────────────────────────────────────

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            params TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            progress TEXT DEFAULT '',
            result TEXT DEFAULT '',
            error TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def db_create_job(job_id: str, job_type: str, params: dict) -> None:
    now = datetime.now().isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO jobs (id, type, params, status, created_at, updated_at) VALUES (?, ?, ?, 'pending', ?, ?)",
        (job_id, job_type, json.dumps(params, ensure_ascii=False), now, now),
    )
    conn.commit()
    conn.close()


def db_update_job(job_id: str, **kwargs):
    now = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [now, job_id]
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(f"UPDATE jobs SET {sets}, updated_at = ? WHERE id = ?", values)
    conn.commit()
    conn.close()


def db_get_job(job_id: str) -> dict | None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── 任务执行（后台线程）────────────────────────────────

def run_round2_job(job_id: str, stocks: list[str]):
    """后台线程：执行 Round 2 分析。"""
    try:
        db_update_job(job_id, status="running", progress="正在采集股票数据...")

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        cmd = [sys.executable, str(ROOT / "run_round2.py")] + ["--stocks"] + stocks
        log.info(f"[{job_id[:8]}] 启动 Round2: {' '.join(stocks)}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT),
            env=env,
        )

        lines = []
        for line in proc.stdout:
            line = line.rstrip()
            lines.append(line)
            # 提取进度信息
            if any(kw in line for kw in ["处理：", "分析", "完成", "采集", "Pass", "报告"]):
                db_update_job(job_id, progress=line[-100:])

        proc.wait()

        if proc.returncode != 0:
            err = "\n".join(lines[-20:])
            db_update_job(job_id, status="failed", error=err[-500:])
            return

        # 找最新报告文件
        reports = sorted(REPORTS_DIR.glob("*round2*.md"), key=lambda p: p.stat().st_mtime)
        if not reports:
            db_update_job(job_id, status="failed", error="报告文件未生成")
            return

        report_path = reports[-1]
        result_md = report_path.read_text(encoding="utf-8")
        db_update_job(job_id, status="done", progress="分析完成", result=result_md)
        log.info(f"[{job_id[:8]}] Round2 完成，报告 {len(result_md)} 字符")

    except Exception as e:
        log.error(f"[{job_id[:8]}] Round2 异常：{e}")
        db_update_job(job_id, status="failed", error=str(e))


def run_round1_job(job_id: str, sector: str):
    """后台线程：执行 Round 1 研报。"""
    try:
        db_update_job(job_id, status="running", progress="Pass 1：正在采集行业素材...")

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        cmd = [sys.executable, str(ROOT / "run_round1.py"), "--sector", sector]
        log.info(f"[{job_id[:8]}] 启动 Round1: {sector}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT),
            env=env,
        )

        pass1_done = False
        for line in proc.stdout:
            line = line.rstrip()
            if "Pass 1" in line and "完成" in line:
                pass1_done = True
                db_update_job(job_id, progress="Pass 2：正在撰写研报（预计30-40分钟）...")
            elif "Pass 2" in line or "研报" in line:
                db_update_job(job_id, progress=f"Pass 2：{line[-80:]}")
            elif "Pass 1" in line:
                db_update_job(job_id, progress=f"Pass 1：{line[-80:]}")

        proc.wait()

        if proc.returncode != 0:
            db_update_job(job_id, status="failed", error=f"进程退出码 {proc.returncode}")
            return

        # 找最新报告文件
        reports = sorted(REPORTS_DIR.glob("*round1*.md"), key=lambda p: p.stat().st_mtime)
        if not reports:
            db_update_job(job_id, status="failed", error="报告文件未生成")
            return

        report_path = reports[-1]
        result_md = report_path.read_text(encoding="utf-8")
        db_update_job(job_id, status="done", progress="研报生成完成", result=result_md)
        log.info(f"[{job_id[:8]}] Round1 完成，报告 {len(result_md)} 字符")

    except Exception as e:
        log.error(f"[{job_id[:8]}] Round1 异常：{e}")
        db_update_job(job_id, status="failed", error=str(e))


# ── 请求模型 ──────────────────────────────────────────

class Round2Request(BaseModel):
    stocks: list[str]

class Round1Request(BaseModel):
    sector: str

class ValidateSectorRequest(BaseModel):
    sector: str

class UploadAnalysisRequest(BaseModel):
    sector: str
    content: str   # raw material text pasted/read by client

class DeepAnalysisRequest(BaseModel):
    ticker: str
    date: str = ""  # default to today if empty


def run_upload_job(job_id: str, sector: str, mat_path: str):
    """后台线程：跳过 Pass 1，直接用上传素材跑 Pass 2。"""
    try:
        db_update_job(job_id, status="running", progress="正在按方法论框架分析素材（约5-15分钟）...")

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        cmd = [
            sys.executable, str(ROOT / "run_round1.py"),
            "--sector", sector,
            "--skip-pass1",
            "--materials", mat_path,
        ]
        log.info(f"[{job_id[:8]}] 启动 Upload分析: sector={sector}, mat={mat_path}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT),
            env=env,
        )

        for line in proc.stdout:
            line = line.rstrip()
            if any(kw in line for kw in ["Pass 2", "研报", "分析", "完成", "字符"]):
                db_update_job(job_id, progress=line[-100:])

        proc.wait()

        if proc.returncode != 0:
            db_update_job(job_id, status="failed", error=f"分析失败（退出码 {proc.returncode}）")
            return

        # 找最新报告（按修改时间）
        reports = sorted(REPORTS_DIR.glob("*round1*.md"), key=lambda p: p.stat().st_mtime)
        if not reports:
            db_update_job(job_id, status="failed", error="报告文件未生成")
            return

        result_md = reports[-1].read_text(encoding="utf-8")
        db_update_job(job_id, status="done", progress="方法论对齐完成", result=result_md)
        log.info(f"[{job_id[:8]}] Upload分析完成，报告 {len(result_md)} 字符")

    except Exception as e:
        log.error(f"[{job_id[:8]}] Upload异常：{e}")
        db_update_job(job_id, status="failed", error=str(e))


def run_deep_analysis_job(job_id: str, ticker: str, date: str):
    """后台线程：in-process 调用 run_deep_analysis，通过 on_step 回调推 SSE 事件。"""
    q = sse_queues.get(job_id)

    def on_step(step_name: str, status: str, preview: str = ""):
        """将步骤事件推入 SSE 队列，同时更新 DB 进度。"""
        event = {"step": step_name, "status": status, "preview": preview[:120]}
        if q is not None:
            q.put(event)
        if status == "started":
            db_update_job(job_id, progress=f"▶ {step_name}...")
        elif status == "completed":
            db_update_job(job_id, progress=f"✓ {step_name}")

    try:
        db_update_job(job_id, status="running", progress="正在初始化分析环境...")
        log.info(f"[{job_id[:8]}] 启动深度分析: ticker={ticker}, date={date}")

        # 动态导入（避免循环导入，确保 CLAUDECODE 已从 env 清除）
        import os as _os
        _os.environ.pop("CLAUDECODE", None)

        import run_demo_cli
        result = run_demo_cli.run_deep_analysis(ticker, date, on_step=on_step)

        # 存储结果：JSON 包含 full_report + summary
        result_payload = json.dumps(
            {"full_report": result["full_report"], "summary": result.get("summary", {})},
            ensure_ascii=False,
        )

        # 拷贝到 reports/ 以便统一下载
        REPORTS_DIR.mkdir(exist_ok=True)
        (REPORTS_DIR / f"deep_{ticker}_{date}.md").write_text(result["full_report"], encoding="utf-8")

        db_update_job(job_id, status="done", progress="深度分析完成（8-Agent）", result=result_payload)
        log.info(f"[{job_id[:8]}] 深度分析完成，报告 {len(result['full_report'])} 字符")

    except Exception as e:
        log.error(f"[{job_id[:8]}] 深度分析异常：{e}")
        db_update_job(job_id, status="failed", error=str(e))
        if q is not None:
            q.put({"step": "错误", "status": "failed", "error": str(e)[:200]})
    finally:
        # 放 None 哨兵，通知 SSE 流结束
        if q is not None:
            q.put(None)


# ── API 路由 ──────────────────────────────────────────

@app.post("/api/validate-sector")
async def validate_sector(req: ValidateSectorRequest):
    """快速校验行业名称是否为合法的 A 股行业方向（<5秒）。"""
    sector = req.sector.strip()
    if not sector:
        return {"valid": False, "message": "行业名称不能为空"}
    if len(sector) > 50:
        return {"valid": False, "message": "行业名称过长（最多50字）"}

    # 基础规则校验：包含数字/英文组合可能是股票代码，拒绝
    import re
    if re.match(r"^\d{6}$", sector):
        return {"valid": False, "message": "请输入行业名称，不是股票代码"}

    # 调用 claude -p 快速判断
    prompt = (
        f"判断「{sector}」是否为中国A股市场中可以做行业投研的方向。"
        f"只回答 YES 或 NO，不要解释。"
    )
    try:
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        proc = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-haiku-4-5-20251001",
             "--output-format", "text"],
            capture_output=True, text=True, timeout=15, cwd=str(ROOT), env=env,
        )
        answer = proc.stdout.strip().upper()
        if "YES" in answer:
            return {"valid": True, "message": ""}
        else:
            return {"valid": False, "message": f"「{sector}」不是明确的A股行业方向，请重新输入（如：新能源储能、人形机器人、半导体设备）"}
    except Exception as e:
        log.warning(f"validate-sector 调用 claude 失败：{e}，默认通过")
        return {"valid": True, "message": ""}  # 降级：校验失败时放行


@app.post("/api/analyze-upload")
async def analyze_upload(req: UploadAnalysisRequest):
    """素材上传分析：跳过 Pass 1，直接用上传素材跑 Pass 2 方法论对齐。"""
    import re as _re
    sector = req.sector.strip()
    content = req.content.strip()

    if not sector:
        raise HTTPException(400, "请提供行业名称")
    if not content or len(content) < 50:
        raise HTTPException(400, "素材内容过短（至少50字）")
    if len(content) > 500_000:
        raise HTTPException(400, "素材内容过长（最多50万字符）")

    # 保存到素材目录
    slug = _re.sub(r"[（）()【】\[\]/\\]", "_", sector)[:15].strip("_")
    job_id = str(uuid.uuid4())
    mat_dir = ROOT / "素材"
    mat_dir.mkdir(exist_ok=True)
    mat_filename = f"upload_{slug}_{job_id[:8]}.md"
    mat_path = mat_dir / mat_filename
    mat_path.write_text(content, encoding="utf-8")

    db_create_job(job_id, "upload", {"sector": sector, "materials_file": str(mat_path)})
    t = threading.Thread(target=run_upload_job, args=(job_id, sector, str(mat_path)), daemon=True)
    t.start()
    log.info(f"Upload分析任务已创建：{job_id[:8]}，sector={sector}，素材 {len(content)} 字符")
    return {"job_id": job_id}


@app.post("/api/round2")
async def start_round2(req: Round2Request):
    """启动 Round 2 分析任务。"""
    import re
    stocks = [s.strip() for s in req.stocks if s.strip()]
    if not stocks:
        raise HTTPException(400, "请提供至少一个股票代码")
    if len(stocks) > 5:
        raise HTTPException(400, "最多同时分析 5 只股票")
    for code in stocks:
        if not re.match(r"^\d{6}$", code):
            raise HTTPException(400, f"股票代码格式错误：{code}（应为6位数字）")

    job_id = str(uuid.uuid4())
    db_create_job(job_id, "round2", {"stocks": stocks})
    t = threading.Thread(target=run_round2_job, args=(job_id, stocks), daemon=True)
    t.start()
    log.info(f"Round2 任务已创建：{job_id[:8]}，股票：{stocks}")
    return {"job_id": job_id}


@app.post("/api/round1")
async def start_round1(req: Round1Request):
    """启动 Round 1 行业研报任务。"""
    sector = req.sector.strip()
    if not sector:
        raise HTTPException(400, "请提供行业名称")

    job_id = str(uuid.uuid4())
    db_create_job(job_id, "round1", {"sector": sector})
    t = threading.Thread(target=run_round1_job, args=(job_id, sector), daemon=True)
    t.start()
    log.info(f"Round1 任务已创建：{job_id[:8]}，行业：{sector}")
    return {"job_id": job_id}


@app.post("/api/deep-analysis")
async def start_deep_analysis(req: DeepAnalysisRequest):
    """启动 TradingAgents 深度个股分析任务（7-Agent，~15-20分钟）。"""
    import re
    ticker = req.ticker.strip()
    if not re.match(r"^\d{6}$", ticker):
        raise HTTPException(400, f"股票代码格式错误：{ticker}（应为6位数字）")

    date = req.date.strip() or datetime.now().strftime("%Y-%m-%d")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "日期格式错误，应为 YYYY-MM-DD")

    job_id = str(uuid.uuid4())
    db_create_job(job_id, "deep", {"ticker": ticker, "date": date})
    # 注册 SSE 队列（必须在线程启动前）
    sse_queues[job_id] = queue.Queue()
    t = threading.Thread(target=run_deep_analysis_job, args=(job_id, ticker, date), daemon=True)
    t.start()
    log.info(f"深度分析任务已创建：{job_id[:8]}，ticker={ticker}，date={date}")
    return {"job_id": job_id}


@app.get("/api/job/{job_id}")
async def get_job(job_id: str):
    """查询任务状态。"""
    job = db_get_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return {
        "id": job["id"],
        "type": job["type"],
        "status": job["status"],
        "progress": job["progress"],
        "result": job["result"],
        "error": job["error"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }


@app.get("/api/jobs")
async def list_jobs():
    """列出最近20个任务。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, type, status, progress, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── SSE：深度分析实时步骤推送 ────────────────────────

@app.get("/api/deep-sse/{job_id}")
async def deep_sse(job_id: str):
    """SSE 端点：实时推送深度分析步骤进度。

    客户端用 EventSource 连接；每个步骤开始/完成时推一条事件。
    结束时推 {"done": true}。
    若任务已完成，立即推 done 事件。
    """
    job = db_get_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")

    # 如果任务已结束，立即返回 done
    if job["status"] in ("done", "failed"):
        async def immediate_done():
            payload = json.dumps({"done": True, "status": job["status"]}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        return StreamingResponse(
            immediate_done(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    q = sse_queues.get(job_id)
    if q is None:
        raise HTTPException(404, "SSE 队列不存在，任务可能已完成或未启动")

    async def event_stream():
        while True:
            try:
                event = q.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.2)
                continue

            if event is None:  # 哨兵：任务结束
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                break

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


# ── 报告文件下载 ──────────────────────────────────────

@app.get("/api/reports")
async def list_reports():
    """列出所有已生成的报告文件。"""
    REPORTS_DIR.mkdir(exist_ok=True)
    files = sorted(REPORTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        }
        for f in files
    ]

@app.get("/api/reports/{filename}")
async def download_report(filename: str):
    """下载指定报告文件。"""
    import re
    # 只允许 .md 文件，防止路径穿越
    if not re.match(r'^[\w\u4e00-\u9fff\-\.]+\.md$', filename) or ".." in filename:
        raise HTTPException(400, "非法文件名")
    path = REPORTS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "文件不存在")
    from fastapi.responses import Response
    content = path.read_bytes()
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── 静态文件 ──────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# 挂载 static 目录（index.html 由上面的路由处理）
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── 启动 ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    init_db()
    log.info(f"qqinvest 服务启动，访问 http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
