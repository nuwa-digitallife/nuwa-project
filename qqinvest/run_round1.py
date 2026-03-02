#!/usr/bin/env python3.13
"""
qqinvest Round 1 — 行业主观研报（参数化）

两阶段流程：
  Pass 1: 素材深采（sonnet，WebSearch + WebFetch，~30分钟）
  Pass 2: 行业分析报告（opus，5节方法论框架，~60分钟）

使用：
  python run_round1.py                          # 默认行业（特种机器人）
  python run_round1.py --sector "新能源储能"    # 指定行业
  python run_round1.py --pass 1                 # 只跑 Pass 1
  python run_round1.py --pass 2                 # 只跑 Pass 2（需要 Pass 1 输出）
  python run_round1.py --skip-pass1             # 跳过 Pass 1，直接用已有素材
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 路径配置 ─────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "prompts"
MATERIALS_DIR = ROOT / "素材"
REPORTS_DIR = ROOT / "reports"
DEVLOG = ROOT.parent / "logs" / "devlog.jsonl"

# ── 模型配置 ─────────────────────────────────────────
PASS1_MODEL = "claude-sonnet-4-6"
PASS2_MODEL = "claude-opus-4-6"

PASS1_TOOLS = "WebSearch,WebFetch"
PASS2_TOOLS = "WebSearch,WebFetch,Read"

PASS1_TIMEOUT = 2400   # 40分钟（素材采集可能很耗时）
PASS2_TIMEOUT = 3600   # 60分钟（opus写报告）

# ── Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("round1")


def run_claude(prompt: str, model: str, tools: str, timeout: int, label: str) -> str:
    """调用 claude -p，返回输出文本。超时或出错时抛异常。"""
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--allowedTools", tools,
        "--output-format", "text",
    ]
    log.info(f"[{label}] 启动 Claude（model={model}，timeout={timeout}s）")
    start = time.time()

    import os
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # 允许嵌套启动 claude

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(ROOT),
        env=env,
    )

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise TimeoutError(f"[{label}] 超时（{timeout}s）")

    elapsed = time.time() - start
    log.info(f"[{label}] 完成，耗时 {elapsed:.0f}s，返回码 {proc.returncode}")

    if proc.returncode != 0:
        log.error(f"[{label}] stderr: {stderr[-2000:]}")
        raise RuntimeError(f"[{label}] Claude 返回非零退出码 {proc.returncode}")

    if stderr:
        log.debug(f"[{label}] stderr（前500字）: {stderr[:500]}")

    return stdout


def save_devlog(entry: dict):
    """追加一条记录到 devlog.jsonl。"""
    try:
        DEVLOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DEVLOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning(f"devlog 写入失败：{e}")


DEFAULT_SECTOR = "特种机器人（矿山/军工/安防/电力巡检）"


def render_template(template_text: str, sector: str) -> str:
    """将模板中的 {sector} 占位符替换为实际行业名。"""
    return template_text.replace("{sector}", sector)


def sector_to_slug(sector: str) -> str:
    """将行业名转为文件名安全的短标识（取前8个字符，去掉括号）。"""
    import re
    clean = re.sub(r"[（）()【】\[\]/\\]", "_", sector)
    return clean[:20].strip("_")


def run_pass1(date_str: str, sector: str) -> Path:
    """
    Pass 1：素材深采
    输入：pass1_template.md 提示词模板（含 {sector} 占位符）
    输出：素材/research_materials_{slug}_{date}.md
    """
    # 优先用新模板，兼容旧文件
    template_file = PROMPTS_DIR / "pass1_template.md"
    if not template_file.exists():
        template_file = PROMPTS_DIR / "pass1_research.md"
    if not template_file.exists():
        raise FileNotFoundError(f"提示词文件不存在：{template_file}")

    slug = sector_to_slug(sector)
    output_file = MATERIALS_DIR / f"research_materials_{slug}_{date_str}.md"

    prompt = render_template(template_file.read_text(encoding="utf-8"), sector)

    log.info("=" * 60)
    log.info(f"Pass 1：{sector} 素材深采")
    log.info("=" * 60)

    result = run_claude(prompt, PASS1_MODEL, PASS1_TOOLS, PASS1_TIMEOUT, "Pass1")

    MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
    output_file.write_text(result, encoding="utf-8")
    log.info(f"Pass 1 输出已保存：{output_file}")
    log.info(f"Pass 1 字数：{len(result)} 字符")

    save_devlog({
        "timestamp": datetime.now().isoformat(),
        "project": "qqinvest",
        "type": "task",
        "context": f"Round 1 Pass 1 素材采集 [{sector}]",
        "action": f"完成{sector}行业素材深采，输出到 {output_file.name}",
        "result": f"输出 {len(result)} 字符",
        "insight": "",
    })

    return output_file


def run_pass2(date_str: str, materials_file: Path, sector: str) -> Path:
    """
    Pass 2：分析报告生成
    输入：pass2_template.md 提示词模板 + Pass 1 素材
    输出：reports/{slug}_round1_{date}.md
    """
    template_file = PROMPTS_DIR / "pass2_template.md"
    if not template_file.exists():
        template_file = PROMPTS_DIR / "pass2_analysis.md"
    if not template_file.exists():
        raise FileNotFoundError(f"提示词文件不存在：{template_file}")
    if not materials_file.exists():
        raise FileNotFoundError(f"素材文件不存在：{materials_file}")

    slug = sector_to_slug(sector)
    output_file = REPORTS_DIR / f"{slug}_round1_{date_str}.md"

    prompt_template = render_template(template_file.read_text(encoding="utf-8"), sector)
    materials = materials_file.read_text(encoding="utf-8")

    # 拼接素材到 prompt
    prompt = f"""{prompt_template}

