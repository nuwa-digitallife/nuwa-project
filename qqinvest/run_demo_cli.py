#!/usr/bin/env python3.13
"""
TradingAgents-CLI 模式
用 claude -p 子进程替代直接 API 调用，消耗订阅额度而非 API key

用法（CLI）：
  python3.13 run_demo_cli.py 601608 2026-03-01

模块导入（供 server.py 调用）：
  from run_demo_cli import run_deep_analysis
  result = run_deep_analysis("601608", "2026-03-01", on_step=callback)
  # callback(step_name: str, status: str, preview: str = "")
"""
import json
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


def fetch_social_sentiment(ticker: str) -> str:
    """获取社交情绪数据：资金流向 + 人气热度 + 评论情感（akshare，不消耗 AI）"""
    parts = []

    # 1. 东财个股资金流向
    try:
        market = "sh" if ticker.startswith(("6", "9")) else "sz"
        df = ak.stock_individual_fund_flow(stock=ticker, market=market)
        if df is not None and not df.empty:
            # 取关键列
            cols = [c for c in df.columns if any(k in str(c) for k in ["日期", "主力", "净额", "净占比", "净流入"])]
            display = df[cols].tail(5) if cols else df.tail(5)
            parts.append("## 个股资金流向（近5日）\n" + display.to_string(index=False))
        else:
            parts.append("## 个股资金流向\n暂无数据")
    except Exception as e:
        parts.append(f"## 个股资金流向\n获取失败：{e}")

    # 2. 东财人气热度排名
    try:
        hot_df = ak.stock_hot_rank_em()
        if hot_df is not None and not hot_df.empty:
            # 找代码列（可能叫"代码"/"股票代码"等）
            code_col = next((c for c in hot_df.columns if "代码" in str(c)), hot_df.columns[0])
            row = hot_df[hot_df[code_col].astype(str).str.contains(ticker, na=False)]
            if not row.empty:
                parts.append("## 人气热度排名\n" + row.to_string(index=False))
            else:
                parts.append("## 人气热度排名\n（该股票未进入今日人气榜前100）")
        else:
            parts.append("## 人气热度排名\n暂无数据")
    except Exception as e:
        parts.append(f"## 人气热度排名\n获取失败：{e}")

    # 3. 东财投资者评论情感
    try:
        comment_df = ak.stock_comment_em(symbol=ticker)
        if comment_df is not None and not comment_df.empty:
            parts.append("## 投资者评论情感\n" + comment_df.head(10).to_string(index=False))
        else:
            parts.append("## 投资者评论情感\n暂无数据")
    except Exception as e:
        parts.append(f"## 投资者评论情感\n获取失败：{e}")

    return "\n\n".join(parts) if parts else "社交情绪数据暂时无法获取"


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

SOCIAL_PROMPT = """你是一位专业的社交情绪分析师。请基于以下社交数据，分析股票 {ticker}（{company}）的市场情绪状况。

{social_data}

请按以下结构输出中文分析报告：
1. 资金流向分析（主力净流入/流出趋势，量级评估，与股价走势是否吻合）
2. 投资者情绪倾向（热度排名、看多/看空情绪比例）
3. 散户行为特征（追涨杀跌、抄底信号、持仓意愿变化）
4. 情绪催化剂（近期驱动情绪变化的关键因素）
5. 情绪风险预警（过热/过冷信号，与基本面的背离情况）
6. 社交情绪综合评级（积极/中性/消极）及核心理由"""

BULL_PROMPT = """你是一位专业的看多研究员，负责构建 {ticker}（{company}）的多头投资论点。

以下是四位分析师的报告：

## 技术面分析
{market_report}

## 新闻面分析
{news_report}

## 基本面分析
{fund_report}

## 社交情绪分析
{social_report}

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

以下是四位分析师的报告：

## 技术面分析
{market_report}

## 新闻面分析
{news_report}

## 基本面分析
{fund_report}

## 社交情绪分析
{social_report}

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

## 社交情绪面
{social_report}

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

EXTRACT_PROMPT = """从以下交易员操作方案中提取结构化数据，只输出纯 JSON（不要有任何其他文字、代码块标记）：

{trader_report}

