#!/usr/bin/env python3.13
"""
TradingAgents-CLI 模式
用 claude -p 子进程替代直接 API 调用，消耗订阅额度而非 API key

用法：
  python3.13 run_demo_cli.py 601608 2026-03-01
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# 代理绕过（eastmoney 直连）
no_proxy = [
    "eastmoney.com", "push2his.eastmoney.com", "push2.eastmoney.com",
    "xueqiu.com", "sina.com.cn", "baostock.com", "gtimg.cn",
]
existing = os.environ.get("NO_PROXY", "")
merged = set(existing.split(",")) | set(no_proxy) if existing else set(no_proxy)
os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(merged)

import baostock as bs
import akshare as ak
import pandas as pd

TICKER = sys.argv[1] if len(sys.argv) > 1 else "601608"
DATE   = sys.argv[2] if len(sys.argv) > 2 else "2026-03-01"

# ── 核心工具：claude -p 子进程 ─────────────────────────────────────────

def run_claude(prompt: str, model: str = "claude-sonnet-4-6",
               timeout: int = 300, label: str = "") -> str:
    if label:
        print(f"  ▶ {label}...", end="", flush=True)
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "text"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, env=env)
        out = result.stdout.strip() if result.returncode == 0 else f"[ERROR] {result.stderr[:300]}"
    except subprocess.TimeoutExpired:
        out = "[TIMEOUT]"
    if label:
        print(f" 完成（{len(out)} 字）")
    return out

# ── 数据获取（Python，不消耗 AI）──────────────────────────────────────

def fetch_market_data(ticker: str, end_date: str) -> str:
    prefix = "sh" if ticker.startswith(("6", "9")) else "sz"
    bs_code = f"{prefix}.{ticker}"
    start = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=100)).strftime("%Y-%m-%d")

    bs.login()
    rs = bs.query_history_k_data_plus(
        bs_code, "date,open,high,low,close,volume,pctChg,turn",
        start_date=start, end_date=end_date, frequency="d", adjustflag="3"
    )
    rows = []
    while rs.error_code == '0' and rs.next():
        rows.append(rs.get_row_data())
    bs.logout()

    if not rows:
        return "无法获取行情数据"

    df = pd.DataFrame(rows, columns=["日期","开盘","最高","最低","收盘","成交量","涨跌幅","换手率"])
    for col in ["开盘","最高","最低","收盘","成交量","涨跌幅","换手率"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna().reset_index(drop=True)

    # 技术指标
    df["MA5"]  = df["收盘"].rolling(5).mean()
    df["MA20"] = df["收盘"].rolling(20).mean()
    df["MA60"] = df["收盘"].rolling(60).mean()
    ema12 = df["收盘"].ewm(span=12, adjust=False).mean()
    ema26 = df["收盘"].ewm(span=26, adjust=False).mean()
    df["DIF"]  = ema12 - ema26
    df["DEA"]  = df["DIF"].ewm(span=9, adjust=False).mean()
    df["MACD"] = 2 * (df["DIF"] - df["DEA"])
    delta = df["收盘"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["RSI14"] = 100 - (100 / (1 + gain / loss.replace(0, 1e-9)))

    lat   = df.iloc[-1]
    r5    = df.tail(5)
    r20   = df.tail(20)[["日期","收盘","MA5","MA20","MACD","RSI14"]]

    return f"""## 行情数据（截至 {end_date}）

**最新收盘价**：{lat['收盘']:.2f} 元
**当日涨跌幅**：{lat['涨跌幅']:.2f}%
**换手率**：{lat['换手率']:.2f}%

**均线系统**：
- MA5  = {lat['MA5']:.2f}（价格{'高于' if lat['收盘']>lat['MA5'] else '低于'} MA5）
- MA20 = {lat['MA20']:.2f}（价格{'高于' if lat['收盘']>lat['MA20'] else '低于'} MA20）
- MA60 = {lat['MA60']:.2f}（价格{'高于' if lat['收盘']>lat['MA60'] else '低于'} MA60）

**MACD**：DIF={lat['DIF']:.3f}  DEA={lat['DEA']:.3f}  柱={lat['MACD']:.3f}（{'红柱多头' if lat['MACD']>0 else '绿柱空头'}）
**RSI14**：{lat['RSI14']:.1f}

**近5日明细**：
{r5[['日期','开盘','最高','最低','收盘','涨跌幅']].to_string(index=False)}

