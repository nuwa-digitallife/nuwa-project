#!/usr/bin/env python3.13
"""
TradingAgents-CN 非交互式 demo
直接调 TradingAgentsGraph API，绕过 TUI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv(Path(__file__).parent / ".env")

# 东方财富直连
no_proxy_domains = [
    "eastmoney.com","push2his.eastmoney.com","push2.eastmoney.com",
    "82.push2.eastmoney.com","xueqiu.com","sina.com.cn","baostock.com","gtimg.cn",
]
existing = os.environ.get("NO_PROXY","")
merged = set(existing.split(",")) | set(no_proxy_domains) if existing else set(no_proxy_domains)
os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(merged)

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# ── 配置 ─────────────────────────────────────────────
TICKER = sys.argv[1] if len(sys.argv) > 1 else "601608"
DATE   = sys.argv[2] if len(sys.argv) > 2 else "2026-03-01"

config = {
    **DEFAULT_CONFIG,
    "llm_provider": "anthropic",
    "deep_think_llm": "claude-opus-4-6",
    "quick_think_llm": "claude-sonnet-4-6",
    "backend_url": "https://api.anthropic.com",
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "online_tools": False,
    "results_dir": str(Path(__file__).parent / "results"),
}

ANALYSTS = ["market", "news", "fundamentals"]  # 去掉社交媒体（国内不可用）

print(f"\n{'='*60}")
print(f"TradingAgents-CN | 分析：{TICKER}  日期：{DATE}")
print(f"LLM: {config['deep_think_llm']} / {config['quick_think_llm']}")
print(f"分析师：{ANALYSTS}")
print(f"{'='*60}\n")

# ── 初始化 ────────────────────────────────────────────
graph = TradingAgentsGraph(ANALYSTS, config=config, debug=True)

# ── 运行（propagate 自己跑完全图，返回 final_state + decision）──
print("▶ 开始多 Agent 分析...\n")
final_state, decision = graph.propagate(TICKER, DATE)

# ── 输出 ──────────────────────────────────────────────
print(f"\n{'='*60}")
print("📊 分析报告")
print(f"{'='*60}\n")

def to_str(val):
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    return str(val) if val else ""

for key, label in [
    ("market_report",       "市场技术分析"),
    ("news_report",         "新闻分析"),
    ("fundamentals_report", "基本面分析"),
]:
    val = final_state.get(key)
    if val:
        s = to_str(val)
        print(f"\n## {label}\n")
        print(s[:2000] + ("..." if len(s) > 2000 else ""))

debate = final_state.get("investment_debate_state", {})
if debate.get("judge_decision"):
    s = to_str(debate["judge_decision"])
    print(f"\n## 多空辩论结论\n")
    print(s[:1500])

if final_state.get("trader_investment_plan"):
    s = to_str(final_state["trader_investment_plan"])
    print(f"\n## 交易员操作建议\n")
    print(s[:1500])

print(f"\n## 最终信号：{decision}")

# 保存完整报告
out_dir = Path(config["results_dir"]) / TICKER / DATE
out_dir.mkdir(parents=True, exist_ok=True)
report_path = out_dir / "full_report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# TradingAgents-CN | {TICKER} | {DATE}\n\n")
    for key, label in [
        ("market_report","市场技术分析"),("news_report","新闻分析"),
        ("fundamentals_report","基本面分析"),
    ]:
        val = final_state.get(key)
        if val:
            f.write(f"\n## {label}\n\n{to_str(val)}\n")
    if debate.get("judge_decision"):
        f.write(f"\n## 多空辩论\n\n{to_str(debate['judge_decision'])}\n")
    if final_state.get("trader_investment_plan"):
        f.write(f"\n## 操作建议\n\n{to_str(final_state['trader_investment_plan'])}\n")
    f.write(f"\n## 最终信号\n\n{decision}\n")

print(f"\n报告已保存：{report_path}")
