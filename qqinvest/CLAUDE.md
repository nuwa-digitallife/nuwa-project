# qqinvest

投资研究 AI 能力测试项目。测试大模型在主观投资分析（Round 1）+ 量化信号发现（Round 2）上的能力上限。

目标行业：**A股特种机器人**（矿山/军工/安防/电力巡检）
受众：陆家嘴主观投资基金经理（合作方评估）

## 文件结构

```
qqinvest/
├── run_round1.py          # Round 1 主控：2-Pass 行业研报
├── run_round2.py          # Round 2 主控：个股量化信号（akshare + Claude）
├── prompts/
│   ├── pass1_research.md  # 素材采集指令（WebSearch + WebFetch）
│   ├── pass2_analysis.md  # 行业主观分析指令（5节方法论）
│   └── pass2_quant.md     # 量化分析指令（技术/资金/情绪三维评分）
├── 素材/                   # Pass 1 中间产出 + Round 2 原始数据 JSON
├── reports/               # 最终报告
│   ├── special_robots_round1_{date}.md
│   └── special_robots_round2_{date}.md
├── investment_ai_test_plan.md  # 方法论来源（合作方实战框架）
└── PLAN_round1.md
```

## 使用方式

```bash
cd /Users/ciwang/Desktop/nuwa-project/qqinvest
# 依赖已安装到 python3.13（akshare 不支持 python3.14+）
# pip3.13 install akshare pandas-ta --break-system-packages

# Round 1（约30-60分钟，opus）
python3.13 run_round1.py
# → reports/special_robots_round1_{today}.md

# Round 2（约15分钟，sonnet，默认5只股票）
python3.13 run_round2.py
# → reports/special_robots_round2_{today}.md

# 常用选项
python3.13 run_round1.py --pass 1             # 只跑素材采集
python3.13 run_round1.py --skip-pass1         # 用已有素材直接跑分析
python3.13 run_round2.py --stocks 603666 000584  # 指定股票代码
python3.13 run_round2.py --skip-fetch         # 用已有 JSON 跳过数据采集
```

## 验收标准

- Round 1：5节完整 + 末尾汇总表 + >= 8000 字 + [待验证] 标注
- Round 2：每只股票一页 + 三维评分表 + 看涨/看跌各3条 + 操作建议

## Parent Project

Part of [Project Nuwa](../CLAUDE.md). Refer to parent CLAUDE.md for global conventions.