---

## 以下是 Pass 1 采集的原始素材

{materials}

---

请基于以上素材，按照上述五节框架撰写完整研报。素材中标注「[待验证]」或「[未找到]」的内容，在报告中同样标注，不要补充编造。如需补充验证，可使用 WebSearch 工具。
"""

    log.info("=" * 60)
    log.info(f"Pass 2：{sector} 行业主观研报")
    log.info(f"素材文件：{materials_file.name}（{len(materials)} 字符）")
    log.info("=" * 60)

    result = run_claude(prompt, PASS2_MODEL, PASS2_TOOLS, PASS2_TIMEOUT, "Pass2")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 加报告头
    header = f"""# {sector} 行业投研报告
**生成时间**：{date_str}
**素材来源**：{materials_file.name}
**分析模型**：{PASS2_MODEL}

---

"""
    full_report = header + result
    output_file.write_text(full_report, encoding="utf-8")

    log.info(f"Pass 2 输出已保存：{output_file}")
    log.info(f"报告字数：{len(full_report)} 字符")

    save_devlog({
        "timestamp": datetime.now().isoformat(),
        "project": "qqinvest",
        "type": "task",
        "context": f"Round 1 Pass 2 研报生成 [{sector}]",
        "action": f"完成{sector}行业主观研报，输出到 {output_file.name}",
        "result": f"报告 {len(full_report)} 字符",
        "insight": "",
    })

    return output_file


def main():
    parser = argparse.ArgumentParser(description="qqinvest Round 1 — 行业主观研报（参数化）")
    parser.add_argument("--sector", type=str, default=DEFAULT_SECTOR,
                        help=f"目标行业（默认：{DEFAULT_SECTOR}）")
    parser.add_argument("--pass", dest="only_pass", type=int, choices=[1, 2],
                        help="只运行指定 Pass（调试用）")
    parser.add_argument("--skip-pass1", action="store_true",
                        help="跳过 Pass 1，使用已有素材文件")
    parser.add_argument("--materials", type=str,
                        help="手动指定素材文件路径（配合 --skip-pass1 使用）")
    parser.add_argument("--date", type=str,
                        help="指定日期字符串（默认今天）")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    sector = args.sector

    log.info(f"qqinvest Round 1 启动，行业：{sector}，日期：{date_str}")

    try:
        # ── Pass 1 ────────────────────────────────────
        if args.only_pass == 2 or args.skip_pass1:
            # 跳过 Pass 1
            if args.materials:
                materials_file = Path(args.materials)
            else:
                # 自动找最新的素材文件（优先匹配当前 sector slug）
                slug = sector_to_slug(sector)
                existing = sorted(MATERIALS_DIR.glob(f"research_materials_{slug}_*.md"))
                if not existing:
                    existing = sorted(MATERIALS_DIR.glob("research_materials_*.md"))
                if not existing:
                    log.error("找不到素材文件，请先运行 Pass 1 或指定 --materials")
                    sys.exit(1)
                materials_file = existing[-1]
                log.info(f"使用已有素材文件：{materials_file}")
        elif args.only_pass == 1:
            materials_file = run_pass1(date_str, sector)
            log.info("Pass 1 完成，退出（--pass 1 模式）")
            return
        else:
            # 默认：跑两个 Pass
            materials_file = run_pass1(date_str, sector)

        # ── Pass 2 ────────────────────────────────────
        if args.only_pass == 1:
            return  # 已在上方处理

        report_file = run_pass2(date_str, materials_file, sector)

        # ── 完成 ──────────────────────────────────────
        log.info("=" * 60)
        log.info("Round 1 完成！")
        log.info(f"报告路径：{report_file}")
        log.info("")
        log.info("验收检查：")
        content = report_file.read_text(encoding="utf-8")
        char_count = len(content)
        has_table = "| 公司名" in content or "|公司名" in content
        log.info(f"  字数：{char_count}（目标 >= 8000 字符）{'✓' if char_count >= 8000 else '✗'}")
        log.info(f"  汇总表：{'✓' if has_table else '✗（未找到汇总表）'}")
        log.info(f"  行业：{sector}")
        log.info("=" * 60)

    except KeyboardInterrupt:
        log.info("用户中断")
        sys.exit(1)
    except Exception as e:
        log.error(f"执行失败：{e}")
        save_devlog({
            "timestamp": datetime.now().isoformat(),
            "project": "qqinvest",
            "type": "issue",
            "context": "Round 1 执行",
            "action": f"执行失败：{e}",
            "result": "失败",
            "insight": str(e),
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
