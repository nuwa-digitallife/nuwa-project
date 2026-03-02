#!/usr/bin/env python3.13
"""
qqinvest Round 2 — 个股量化信号分析

流程：
  Step 1: 数据采集（akshare，不调用 Claude）
    - 历史行情（日线 OHLCV）
    - 技术指标（MA5/MA20/MACD/RSI/布林带，pandas-ta）
    - 资金流向（近5日主力净流入）
    - 新闻数据（近7天标题）

  Step 2: 量化分析报告（Claude sonnet，per-stock）
    - 技术面/情绪面/资金面三维评分
    - 看涨/看跌各3条论点
    - 综合评分 + 操作建议

使用：
  python run_round2.py                          # 默认股票池
  python run_round2.py --stocks 603666 688053   # 指定股票代码
  python run_round2.py --skip-fetch             # 跳过数据采集，用已有数据
  python run_round2.py --stock-only 603666      # 只分析单只股票
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── 路径配置 ─────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "素材"
REPORTS_DIR = ROOT / "reports"
DEVLOG = ROOT.parent / "logs" / "devlog.jsonl"

def infer_market(code: str) -> str:
    """根据股票代码推断市场（sh/sz/bj）。"""
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith(("0", "3")):
        return "sz"
    elif code.startswith(("4", "8")):
        return "bj"
    return "sh"  # 默认沪市

# ── 默认股票池（Round 1 推荐标的，2026-03-01 更新）─────
DEFAULT_STOCKS = [
    ("603666", "sh", "亿嘉和"),       # 高纯度，电力巡检机器人
    ("688290", "sh", "景业智能"),     # 高纯度，核电机器人
    ("601608", "sh", "中信重工"),     # 中纯度，消防机器人
    ("688084", "sh", "晶品特装"),     # 中纯度，军工特种装备
    ("000409", "sz", "云鼎科技"),     # 中纯度，矿山智能化
    ("002265", "sz", "建设工业"),     # 中纯度，军用机器狼
]

# ── 模型配置 ─────────────────────────────────────────
ANALYSIS_MODEL = "claude-sonnet-4-6"
ANALYSIS_TOOLS = "Read"
ANALYSIS_TIMEOUT = 300  # 5分钟/只

# ── Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("round2")


def bypass_proxy_for_akshare():
    """东方财富等 A 股数据源走国内直连，不需要走代理。"""
    import os
    no_proxy_domains = [
        "eastmoney.com", "push2his.eastmoney.com", "push2.eastmoney.com",
        "datacenter-web.eastmoney.com", "82.push2.eastmoney.com",
        "xueqiu.com", "sina.com.cn", "gtimg.cn",
    ]
    existing = os.environ.get("NO_PROXY", os.environ.get("no_proxy", ""))
    existing_set = set(existing.split(",")) if existing else set()
    merged = existing_set | set(no_proxy_domains)
    no_proxy_str = ",".join(merged)
    os.environ["NO_PROXY"] = no_proxy_str
    os.environ["no_proxy"] = no_proxy_str
    log.info(f"NO_PROXY 已设置，东方财富走直连")


def check_dependencies():
    """检查必要依赖是否安装。"""
    missing = []
    try:
        import akshare
    except ImportError:
        missing.append("akshare")
    try:
        import pandas_ta
    except ImportError:
        missing.append("pandas-ta")
    try:
        import pandas
    except ImportError:
        missing.append("pandas")

    if missing:
        log.error(f"缺少依赖：{', '.join(missing)}")
        log.error(f"请运行：pip install {' '.join(missing)}")
        sys.exit(1)


def fetch_stock_data(code: str, market: str, name: str) -> dict:
    """
    采集单只股票的全量数据。
    返回结构化 dict，保存为 data_{code}.json。
    """
    import akshare as ak
    import pandas as pd

    log.info(f"  采集 {name}（{code}）...")

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")

    data = {
        "code": code,
        "name": name,
        "market": market,
        "fetch_time": datetime.now().isoformat(),
        "hist": None,
        "indicators": None,
        "fund_flow": None,
        "news": None,
        "errors": [],
    }

    # ── 1. 历史行情（baostock 主力，不走东方财富代理）──────
    df = None
    try:
        import baostock as bs
        bs_market = "sh" if market == "sh" else "sz"
        bs_code = f"{bs_market}.{code}"
        bs_start = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
        bs_end = datetime.now().strftime("%Y-%m-%d")
        lg = bs.login()
        if lg.error_code == "0":
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,pctChg,turn",
                start_date=bs_start,
                end_date=bs_end,
                frequency="d",
                adjustflag="2",
            )
            rows = []
            while (rs.error_code == "0") and rs.next():
                rows.append(rs.get_row_data())
            bs.logout()
            if rows:
                df = pd.DataFrame(rows, columns=["date","open","high","low","close","volume","pct_change","turnover"])
                for col in ["open","high","low","close","volume","pct_change","turnover"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                log.info(f"    baostock行情：{len(df)}行")
        else:
            bs.logout()
            log.warning(f"    baostock login failed: {lg.error_msg}")
    except Exception as e:
        log.warning(f"    baostock 失败，尝试 akshare：{e}")

    # akshare 备用（如 baostock 失败）
    if df is None or df.empty:
        try:
            df_ak = ak.stock_zh_a_hist(
                symbol=code, period="daily",
                start_date=start_date, end_date=end_date, adjust="qfq",
            )
            if df_ak is not None and not df_ak.empty:
                col_map = {
                    "日期": "date", "开盘": "open", "收盘": "close",
                    "最高": "high", "最低": "low", "成交量": "volume",
                    "涨跌幅": "pct_change", "换手率": "turnover",
                }
                df = df_ak.rename(columns=col_map)
                df["date"] = df["date"].astype(str)
                log.info(f"    akshare行情（备用）：{len(df)}行")
        except Exception as e2:
            data["errors"].append(f"历史行情：baostock+akshare 均失败：{e2}")
            log.warning(f"    历史行情双源均失败：{e2}")

    try:
        if df is not None and not df.empty:

            # ── 2. 技术指标 ──────────────────────────────
            try:
                import pandas_ta as pta
                df["MA5"] = df["close"].rolling(5).mean().round(3)
                df["MA20"] = df["close"].rolling(20).mean().round(3)
                df["MA60"] = df["close"].rolling(60).mean().round(3)

                # MACD（默认12,26,9）
                macd = df.ta.macd(fast=12, slow=26, signal=9)
                if macd is not None:
                    df = pd.concat([df, macd], axis=1)

                # RSI
                rsi = df.ta.rsi(length=14)
                if rsi is not None:
                    df["RSI14"] = rsi.round(2)

                # 布林带
                bbands = df.ta.bbands(length=20, std=2)
                if bbands is not None:
                    df = pd.concat([df, bbands], axis=1)

                log.info(f"    技术指标计算完成")
            except Exception as e:
                log.warning(f"    技术指标计算失败：{e}")
                data["errors"].append(f"技术指标：{e}")

            # 只保留最近60行数据（避免 prompt 过长）
            recent = df.tail(60).copy()
            # NaN 转 None
            recent = recent.where(pd.notna(recent), None)
            data["hist"] = recent.to_dict(orient="records")

            # 单独保存关键指标摘要（供 prompt 引用）
            last = recent.iloc[-1]
            prev5 = recent.tail(5)["close"].tolist()
            prev20 = recent.tail(20)["close"].tolist()

            data["indicators"] = {
                "latest_close": float(last.get("close", 0)),
                "latest_date": str(last.get("date", "")),
                "MA5": float(last.get("MA5", 0)) if last.get("MA5") else None,
                "MA20": float(last.get("MA20", 0)) if last.get("MA20") else None,
                "MA60": float(last.get("MA60", 0)) if last.get("MA60") else None,
                "RSI14": float(last.get("RSI14", 0)) if last.get("RSI14") else None,
                "MACD": {
                    "macd": float(last.get("MACD_12_26_9", 0)) if last.get("MACD_12_26_9") else None,
                    "signal": float(last.get("MACDs_12_26_9", 0)) if last.get("MACDs_12_26_9") else None,
                    "hist": float(last.get("MACDh_12_26_9", 0)) if last.get("MACDh_12_26_9") else None,
                },
                "BB": {
                    "upper": float(last.get("BBU_20_2.0", 0)) if last.get("BBU_20_2.0") else None,
                    "mid": float(last.get("BBM_20_2.0", 0)) if last.get("BBM_20_2.0") else None,
                    "lower": float(last.get("BBL_20_2.0", 0)) if last.get("BBL_20_2.0") else None,
                },
                "volume_avg20": float(recent.tail(20)["volume"].mean()) if "volume" in recent else None,
                "latest_volume": float(last.get("volume", 0)) if last.get("volume") else None,
                "pct_5d": round((prev5[-1] / prev5[0] - 1) * 100, 2) if len(prev5) >= 2 else None,
                "pct_20d": round((prev20[-1] / prev20[0] - 1) * 100, 2) if len(prev20) >= 2 else None,
            }
            log.info(f"    行情数据：{len(recent)}条，最新收盘 {data['indicators']['latest_close']}")
        else:
            data["errors"].append("历史行情：返回空数据")
            log.warning(f"    历史行情返回空数据")
    except Exception as e:
        data["errors"].append(f"历史行情：{e}")
        log.warning(f"    历史行情采集失败：{e}")

    # ── 3. 资金流向 ────────────────────────────────────
    try:
        flow = ak.stock_individual_fund_flow(stock=code, market=market)
        if flow is not None and not flow.empty:
            # 取最近5天
            recent_flow = flow.tail(5)
            flow_col_map = {
                "日期": "date",
                "主力净流入-净额": "main_net",
                "主力净流入-净占比": "main_net_pct",
                "超大单净流入-净额": "huge_net",
                "大单净流入-净额": "big_net",
                "中单净流入-净额": "mid_net",
                "小单净流入-净额": "small_net",
            }
            recent_flow = recent_flow.rename(columns={k: v for k, v in flow_col_map.items() if k in recent_flow.columns})
            recent_flow["date"] = recent_flow["date"].astype(str) if "date" in recent_flow else recent_flow.index.astype(str)
            import pandas as pd
            recent_flow = recent_flow.where(pd.notna(recent_flow), None)
            data["fund_flow"] = recent_flow.to_dict(orient="records")
            log.info(f"    资金流向：{len(data['fund_flow'])}天")
        else:
            data["errors"].append("资金流向：返回空数据")
    except Exception as e:
        data["errors"].append(f"资金流向：{e}")
        log.warning(f"    资金流向采集失败：{e}")

    # ── 4. 新闻数据 ────────────────────────────────────
    try:
        news = ak.stock_news_em(symbol=code)
        if news is not None and not news.empty:
            # 取最近20条（7天内）
            news_col_map = {
                "新闻标题": "title",
                "新闻内容": "content",
                "发布时间": "publish_time",
                "文章来源": "source",
            }
            news = news.rename(columns={k: v for k, v in news_col_map.items() if k in news.columns})
            news["publish_time"] = news["publish_time"].astype(str) if "publish_time" in news else ""
            recent_news = news.head(20)
            import pandas as pd
            recent_news = recent_news.where(pd.notna(recent_news), None)
            # 只保留标题和时间（内容可能很长）
            news_list = []
            for _, row in recent_news.iterrows():
                news_list.append({
                    "title": row.get("title", ""),
                    "time": row.get("publish_time", ""),
                    "source": row.get("source", ""),
                })
            data["news"] = news_list
            log.info(f"    新闻：{len(news_list)}条")
        else:
            data["errors"].append("新闻：返回空数据")
    except Exception as e:
        data["errors"].append(f"新闻：{e}")
        log.warning(f"    新闻采集失败：{e}")

    return data


def build_quant_prompt(stock_data: dict) -> str:
    """将股票数据转换为量化分析 prompt。"""
    prompt_template = (PROMPTS_DIR / "pass2_quant.md").read_text(encoding="utf-8")

    code = stock_data["code"]
    name = stock_data["name"]
    ind = stock_data.get("indicators") or {}
    fund_flow = stock_data.get("fund_flow") or []
    news = stock_data.get("news") or []

    data_section = f"""
