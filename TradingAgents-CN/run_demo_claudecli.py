#!/usr/bin/env python3.13
"""
TradingAgents-CN Claude CLI 演示入口

使用 claude -p 订阅模式（无需 API Key）运行完整 TradingAgents-CN 流水线。
工具数据由 ClaudeCLILLM 内部预执行，Claude 收到数据后直接生成分析报告。

用法：
  python3.13 run_demo_claudecli.py 601608 2026-03-01
  python3.13 run_demo_claudecli.py AAPL 2026-03-01
"""
import os
import sys
from pathlib import Path

# ── 代理设置（绕过 eastmoney 等 A 股数据源） ──────────────────────────────
no_proxy_domains = [
    "eastmoney.com", "push2his.eastmoney.com", "push2.eastmoney.com",
    "xueqiu.com", "sina.com.cn", "baostock.com", "gtimg.cn",
    "akshare.com", "tushare.pro",
]
existing = os.environ.get("NO_PROXY", "")
merged = set(existing.split(",")) | set(no_proxy_domains) if existing else set(no_proxy_domains)
os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(merged)

# ── 加载 .env（如果存在） ────────────────────────────────────────────────
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# ── 参数解析 ─────────────────────────────────────────────────────────────
TICKER = sys.argv[1] if len(sys.argv) > 1 else "601608"
DATE   = sys.argv[2] if len(sys.argv) > 2 else "2026-03-01"

print(f"=== TradingAgents-CN (Claude CLI 模式) ===")
print(f"股票: {TICKER}  日期: {DATE}")
print()

# ── 配置 ─────────────────────────────────────────────────────────────────
from tradingagents.default_config import DEFAULT_CONFIG

config = {
    **DEFAULT_CONFIG,
    "llm_provider": "claude-cli",
    "deep_think_llm": "claude-opus-4-6",     # 研究员/裁定/风险/交易员
    "quick_think_llm": "claude-sonnet-4-6",  # 分析师
    "backend_url": "",                        # 不需要
    "online_tools": False,                    # 用本地 akshare/baostock 数据
    "online_news": False,
    "realtime_data": False,
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "memory_enabled": False,                  # 暂关闭向量内存，减少依赖
}

# ── 初始化 Graph ──────────────────────────────────────────────────────────
print("初始化 TradingAgentsGraph...")
from tradingagents.graph.trading_graph import TradingAgentsGraph

graph = TradingAgentsGraph(
    selected_analysts=["market", "news", "fundamentals"],
    config=config,
    debug=True,   # debug=True uses values-mode correctly (final_state = last chunk)
)
print("✅ Graph 初始化完成")
print()

# ── 运行 ─────────────────────────────────────────────────────────────────
print(f"开始分析 {TICKER} ({DATE})...")
print("（每个 claude -p 调用约需 30-120 秒，共约 5-8 次）")
print()

final_state, decision = graph.propagate(TICKER, DATE)

# ── 输出结果 ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("📊 分析完成")
print("=" * 60)

if final_state.get("market_report"):
    print("\n### 市场技术分析")
    print(final_state["market_report"][:500] + "..." if len(final_state.get("market_report", "")) > 500 else final_state["market_report"])

if final_state.get("news_report"):
    print("\n### 新闻情绪分析")
    print(final_state["news_report"][:500] + "..." if len(final_state.get("news_report", "")) > 500 else final_state["news_report"])

if final_state.get("fundamentals_report"):
    print("\n### 基本面分析")
    print(final_state["fundamentals_report"][:500] + "..." if len(final_state.get("fundamentals_report", "")) > 500 else final_state["fundamentals_report"])

print("\n" + "=" * 60)
print(f"📋 最终交易决策: {decision}")
print("=" * 60)

# ── 保存报告 ─────────────────────────────────────────────────────────────
from datetime import datetime
reports_dir = Path(__file__).parent / "reports"
reports_dir.mkdir(exist_ok=True)
report_path = reports_dir / f"claudecli_{TICKER}_{DATE}.md"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# TradingAgents 分析报告\n\n")
    f.write(f"- 股票：{TICKER}\n- 日期：{DATE}\n- 模式：claude-cli\n\n")

    for key, title in [
        ("market_report", "市场技术分析"),
        ("news_report", "新闻情绪分析"),
        ("fundamentals_report", "基本面分析"),
        ("investment_debate_state", "投资辩论"),
        ("risk_debate_state", "风险评估"),
    ]:
        val = final_state.get(key)
        if val:
            f.write(f"\n## {title}\n\n{val}\n")

    f.write(f"\n## 最终决策\n\n{decision}\n")

print(f"\n✅ 完整报告已保存：{report_path}")