输出格式（每个字段都必须有，找不到用 null 或空字符串）：
{{
  "signal": "买入或持有或卖出",
  "confidence": 置信度数字0.0到1.0,
  "target_high": 目标价上限数字,
  "target_low": 目标价下限数字,
  "stop_loss": 止损价数字,
  "risk_score": 风险评分数字0.0到1.0,
  "one_line": "一句话操作建议（30字以内）"
}}"""

# ── 主函数（可调用模块）──────────────────────────────────────────────

def run_deep_analysis(ticker: str, date: str, on_step=None) -> dict:
    """
    执行 8-Agent（含社交情绪）深度个股分析。

    Args:
        ticker: 6位股票代码（如 "601608"）
        date:   分析日期 YYYY-MM-DD
        on_step: 可选回调 on_step(step_name, status, preview)
                 status: "started" | "completed"

    Returns:
        {
            "ticker": str,
            "company": str,
            "date": str,
            "full_report": str,   # 完整 Markdown
            "summary": dict,      # 结构化摘要（解析失败时为 {}）
            "steps": list[dict],  # 每步记录
        }
    """
    steps_log = []

    def step(name: str, status: str, preview: str = ""):
        if on_step:
            on_step(name, status, preview)
        if status == "completed":
            steps_log.append({"step": name, "preview": preview[:100]})

    print(f"\n{'='*60}")
    print(f"TradingAgents-CLI | {ticker} | {date}")
    print(f"模式：claude -p 订阅额度（不消耗 API key）")
    print(f"{'='*60}\n")

    # ── 1. 数据获取 ────────────────────────────────────────────────────
    step("获取数据", "started")
    print("📊 获取基础数据...")
    company = get_company_name(ticker)
    print(f"  公司：{company}")

    market_data = fetch_market_data(ticker, date)
    print(f"  行情：{len(market_data)} 字符")
    news_data = fetch_news(ticker)
    print(f"  新闻：{len(news_data)} 字符")
    fund_data = fetch_fundamentals(ticker)
    print(f"  基本面：{len(fund_data)} 字符")
    social_data = fetch_social_sentiment(ticker)
    print(f"  社交情绪：{len(social_data)} 字符")
    step("获取数据", "completed", f"行情{len(market_data)}+新闻{len(news_data)}+社交{len(social_data)}字符")

    print("\n🤖 启动多 Agent 分析...\n")

    # ── 2. 市场分析师（Sonnet）────────────────────────────────────────
    step("市场分析师", "started")
    market_report = run_claude(
        MARKET_PROMPT.format(ticker=ticker, company=company, market_data=market_data),
        model="claude-sonnet-4-6", timeout=300, label="市场分析师")
    step("市场分析师", "completed", market_report[:80])

    # ── 3. 新闻分析师（Sonnet）────────────────────────────────────────
    step("新闻分析师", "started")
    news_report = run_claude(
        NEWS_PROMPT.format(ticker=ticker, company=company, news_data=news_data),
        model="claude-sonnet-4-6", timeout=300, label="新闻分析师")
    step("新闻分析师", "completed", news_report[:80])

    # ── 4. 基本面分析师（Sonnet）──────────────────────────────────────
    step("基本面分析师", "started")
    fund_report = run_claude(
        FUNDAMENTALS_PROMPT.format(ticker=ticker, company=company, fund_data=fund_data),
        model="claude-sonnet-4-6", timeout=300, label="基本面分析师")
    step("基本面分析师", "completed", fund_report[:80])

    # ── 5. 社交情绪分析师（Sonnet）— NEW ──────────────────────────────
    step("社交情绪分析师", "started")
    social_report = run_claude(
        SOCIAL_PROMPT.format(ticker=ticker, company=company, social_data=social_data),
        model="claude-sonnet-4-6", timeout=300, label="社交情绪分析师")
    step("社交情绪分析师", "completed", social_report[:80])

    # ── 6. 多方研究员（Opus）──────────────────────────────────────────
    step("多方研究员", "started")
    bull_arg = run_claude(
        BULL_PROMPT.format(
            ticker=ticker, company=company,
            market_report=market_report, news_report=news_report,
            fund_report=fund_report, social_report=social_report),
        model="claude-opus-4-6", timeout=400, label="多方研究员")
    step("多方研究员", "completed", bull_arg[:80])

    # ── 7. 空方研究员（Opus）──────────────────────────────────────────
    step("空方研究员", "started")
    bear_arg = run_claude(
        BEAR_PROMPT.format(
            ticker=ticker, company=company,
            market_report=market_report, news_report=news_report,
            fund_report=fund_report, social_report=social_report),
        model="claude-opus-4-6", timeout=400, label="空方研究员")
    step("空方研究员", "completed", bear_arg[:80])

    # ── 8. 研究主任裁定（Opus）────────────────────────────────────────
    step("研究主任裁定", "started")
    judge_decision = run_claude(
        JUDGE_PROMPT.format(bull_arg=bull_arg, bear_arg=bear_arg),
        model="claude-opus-4-6", timeout=400, label="研究主任")
    step("研究主任裁定", "completed", judge_decision[:80])

    # ── 9. 风险评估（Opus）────────────────────────────────────────────
    step("风险评估", "started")
    risk_assessment = run_claude(
        RISK_PROMPT.format(
            judge_decision=judge_decision,
            debate_summary=f"多头摘要:\n{bull_arg[:600]}\n\n空头摘要:\n{bear_arg[:600]}"),
        model="claude-opus-4-6", timeout=400, label="风险经理")
    step("风险评估", "completed", risk_assessment[:80])

    # ── 10. 最终操作建议（Opus）───────────────────────────────────────
    step("最终操作建议", "started")
    final_plan = run_claude(
        TRADER_PROMPT.format(
            market_report=market_report, news_report=news_report,
            fund_report=fund_report, social_report=social_report,
            judge_decision=judge_decision, risk_assessment=risk_assessment),
        model="claude-opus-4-6", timeout=400, label="交易员")
    step("最终操作建议", "completed", final_plan[:80])

    # ── 11. 结构化摘要提取（Sonnet）— NEW ────────────────────────────
    step("提取结构化摘要", "started")
    summary_raw = run_claude(
        EXTRACT_PROMPT.format(trader_report=final_plan),
        model="claude-sonnet-4-6", timeout=120, label="摘要提取")
    summary = {}
    try:
        clean = summary_raw.strip()
        # 去掉可能的 ```json ... ``` 包装
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        summary = json.loads(clean.strip())
    except Exception:
        pass
    step("提取结构化摘要", "completed", json.dumps(summary, ensure_ascii=False)[:100])

    # ── 组装完整报告 ───────────────────────────────────────────────────
    full_report = f"# TradingAgents-CLI | {ticker}（{company}）| {date}\n\n**模式**：claude -p 订阅额度\n\n"
    for title, content in [
        ("市场技术分析", market_report),
        ("新闻舆情分析", news_report),
        ("基本面分析",   fund_report),
        ("社交情绪分析", social_report),
        ("多头论点",     bull_arg),
        ("空头论点",     bear_arg),
        ("研究主任裁定", judge_decision),
        ("风险评估",     risk_assessment),
        ("最终操作建议", final_plan),
    ]:
        full_report += f"\n## {title}\n\n{content}\n"

    # ── 保存到本地文件 ─────────────────────────────────────────────────
    out_dir = Path(__file__).parent / "results_cli" / ticker / date
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "full_report.md").write_text(full_report, encoding="utf-8")

    return {
        "ticker": ticker,
        "company": company,
        "date": date,
        "full_report": full_report,
        "summary": summary,
        "steps": steps_log,
    }

# ── CLI 入口 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    TICKER = sys.argv[1] if len(sys.argv) > 1 else "601608"
    DATE   = sys.argv[2] if len(sys.argv) > 2 else "2026-03-01"

    result = run_deep_analysis(TICKER, DATE)

    print(f"\n{'='*60}")
    print("📊 最终操作建议")
    print(f"{'='*60}\n")
    if "## 最终操作建议" in result["full_report"]:
        print(result["full_report"].split("## 最终操作建议")[-1][:2000])
    else:
        print(result["full_report"][:2000])

    if result["summary"]:
        print("\n📋 结构化摘要：")
        for k, v in result["summary"].items():
            print(f"  {k}: {v}")

    print(f"\n✅ 报告已保存：{Path(__file__).parent / 'results_cli' / TICKER / DATE / 'full_report.md'}")