## 股票数据：{name}（{code}）

**采集时间**：{stock_data.get("fetch_time", "未知")}
**数据质量**：{f"错误：{'; '.join(stock_data['errors'])}" if stock_data.get("errors") else "正常"}

### 关键技术指标（最新）

| 指标 | 数值 |
|------|------|
| 最新收盘价 | {ind.get("latest_close", "N/A")} 元（{ind.get("latest_date", "")}） |
| MA5 | {ind.get("MA5", "N/A")} |
| MA20 | {ind.get("MA20", "N/A")} |
| MA60 | {ind.get("MA60", "N/A")} |
| RSI14 | {ind.get("RSI14", "N/A")} |
| MACD | {ind.get("MACD", {}).get("macd", "N/A")} |
| MACD信号线 | {ind.get("MACD", {}).get("signal", "N/A")} |
| MACD柱 | {ind.get("MACD", {}).get("hist", "N/A")} |
| 布林上轨 | {ind.get("BB", {}).get("upper", "N/A")} |
| 布林中轨 | {ind.get("BB", {}).get("mid", "N/A")} |
| 布林下轨 | {ind.get("BB", {}).get("lower", "N/A")} |
| 近5日涨跌 | {ind.get("pct_5d", "N/A")}% |
| 近20日涨跌 | {ind.get("pct_20d", "N/A")}% |
| 最新成交量 | {ind.get("latest_volume", "N/A")} |
| 20日均量 | {ind.get("volume_avg20", "N/A")} |