**近20日指标**：
{r20.to_string(index=False)}
"""


def fetch_news(ticker: str) -> str:
    try:
        df = ak.stock_news_em(symbol=ticker)
        if df is None or df.empty:
            return "暂无最新新闻"
        df = df.head(15)
        lines = []
        for _, row in df.iterrows():
            title = row.get("新闻标题", row.get("title", ""))
            time_ = str(row.get("发布时间", row.get("publish_time", "")))[:16]
            lines.append(f"- [{time_}] {title}")
        return "\n".join(lines) if lines else "无新闻数据"
    except Exception as e:
        return f"新闻获取失败：{e}"


def fetch_fundamentals(ticker: str) -> str:
    try:
        df = ak.stock_individual_info_em(symbol=ticker)
        if df is not None and not df.empty:
            lines = [f"- {row.iloc[0]}：{row.iloc[1]}" for _, row in df.iterrows()]
            return "## 公司基本信息\n" + "\n".join(lines)
    except Exception:
        pass
    return f"（akshare 基本面数据获取失败，ticker={ticker}）"


def get_company_name(ticker: str) -> str:
    try:
        prefix = "sh" if ticker.startswith(("6", "9")) else "sz"
        bs.login()
        rs = bs.query_stock_basic(code=f"{prefix}.{ticker}")
        while rs.error_code == '0' and rs.next():
            row = rs.get_row_data()
            bs.logout()
            return row[1]
        bs.logout()
    except Exception:
        pass
    return ticker

# ── Prompt 模板 ──────────────────────────────────────────────────────

MARKET_PROMPT = """你是一位专业的股票技术分析师。请基于以下行情数据，对股票 {ticker}（{company}）进行详细的技术分析报告。

{market_data}

请按以下结构输出中文分析报告：
1. 趋势判断（当前处于上升/下降/震荡趋势，关键依据）
2. 均线分析（各均线排列形态，多头/空头排列？）
3. MACD 分析（金叉/死叉/柱状图趋势）
4. RSI 分析（超买/超卖/中性区间）
5. 关键价位（支撑位3个 + 压力位3个，附依据）
6. 操作建议（进攻/防守/观望，附具体买卖条件和止损位）
7. 风险提示

请用专业、具体、数据驱动的语言撰写，避免泛泛而谈。"""

NEWS_PROMPT = """你是一位专业的财经新闻分析师。请基于以下新闻数据，分析股票 {ticker}（{company}）的舆情状况。

## 近期新闻
{news_data}

请按以下结构输出中文分析报告：
1. 新闻总体情感倾向（利多/利空/中性，比例评估）
2. 重要新闻解读（选3-5条最重要的，分析市场影响）
3. 市场情绪评估（投资者信心变化趋势）
4. 催化剂识别（近期可能的股价催化剂）
5. 风险事件预警
6. 结论：当前新闻面对股价的综合影响评级（正面/负面/中性）"""

FUNDAMENTALS_PROMPT = """你是一位专业的基本面分析师。请基于以下数据，分析股票 {ticker}（{company}）的基本面状况。

{fund_data}

结合你对该公司的公开信息认知（最近财报、业务进展），进行分析：
1. 核心业务与收入结构
2. 财务健康度（盈利能力、偿债能力）
3. 估值分析（当前 PE/PB 是否合理？行业对比）
4. 成长性（收入/利润增长趋势，未来催化剂）
5. 核心竞争力与护城河
6. 主要风险点
7. 基本面综合评级（强烈买入/买入/中性/卖出/强烈卖出）及逻辑"""

BULL_PROMPT = """你是一位专业的看多研究员，负责构建 {ticker}（{company}）的多头投资论点。

以下是三位分析师的报告：

## 技术面分析
{market_report}

## 新闻面分析
{news_report}

## 基本面分析
{fund_report}

请从多头角度出发，构建3个强力看涨论点，每个论点必须：
- 基于上述报告中的真实数据
- 逻辑严密，有数据支撑
- 直接反驳显而易见的空头观点

格式：
## 多头论点
**论点1：[标题]**
[详细论述，引用具体数据]

**论点2：[标题]**
[...]

**论点3：[标题]**
[...]

## 看多结论
[综合三个论点，给出明确的买入建议和目标价区间]"""

BEAR_PROMPT = """你是一位专业的看空研究员，负责构建 {ticker}（{company}）的空头投资论点。

以下是三位分析师的报告：

## 技术面分析
{market_report}

## 新闻面分析
{news_report}

## 基本面分析
{fund_report}

请从空头角度出发，构建3个强力看跌论点，每个论点必须：
- 基于上述报告中的真实数据
- 逻辑严密，有数据支撑
- 直接反驳显而易见的多头观点

格式：
## 空头论点
**论点1：[标题]**
[详细论述，引用具体数据]

**论点2：[标题]**
[...]

**论点3：[标题]**
[...]

## 看空结论
[综合三个论点，给出明确的卖出建议和风险提示]"""

JUDGE_PROMPT = """你是一位资深投资研究主任，负责裁定以下多空辩论并给出最终投资建议。

## 多头论点
{bull_arg}

## 空头论点
{bear_arg}

请进行客观中立的裁定：
1. 双方论点点评（各自的优势和弱点）
2. 关键分歧点识别（最核心的争议是什么）
3. 证据权重评估（哪方数据更有说服力）
4. 综合裁定（支持多方/空方/中性，并说明理由）
5. 最终交易建议：买入/卖出/持有
   - 目标价区间
   - 置信度（0-1）
   - 风险评分（0-1）
   - 进场条件和止损条件"""

RISK_PROMPT = """你是一位风险管理委员会主任，负责对以下交易建议进行风险审查。

