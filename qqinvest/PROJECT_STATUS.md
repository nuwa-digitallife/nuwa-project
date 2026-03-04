# qqinvest 项目进展

**最后更新**：2026-03-04
**项目定位**：测试大模型在主观投资分析（Round 1）+ 量化信号发现（Round 2）上的能力上限
**目标行业**：A股特种机器人（矿山/军工/安防/电力巡检）
**受众**：陆家嘴主观投资基金经理（合作方评估）

---

## 一、已完成

### Round 1 — 行业主观研报
- **方法论**：2-Pass 框架。Pass 1（Sonnet）网络采集原始素材；Pass 2（Opus）按五节框架撰写研报
- **五节结构**：纯度划分筛选 → 产业链上中下游推演 → 成长空间与时间节奏 → 内部人交易与市场信号 → 综合研判
- **参数化**：`run_round1.py` 支持 `--sector` 自定义行业，Pass 独立执行
- **已产出报告**：
  - `special_robots_round1_2026-03-01.md`（首版）
  - `特种机器人_矿山_军工_安防_电力巡检_round1_2026-03-02.md`（迭代版，17000字）
- **核心标的**：亿嘉和（603666）、中信重工（601608）、景业智能（688290）、云鼎科技（835277）、晶品特装（688684）

### Round 2 — 个股量化信号
- **方法论**：技术面 + 资金面 + 情绪面三维评分，akshare/baostock 本地数据
- **已产出报告**：`special_robots_round2_2026-03-01.md`（6只股票）

### TradingAgents-CN 改造（8-Agent 量化管道）
- **核心改动**：新增 `ClaudeCLILLM` 适配器，走 `claude -p` 订阅模式，**无需 API Key**
- **机制**：`bind_tools()` 预执行工具数据 → 注入 prompt → 返回 `tool_calls=[]` 触发 analyst 直接用 content 路径
- **关键文件**：
  - `tradingagents/llm_adapters/claude_cli_llm.py`（新建）
  - `tradingagents/graph/trading_graph.py`（加 claude-cli 分支）
  - `run_demo_claudecli.py`（演示入口）
- **实测结果**：601608 完整跑通，8 Agent 全部产出，耗时约 20 分钟
  - 决策：**卖出**，目标价 ¥7.10，置信度 0.62，风险评分 0.76
  - 核心逻辑：PE 160倍、ROE 3.1%，极度高估；矿山机器人业务占比仅 15-20%
- **报告**：`TradingAgents-CN/reports/claudecli_601608_2026-03-01.md`

### 深度个股分析（server.py 内置）
- 独立于 TradingAgents-CN，基于 run_demo_cli.py 的 7-Agent 管道
- 已跑：601608（2026-03-01）、603666（2026-03-03）

### 演示 UI（app.py）
- **框架**：Streamlit，3 Tab，无需登录
- **Tab 1 行业主观研究**：左侧研究员主观框架输入（催化剂/标的/非共识/顾虑/节奏），右侧展示研报 + 下载
- **Tab 2 个股量化分析**：8 Agent 报告展示，交易信号/目标价/置信度/风险评分解析
- **Tab 3 综合投研决策**：两层合并（主观行业研判 + 量化执行信号），方法论说明
- **启动**：`python3.13 -m streamlit run app.py --server.port 8502`
- **核心价值**：研究员写判断 → AI 用数据验证/挑战 → 量化 Agent 给执行信号

### 代码仓库
- qqinvest + TradingAgents-CN 合并进 `nuwa-digitallife/nuwa-project`
- 另一台机器：`git clone git@github.com:nuwa-digitallife/nuwa-project.git` → 按 `SETUP.md` 部署

---

## 二、待做

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P1 | 合作方演示 | 部署到另一台机器，用 app.py 给基金经理演示 |
| P2 | 更多行业覆盖 | 用 `--sector` 跑新能源储能、低空经济等行业研报 |
| P2 | Round 2 与 TradingAgents-CN 整合 | 现在 Round 2 独立，考虑接入 TradingAgents-CN 的 Agent 管道 |
| P3 | 主观框架注入验证 | 在 app.py 里真正跑一次带研究员判断的 Pass 2，看 AI 是否能有效验证/挑战 |
| P3 | 报告导出 PDF | 朋友/合作方更习惯看 PDF |

---

## 三、核心架构图

```
研究员主观判断
（催化剂/标的/非共识）
        ↓
   [Pass 1] Sonnet
   网络素材采集
        ↓
   [Pass 2] Opus
   五节研报框架
   逐条验证研究员判断
        ↓
   行业研报 + 推荐标的
        ↓
   [TradingAgents-CN]
   8 Agent 量化管道
   技术+新闻+基本面+多空辩论+风险+交易
        ↓
   交易信号（买入/卖出/持有）
   目标价 + 置信度 + 风险评分
```

---

## 四、关键经验

1. **akshare 必须用 Python 3.13**，3.14+ 不兼容
2. **claude -p 不能在 Claude Code 会话内直接调**，需要 `env.pop("CLAUDECODE", None)` 绕过嵌套检测
3. **LangGraph stream_mode="values"** 的每个 chunk 是全量 state，不是 delta，用 `debug=True` 走正确路径
4. **tool_calls=[]** 是让 analyst 节点走"直接用 content"路径的关键，不需要改任何 analyst 文件
5. **A 股数据在境外/代理环境下需设 NO_PROXY**，eastmoney/baostock 直连才能拿到数据