### 近5日资金流向（万元）

"""

    if fund_flow:
        data_section += "| 日期 | 主力净流入 | 超大单净流入 | 大单净流入 | 小单净流入 |\n"
        data_section += "|------|-----------|------------|-----------|----------|\n"
        for row in fund_flow:
            data_section += (
                f"| {row.get('date', '')} "
                f"| {row.get('main_net', 'N/A')} "
                f"| {row.get('huge_net', 'N/A')} "
                f"| {row.get('big_net', 'N/A')} "
                f"| {row.get('small_net', 'N/A')} |\n"
            )
    else:
        data_section += "（资金流向数据未采集到）\n"

    data_section += "\n### 近期新闻（最新20条标题）\n\n"
    if news:
        for i, item in enumerate(news[:20], 1):
            data_section += f"{i}. [{item.get('time', '')}] {item.get('title', '')}（{item.get('source', '')}）\n"
    else:
        data_section += "（新闻数据未采集到）\n"

    # 历史行情（最近20条，精简版）
    hist = stock_data.get("hist") or []
    if hist:
        data_section += "\n### 近20日行情（精简）\n\n"
        data_section += "| 日期 | 收盘 | 涨跌% | 成交量 | MA5 | MA20 |\n"
        data_section += "|------|------|-------|--------|-----|------|\n"
        for row in hist[-20:]:
            data_section += (
                f"| {row.get('date', '')} "
                f"| {row.get('close', '')} "
                f"| {row.get('pct_change', '')} "
                f"| {row.get('volume', '')} "
                f"| {row.get('MA5', '')} "
                f"| {row.get('MA20', '')} |\n"
            )

    full_prompt = f"{prompt_template}\n\n---\n\n{data_section}"
    return full_prompt


def run_claude_analysis(prompt: str, code: str, name: str) -> str:
    """调用 Claude 对单只股票进行量化分析。"""
    cmd = [
        "claude", "-p", prompt,
        "--model", ANALYSIS_MODEL,
        "--allowedTools", ANALYSIS_TOOLS,
        "--output-format", "text",
    ]
    log.info(f"  [分析] {name}（{code}）...")
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
        stdout, stderr = proc.communicate(timeout=ANALYSIS_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return f"## {name}（{code}）\n\n**错误**：分析超时（{ANALYSIS_TIMEOUT}s）\n"

    elapsed = time.time() - start
    log.info(f"  [分析] {name} 完成，耗时 {elapsed:.0f}s")

    if proc.returncode != 0:
        log.warning(f"  [分析] {name} 返回非零退出码 {proc.returncode}")
        return f"## {name}（{code}）\n\n**错误**：Claude 退出码 {proc.returncode}\n{stderr[:500]}\n"

    return stdout


def save_devlog(entry: dict):
    try:
        DEVLOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DEVLOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning(f"devlog 写入失败：{e}")


def main():
    parser = argparse.ArgumentParser(description="qqinvest Round 2 — 个股量化信号分析")
    parser.add_argument("--stocks", nargs="+", metavar="CODE",
                        help="指定股票代码列表（如：603666 688053）")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="跳过数据采集，使用已有 data_*.json 文件")
    parser.add_argument("--stock-only", metavar="CODE",
                        help="只分析单只股票")
    parser.add_argument("--date", type=str,
                        help="指定日期字符串（默认今天）")
    args = parser.parse_args()

    bypass_proxy_for_akshare()
    check_dependencies()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    log.info(f"qqinvest Round 2 启动，日期：{date_str}")

    # ── 确定股票池 ────────────────────────────────────
    if args.stock_only:
        # 只分析单只，从默认池找名称；找不到自动推断
        stock_pool = [
            (code, mkt, name) for code, mkt, name in DEFAULT_STOCKS
            if code == args.stock_only
        ]
        if not stock_pool:
            stock_pool = [(args.stock_only, infer_market(args.stock_only), args.stock_only)]
    elif args.stocks:
        # 自定义列表，从默认池匹配；找不到自动推断市场
        default_map = {code: (mkt, name) for code, mkt, name in DEFAULT_STOCKS}
        stock_pool = []
        for code in args.stocks:
            if code in default_map:
                mkt, name = default_map[code]
            else:
                mkt, name = infer_market(code), code
            stock_pool.append((code, mkt, name))
    else:
        stock_pool = DEFAULT_STOCKS

    log.info(f"股票池：{[(c, n) for c, _, n in stock_pool]}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    all_analyses = []

    for code, market, name in stock_pool:
        log.info(f"\n{'='*50}")
        log.info(f"处理：{name}（{code}）")
        log.info(f"{'='*50}")

        data_file = DATA_DIR / f"data_{code}_{date_str}.json"

        # ── Step 1: 数据采集 ──────────────────────────
        if args.skip_fetch and data_file.exists():
            log.info(f"  跳过采集，使用已有数据：{data_file}")
            with open(data_file, "r", encoding="utf-8") as f:
                stock_data = json.load(f)
        else:
            try:
                stock_data = fetch_stock_data(code, market, name)
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(stock_data, f, ensure_ascii=False, indent=2)
                log.info(f"  数据已保存：{data_file}")
            except Exception as e:
                log.error(f"  数据采集失败：{e}")
                all_analyses.append(f"## {name}（{code}）\n\n**错误**：数据采集失败：{e}\n")
                continue

        # ── Step 2: 量化分析 ──────────────────────────
        try:
            prompt = build_quant_prompt(stock_data)
            analysis = run_claude_analysis(prompt, code, name)
            all_analyses.append(analysis)
        except Exception as e:
            log.error(f"  分析失败：{e}")
            all_analyses.append(f"## {name}（{code}）\n\n**错误**：分析失败：{e}\n")

        # 避免 API rate limit
        time.sleep(2)

    # ── 汇总报告 ──────────────────────────────────────
    report_file = REPORTS_DIR / f"special_robots_round2_{date_str}.md"

    header = f"""# 特种机器人标的量化信号分析
