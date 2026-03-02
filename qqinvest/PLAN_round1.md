# Plan: qqinvest Round 1 + Round 2 — 特种机器人投研报告（主观+量化）

## Context

- **Round 1**：行业级主观研报（5 节合作方方法论框架）→ 发合作方评估
- **Round 2**：个股量化信号分析（技术/资金/情绪评分）→ 同步给合作方看效果
- 两轮一起做，并行展示 AI 能力的完整覆盖范围

---

## 框架调研结论

**TradingAgents-CN**（开源，31k stars，https://github.com/hsliuping/TradingAgents-CN）：
- 四路 Agent（技术/基本面/新闻/情绪）+ Bull/Bear 辩论 + 风险经理
- 数据源：Tushare + AkShare（A 股完整覆盖）
- 适合生产环境 Round 2，但 Docker 部署耗时，今天 demo 先用自建脚本
- 合作方评分 >= 6 后，迁移到此框架

**AlphaPai（Alpha派）**：纯 SaaS，无公开 API，不纳入技术方案

**Round 2 Demo 方案**：`run_round2.py` + **akshare**（免费，无需 API key）+ Claude sonnet 分析

---

## 文件结构

```
qqinvest/
├── run_round1.py          # Round 1 主控：2-Pass 行业研报
├── run_round2.py          # Round 2 主控：个股量化信号
├── prompts/
│   ├── pass1_research.md  # 素材采集指令
│   ├── pass2_analysis.md  # 行业主观分析（5节方法论）
│   └── pass2_quant.md     # 量化分析指令（技术/资金/情绪）
├── 素材/                   # Pass 1 中间产出
│   └── research_materials.md
├── reports/               # 最终报告
│   ├── special_robots_round1_{date}.md
│   └── special_robots_round2_{date}.md
├── investment_ai_test_plan.md
├── PLAN_round1.md         # 本文件
└── CLAUDE.md
```

---

## Round 1：行业主观研报

**执行**：`python run_round1.py`（预计 30-60 分钟，含 opus 思考）

```
Pass 1: 素材深采（claude-sonnet-4-6, 600s）
├── 工具：WebSearch + WebFetch
├── 多路搜索：公司列表/业务占比/产业链玩家/政策文件/市场空间
└── 输出：素材/research_materials.md（每条标注来源+时间）

Pass 2: 行业研报（claude-opus-4-6, 1800s）
├── 工具：WebSearch（实时验证）
├── 注入：5节方法论框架 + Pass 1 素材
└── 输出：reports/special_robots_round1_{date}.md
```

**5节方法论**（来自 investment_ai_test_plan.md）：
1. 纯度划分：高/中/低 + 公司名+代码+分类理由+证据
2. 产业链推演：上游（减速器/传感器/关节）→ 中游（整机）→ 下游（场景/市场空间）
3. 成长空间：量产元年 / 政策催化 / 回报周期 / 百亿可能性
4. 市场信号：内部人增减持 / 机构持仓 / 异常资金 / 分析师评级
5. 综合研判：行业评级 + 3-5 家推荐标的 + 操作建议 + 汇总表

---

## Round 2：个股量化信号

**执行**：`python run_round2.py`（预计 15 分钟，3-5 只股票）

```
Step 1: akshare 数据采集（纯 Python，不调 Claude）
├── ak.stock_zh_a_hist() → 历史行情（日线）
├── pandas-ta → MA5/MA20/MACD/RSI/布林带
├── ak.stock_individual_fund_flow() → 近5日主力净流入
└── ak.stock_news_em() → 近7天新闻

Step 2: 量化分析报告（claude-sonnet-4-6, 300s/只）
├── 注入：数据 + 指标数值 + 资金流 + 新闻
└── 输出格式（每只股票一页）：
    - 三维评分表（技术面/情绪面/资金面各1-10分）
    - 看涨论点 × 3（数据支撑）
    - 看跌论点 × 3（数据支撑）
    - 综合评分 + 操作建议
```

**Demo 股票**：由脚本内 hardcode 3-5 只特种机器人高纯度标的（Round 1 结果出来后替换）

**依赖**：`pip install akshare pandas-ta`

---

## 后续（合作方评分 >= 6）

部署 TradingAgents-CN 替代自建 Round 2：
```bash
git clone https://github.com/hsliuping/TradingAgents-CN
docker-compose up -d
# 配置 Claude API key + Tushare API key
```

---

*计划更新：2026-03-01*