## 研究主任裁定
{judge_decision}

## 多空辩论摘要
{debate_summary}

请从风险管理角度进行独立审查：
1. 系统性风险（宏观/行业风险）
2. 个股特定风险（流动性、估值、基本面风险）
3. 仓位建议（建议仓位比例及理由）
4. 止损机制（硬性止损线 + 分批减仓条件）
5. 风险调整后最终建议
   - 维持/修改原建议？
   - 加权目标价
   - 操作时间窗口"""

TRADER_PROMPT = """你是一位资深交易员，负责将所有分析转化为具体的操作方案。

## 技术面
{market_report}

## 新闻面
{news_report}

## 基本面
{fund_report}

## 多空辩论与裁定
{judge_decision}

## 风险评估
{risk_assessment}

请给出最终操作建议：
1. **最终信号**：买入/卖出/持有（必须明确选一）
2. **操作计划**
   - 建仓/加仓价格区间
   - 分批操作策略
   - 目标价（短期3个月 / 中期6个月）
   - 止损价（硬性 / 软性）
3. **仓位管理**：建议仓位占总仓位百分比
4. **催化剂监控**：需持续关注的关键事件
5. **退出条件**：什么情况下需要提前退出

最后附汇总表格（信号、目标价、止损价、置信度、风险评分）。"""

# ── 主流程 ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"TradingAgents-CLI | {TICKER} | {DATE}")
    print(f"模式：claude -p 订阅额度（不消耗 API key）")
    print(f"{'='*60}\n")

    # 1. 公司名
    print("📊 获取基础数据...")
    company = get_company_name(TICKER)
    print(f"  公司：{company}")

    # 2. 数据
    market_data = fetch_market_data(TICKER, DATE)
    print(f"  行情：{len(market_data)} 字符")
    news_data = fetch_news(TICKER)
    print(f"  新闻：{len(news_data)} 字符")
    fund_data = fetch_fundamentals(TICKER)
    print(f"  基本面：{len(fund_data)} 字符")

    print("\n🤖 启动多 Agent 分析...\n")

    # 3. 三位分析师（sonnet，快且省）
    market_report = run_claude(
        MARKET_PROMPT.format(ticker=TICKER, company=company, market_data=market_data),
        model="claude-sonnet-4-6", timeout=300, label="市场分析师")

    news_report = run_claude(
        NEWS_PROMPT.format(ticker=TICKER, company=company, news_data=news_data),
        model="claude-sonnet-4-6", timeout=300, label="新闻分析师")

    fund_report = run_claude(
        FUNDAMENTALS_PROMPT.format(ticker=TICKER, company=company, fund_data=fund_data),
        model="claude-sonnet-4-6", timeout=300, label="基本面分析师")

    # 4. 多空辩论（opus）
    bull_arg = run_claude(
        BULL_PROMPT.format(ticker=TICKER, company=company,
                           market_report=market_report, news_report=news_report, fund_report=fund_report),
        model="claude-opus-4-6", timeout=400, label="多方研究员")

    bear_arg = run_claude(
        BEAR_PROMPT.format(ticker=TICKER, company=company,
                           market_report=market_report, news_report=news_report, fund_report=fund_report),
        model="claude-opus-4-6", timeout=400, label="空方研究员")

    # 5. 研究主任裁定（opus）
    judge_decision = run_claude(
        JUDGE_PROMPT.format(bull_arg=bull_arg, bear_arg=bear_arg),
        model="claude-opus-4-6", timeout=400, label="研究主任")

    # 6. 风险评估（opus）
    risk_assessment = run_claude(
        RISK_PROMPT.format(
            judge_decision=judge_decision,
            debate_summary=f"多头摘要:\n{bull_arg[:600]}\n\n空头摘要:\n{bear_arg[:600]}"),
        model="claude-opus-4-6", timeout=400, label="风险经理")

    # 7. 最终交易员建议（opus）
    final_plan = run_claude(
        TRADER_PROMPT.format(
            market_report=market_report, news_report=news_report, fund_report=fund_report,
            judge_decision=judge_decision, risk_assessment=risk_assessment),
        model="claude-opus-4-6", timeout=400, label="交易员")

    # 8. 输出摘要
    print(f"\n{'='*60}")
    print("📊 最终操作建议")
    print(f"{'='*60}\n")
    print(final_plan[:2000])

    # 9. 保存完整报告
    out_dir = Path(__file__).parent / "results_cli" / TICKER / DATE
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "full_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# TradingAgents-CLI | {TICKER}（{company}）| {DATE}\n\n")
        f.write(f"**模式**：claude -p 订阅额度\n\n")
        for title, content in [
            ("市场技术分析", market_report),
            ("新闻舆情分析", news_report),
            ("基本面分析",   fund_report),
            ("多头论点",     bull_arg),
            ("空头论点",     bear_arg),
            ("研究主任裁定", judge_decision),
            ("风险评估",     risk_assessment),
            ("最终操作建议", final_plan),
        ]:
            f.write(f"\n## {title}\n\n{content}\n")

    print(f"\n报告已保存：{report_path}")