**生成时间**：{date_str}
**分析股票**：{', '.join([f'{n}（{c}）' for c, _, n in stock_pool])}
**分析模型**：{ANALYSIS_MODEL}
**数据来源**：akshare（免费，无需API key）

---

"""

    footer = f"""

---

## 数据说明

- 行情数据：akshare A股日线（前复权）
- 技术指标：pandas-ta（MA5/MA20/MA60/MACD/RSI14/布林带）
- 资金流向：akshare 个股资金流向（近5日）
- 新闻数据：东方财富新闻（最新20条标题）
- **免责声明**：本报告仅为技术分析演示，不构成投资建议。
"""

    full_report = header + "\n\n---\n\n".join(all_analyses) + footer
    report_file.write_text(full_report, encoding="utf-8")

    log.info(f"\n{'='*60}")
    log.info(f"Round 2 完成！")
    log.info(f"报告路径：{report_file}")
    log.info(f"报告字数：{len(full_report)} 字符，覆盖 {len(all_analyses)} 只股票")
    log.info(f"{'='*60}")

    save_devlog({
        "timestamp": datetime.now().isoformat(),
        "project": "qqinvest",
        "type": "task",
        "context": f"Round 2 量化分析，{len(stock_pool)} 只股票",
        "action": f"完成量化信号报告，输出到 {report_file.name}",
        "result": f"报告 {len(full_report)} 字符",
        "insight": "",
    })


if __name__ == "__main__":
    main()
