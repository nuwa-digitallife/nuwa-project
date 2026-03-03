# 素材报告：OpenClaw算力涟漪
采集时间：2026-03-03

---

## 核心事实（已验证）

### 1. OpenClaw 是什么：两个不同的东西，但都指向同一个趋势

**重要概念澄清**：在中文媒体的语境中，"OpenClaw"被用来指代 Anthropic 的 Claude Code，但这实际上是两个不同的产品，需要区分：

- **Claude Code**：Anthropic 官方的 AI 编程 CLI 工具，2025年2月作为研究预览版发布，是本文算力涟漪的核心主角。
- **OpenClaw**（原名 Clawdbot/Moltbot）：由独立开发者 Peter Steinberger 制作的开源个人 AI 助手，连接 WhatsApp/Telegram/Slack 等通讯平台，2026年1月病毒式传播，72小时内获得6万 GitHub stars，最终超过14.5万 stars。2026年2月15日，Steinberger 宣布加入 OpenAI，OpenClaw 转移至开源基金会由 OpenAI 支持。

**文章角度建议**：以 Claude Code 为主线，OpenClaw 事件作为侧写——两者都说明了 Agentic AI 的强大吸引力，也共同造成了 Anthropic 的一场 OAuth 危机（从中可以观察到算力需求的爆炸性）。

来源：[The New Stack](https://thenewstack.io/anthropic-agent-sdk-confusion/)、[TechCrunch](https://techcrunch.com/2026/02/15/openclaw-creator-peter-steinberger-joins-openai/)

---

### 2. Claude Code 核心数据（Anthropic 官方宣布，2026年2月13日）

- **收入**：Claude Code 年化收入已超过 **25亿美元（$2.5B ARR）**，自2026年1月1日以来翻倍
- **用户**：每周活跃用户数自2026年1月1日以来翻倍
- **GitHub 渗透率**：当前 **4% 的全球公开 GitHub commits 由 Claude Code 生成**，一个月前还是2%
- **预测**：SemiAnalysis 预测2026年底 Claude Code 将占所有日常 commits 的 20%+
- **企业收入占比**：企业用户贡献 Claude Code 收入的一半以上
- **订阅增长**：企业订阅数自2026年初以来增加4倍

来源：[Anthropic 官方 Series G 公告](https://www.anthropic.com/news/anthropic-raises-30-billion-series-g-funding-380-billion-post-money-valuation)、[SemiAnalysis "Claude Code is the Inflection Point"](https://newsletter.semianalysis.com/p/claude-code-is-the-inflection-point)、[officechai 报道](https://officechai.com/ai/4-of-github-commits-are-now-made-by-claude-code-semianalysis-report/)

---

### 3. Anthropic 整体财务与融资

- 年化收入从2025年底约 $90亿 升至2026年2月 **$140亿（$14B ARR）**
- 2025年全年收入约 $100亿
- 2026年2月12日完成 **300亿美元 G 轮融资**，投后估值 **3800亿美元**
- 每年收入超 $10万的客户数量同比增长7倍，超过500家企业客户每年消费超 $100万

来源：[CNBC](https://www.cnbc.com/2026/02/12/anthropic-closes-30-billion-funding-round-at-380-billion-valuation.html)、[SiliconAngle](https://siliconangle.com/2026/02/12/anthropic-closes-30b-round-annualized-revenue-tops-14b/)

---

### 4. Agentic AI 的算力倍增效应（涟漪的起点）

- **IDC 预测（2026年1月发布）**：到2027年，G2000企业的 AI Agent 使用量将增加**10倍**，但 Token 和 API 调用量将增加**1000倍**
- **IDC 预测（2029年）**：全球活跃 AI Agent 超过**10亿个**（是2025年的40倍），每日执行**2170亿次操作**，每日消耗**3.7万亿 Token**
- **Gartner 预测**：2026年底，40% 的企业应用将嵌入 AI Agent（2025年9月时仅5%）
- **Token 消耗倍数**：Agent 团队模式比普通会话多使用约**7倍** Token，因为每个子 Agent 维护独立的 context window 并行运行
- **扩展思维的代价**：测试时扩展（long thinking）需要的算力是普通推理的**100倍以上**；训练后扩展需要约**30倍**基础训练算力

来源：[IDC FutureScape 2026](https://www.idc.com/resource-center/blog/agent-adoption-the-it-industrys-next-great-inflection-point/)、[Motley Fool](https://www.fool.com/investing/2026/02/26/artificial-intelligence-ai-agents-are-crashing-the/)、[Deloitte 2026 TMT Predictions](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html)

---

### 5. 推理 vs 训练：算力格局的历史性转变

- **2023年**：推理占全部 AI 算力的约 **1/3**
- **2025年**：推理占约 **1/2**（Deloitte 数据）
- **2026年**：推理将占约 **2/3**（Deloitte 预测）
- **2030年**：推理将占约 **3/4**（Brookfield 预测）
- 推理优化芯片市场规模：2025年已超 **$200亿**（来自 Meta、Google、Amazon、Intel、AMD、Qualcomm 等），2026年将达 **$500亿以上**
- AI 算力需求增速是摩尔定律的**2倍**

来源：[Deloitte 2026 Compute Report](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html)

---

### 6. NVIDIA 的地位与挑战

- NVIDIA FY2026（2025年2月至2026年1月）数据中心算力收入预计 **$1547亿**
- Q3 FY2026（2025年10月结束）季度营收创纪录 **$570亿**
- Blackwell 芯片（B200/GB200）积压订单 **360万台**，已售罄至2026年中期
- 分析师预测：NVIDIA 推理市场份额将从当前 90%+ 下降至2028年的 **20-30%**，定制 ASIC 和专用芯片将占据 70-75% 的生产推理工作量
- NVIDIA 战略响应：斥资 **$200亿** 押注 Groq（推理加速芯片），布局 Vera Rubin 架构（承诺比 Blackwell 成本低10倍）

来源：[NVIDIA 官方财报](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2026)、[VentureBeat](https://venturebeat.com/infrastructure/inference-is-splitting-in-two-nvidias-usd20b-groq-bet-explains-its-next-act)

---

### 7. 定制 ASIC 的反攻（被低估的机会）

- **Broadcom（AVGO）**：FY2025 Q4 AI 半导体收入约 **$65亿**（同比+74%），预计 FY2026 Q1 翻倍至 **$82亿**
- 为 Google（TPU）、Meta（MTIA）设计专用推理芯片，占定制 ASIC 市场份额 **90%**
- Google TPU：预计占 Broadcom ASIC 出货量的 58%，但占 ASIC 收入的 **78%（约$221亿）**
- **OpenAI 与 Broadcom 合作**：代号 "Titan" 的定制 ASIC，Citi 估计合同规模 $1000亿，Mizuho 估计可能高达 **$1500-2000亿**（多年）
- **Apple** 已转向使用 Google TPU（2048块 TPUv5p）训练其 AI 模型，而非 NVIDIA GPU

来源：[CNBC Broadcom earnings](https://www.cnbc.com/2025/12/11/broadcom-avgo-q4-earnings-2025.html)、[Google TPU analysis](https://newsletter.semianalysis.com/p/tpuv7-google-takes-a-swing-at-the)

---

### 8. 数据中心能源：涟漪到电网层面

- 2026年全球 AI 数据中心资本支出预计 **$4000-4500亿**（其中芯片 $2500-3000亿）
- 2028年预计突破 **$1万亿/年**
- 2026年数据中心用电量将突破 **1000 TWh**（相当于日本全国用电量，相当于全球核电站年发电量的1/3以上）
- 高盛预测：到2030年，数据中心用电量将增长 **160%**
- **液冷市场爆发**：从2025年的 $28亿 增长至2032年的 **$210亿以上**（CAGR 30%+）
- Blackwell 芯片机柜功率密度超过 **100kW/机柜**，已超出传统风冷极限（风冷上限约41kW）
- **核能/SMR**：微软、谷歌、亚马逊、Meta 已签署超 **20GW SMR** 采购协议；中国"玲龙一号" SMR 预计2026年上半年商业运营（全球首个商业化陆上 SMR）

来源：[IEA Energy and AI Report](https://www.iea.org/reports/energy-and-ai/energy-supply-for-ai)、[Goldman Sachs](https://www.goldmansachs.com/insights/articles/is-nuclear-energy-the-answer-to-ai-data-centers-power-consumption)、[Deloitte 2026](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html)

---

### 9. 边缘推理：下一个战场

- 边缘 AI 芯片初创公司2025年上半年已吸引超 **$51亿** 风投
- 定制 ASIC 边缘推理收入2025年预计接近 **$78亿**
- 2026年 XPU（ASIC/定制加速器）增速预计 **22%**，超过 GPU（19%）和 CPU（14%）
- 全球边缘 AI 芯片市场2036年将超过 **$800亿**（最大应用：汽车+AI 智能手机）
- 核心驱动：云端推理成本不可持续，AI 功能线性扩张但成本可能指数级增长

来源：[SDxCentral](https://www.sdxcentral.com/analysis/ai-inferencing-will-define-2026-and-the-markets-wide-open/)、[IDTechEx](https://www.idtechex.com/en/research-report/ai-chips-for-edge-applications/1148)

---

### 10. 中国算力产业链数据

- 2024年中国 AI 算力市场规模 $190亿，2025年达 $259亿（同比+36.2%），预计2028年达 $552亿
- 中国 AI 服务器市场2025年突破 $561亿，占全球市场份额42%
- 中国移动2025年下半年斥资 **51.12亿元** 集采7058台推理型 AI 服务器（年度最大单笔订单）
- 液冷渗透率：2024年14% → 2025年33% → 2026年预计47%，液冷服务器占比将达60-70%
- 推理算力专项建设：中电信杭州推理算力池、中联通武汉千卡推理中心正在建设中

来源：[OFweek](https://m.ofweek.com/ai/2026-01/ART-201700-8420-30678592.html)、[证券时报](https://www.stcn.com/article/detail/3648600.html)

---

## 关键人物/公司

| 人物/公司 | 关键数据点 |
|-----------|-----------|
| **Dario Amodei（Anthropic CEO）** | 带领 Anthropic 完成 $300亿 G 轮，Claude Code ARR $25亿 |
| **Dylan Patel（SemiAnalysis）** | 发布 "Claude Code is the Inflection Point" 报告，预测2026年底 Claude Code 占 20% GitHub commits |
| **Peter Steinberger（OpenClaw 创始人）** | 独立开发 OpenClaw，72小时6万星，2026年2月15日宣布加入 OpenAI |
| **Sam Altman（OpenAI CEO）** | 招募 Steinberger："他对未来智能体的想法非常惊艳" |
| **Jensen Huang（NVIDIA CEO）** | 宣告 Agent 拐点，将 Blackwell 定位为推理时代核心基础设施，$200亿押注 Groq |
| **NVIDIA** | FY2026 数据中心收入 $1547亿，Blackwell 积压360万台，推理芯片新战线 |
| **Broadcom（AVGO）** | 定制 ASIC 市场份额90%，Google TPU + OpenAI Titan 合同，AI 收入预计2026翻倍 |
| **Google** | TPU 芯片对抗 NVIDIA，占 Broadcom ASIC 收入78%；同时是 Anthropic 的云供应商 |
| **Accenture** | 已部署30,000名员工使用 Claude Code（最大企业级部署） |
| **MARA Holdings** | 比特币矿机转型 AI 推理数据中心，2026年2月与 Starwood 合作建设1GW AI 推理设施 |

---

## 时间线

| 时间 | 事件 |
|------|------|
| 2025年2月 | Claude Code 作为研究预览版发布 |
| 2025年5月 | Claude Code 正式发布（SaaS 产品化） |
| 2025年9月 | Claude Code 年化收入超 $5亿，企业用户数加速增长 |
| 2025年10月26日 | NVIDIA Q3 FY2026 季度营收创纪录 $570亿 |
| 2025年11月 | Deloitte 发布 2026 TMT Predictions：推理将占2026年AI算力2/3 |
| 2025年11月底 | Broadcom AI 芯片销售翻倍报道，AVGO 股价上涨 |
| 2025年12月 | Broadcom 宣布 AI 半导体收入当季翻倍（约$65亿）；NVIDIA Blackwell 积压360万台 |
| 2026年1月初 | OpenClaw 病毒式传播，72小时6万 GitHub stars |
| 2026年1月9日 | Anthropic 部署服务端拦截，阻止第三方工具通过订阅 OAuth token 使用 Claude |
| 2026年1月12日 | Anthropic 发布 Cowork（Claude Code 通用计算版），4名工程师10天完成，代码由 Claude Code 本身写成 |
| 2026年2月5日 | Claude Opus 4.6 正式发布，增强 Agent 长任务能力 |
| 2026年2月12日 | Anthropic 宣布完成 $300亿 G 轮融资，估值 $3800亿 |
| 2026年2月13日 | Anthropic 公布 Claude Code ARR $25亿，GitHub 4% commits 数据 |
| 2026年2月15日 | Peter Steinberger 宣布加入 OpenAI，OpenClaw 转移至开源基金会 |
| 2026年2月17日 | Claude Sonnet 4.6 发布，针对 Agent 和长上下文推理优化 |
| 2026年2月19-20日 | Anthropic 更新服务条款，正式书面禁止第三方工具使用消费级订阅 OAuth |
| 2026年2月26日 | MARA Holdings 宣布与 Starwood 合作建设 AI 推理数据中心（宣布后股价涨17%） |

---

## 多方观点

### 官方/支持方

**Anthropic（Dario Amodei）**："Claude Code 不仅仅是一个编程工具，它是智能体 AI 时代的第一个真正大规模商业案例。我们的增长受限于算力，而不是需求。"

**NVIDIA（Jensen Huang）**："智能体就是印钞机，而算力就是油墨。"（Blackwell 定位为 Agent 时代基础设施）

**Sam Altman**："Peter Steinberger 加入 OpenAI 是为了推动下一代个人智能体……我们预期这将迅速成为核心业务。"

**IDC**："到2027年，G2000企业的 AI Agent 使用量将增加10倍，但 Token 和 API 调用量将增加1000倍。"

### 中立/分析方

**SemiAnalysis（Dylan Patel）**："你眨眼间，AI 吞噬了整个软件开发。4% 的 GitHub commits 来自 Claude Code，而这个数字在一个月前还是2%。按当前轨迹，2026年底将是20%+。"

**Deloitte**："推理将在2026年占全部 AI 算力的2/3。大多数推理仍将发生在数据中心，而非边缘设备。推理优化芯片市场将超过$500亿。"

**VAST Data**："2026年是 AI 推理之年。训练时代把资源集中在少数超大模型上；推理时代把价值分散给数十亿用户的每一次请求。"

### 质疑方/反对方

**开发者社区（Hacker News）**：Anthropic 的 OAuth 禁令被批评为"商业驱动的圈地行为"，将赚钱的企业 API 与消费级订阅隔离，但损害了开源生态。

**Google TPU 阵营**：NVIDIA GPU 推理成本是 Google TPU 的4倍，Alibaba 和 ByteDance 已将部分推理工作负载迁移至 TPU。

**能效质疑**：批评者指出 AI 推理的能源消耗问题——一个短的 GPT-4o 查询消耗0.43Wh 电力，2030年生成式 AI 查询总用电量将达 347 TWh，质疑这是否可持续。（MIT Technology Review）

---

## 数据表

| 指标 | 数值 | 时间 | 信源 |
|------|------|------|------|
| Claude Code ARR | $25亿 | 2026年2月 | Anthropic 官方 |
| Claude Code GitHub commits 占比 | 4%（全球公开） | 2026年2月 | SemiAnalysis |
| Claude Code GitHub commits 占比预测 | 20%+ | 2026年底 | SemiAnalysis |
| Claude Code 周活用户增速 | 翻倍 | 2026年1月以来 | Anthropic 官方 |
| Anthropic ARR | $140亿 | 2026年2月 | SiliconAngle |
| Anthropic G 轮融资 | $300亿 | 2026年2月12日 | Anthropic/CNBC |
| Anthropic 估值 | $3800亿 | 2026年2月 | Anthropic 官方 |
| OpenClaw GitHub stars | 14.5万+ | 2026年2月 | TechCrunch |
| AI Agent Token 增长（IDC） | 1000倍 | 预测至2027年 | IDC |
| 全球 AI Agent 数量预测（IDC） | 10亿+ | 预测至2029年 | IDC |
| 每日 Agent 操作（IDC） | 2170亿次 | 预测至2029年 | IDC |
| 每日 Token 消耗（IDC） | 3.7万亿 | 预测至2029年 | IDC |
| 推理占 AI 算力（2026） | 2/3 | 2026年预测 | Deloitte |
| 推理优化芯片市场 | $500亿+ | 2026年 | Deloitte |
| 全球 AI 数据中心资本支出 | $4000-4500亿 | 2026年 | Deloitte |
| 全球 AI 数据中心资本支出 | ~$1万亿 | 2028年 | Deloitte |
| NVIDIA Q3 FY2026 季度营收 | $570亿 | 2025年10月 | NVIDIA 官方财报 |
| NVIDIA FY2026 数据中心收入预测 | $1547亿 | FY2026 全年 | 分析师预测 |
| NVIDIA Blackwell 积压订单 | 360万台 | 2025年底 | 行业报道 |
| Broadcom AI 半导体收入 Q1 FY2026 | ~$82亿 | 预测 | Broadcom 管理层 |
| OpenAI Titan 定制 ASIC 合同估值 | $1500-2000亿 | 多年 | Mizuho 估计 |
| 数据中心用电量（2026） | 1000+ TWh | 2026年预测 | IEA |
| 数据中心用电量增幅（2030） | +160% | 2030年vs现在 | Goldman Sachs |
| 液冷市场规模（2025） | $28亿 | 2025年 | 行业报告 |
| 液冷市场规模（2032） | $210亿+ | 2032年预测 | 行业报告 |
| 液冷 CAGR | 30%+ | 2025-2032 | 行业报告 |
| 中国 AI 算力市场（2025） | $259亿 | 2025年 | IDC |
| 中国 AI 服务器市场全球占比 | 42% | 2025年 | 行业报告 |
| Agent 工作负载 vs 普通会话 Token 倍数 | 7x | 现状 | Anthropic SDK 文档 |
| 扩展思维算力倍数 | 100x+ | 现状 | Deloitte 报告 |
| 边缘 AI 芯片市场（2036） | $800亿+ | 预测 | IDTechEx |
| AI 芯片初创融资（2025年上半年） | $51亿 | 2025年 | 行业报告 |

---

## 争议点和未解问题

### 1. Claude Code 数据的可信度问题
**争议**：Anthropic 的 $25亿 ARR 和4% GitHub commits 数据均来自 Anthropic 官方 Series G 公告（存在融资背景的公关动机），SemiAnalysis 的20%预测是基于当时的增长率外推。

**建议**：4% 数据来源于 SemiAnalysis 的 GitHub 抓取分析（可重现），相对可信。ARR 数据属于自报，尚无第三方独立核实。

### 2. IDC 的1000倍推断是否夸大？
**争议**：IDC 预测依赖于"40% 企业应用嵌入 Agent"这一 Gartner 预测同步实现。实际采购周期和 Agent 部署复杂性可能导致滞后。历史上 IDC 和 Gartner 对 AI 渗透速度的预测倾向于过度乐观。

### 3. 推理算力需求能否转化为 NVIDIA 收入？
**争议**：分析师普遍认为 NVIDIA 推理市场份额将从90%+跌至2028年的20-30%。但 NVIDIA 的 CUDA 生态护城河使得这个预测存在很大不确定性。这是整个算力涟漪中最大的商业悬念。

### 4. OpenClaw 与 Claude Code 的命名混乱
**未解问题**：中文媒体混用"OpenClaw"指代 Claude Code，但这是两个不同产品。文章应明确区分，或将"OpenClaw 时刻"作为现象标签（类比 ChatGPT 时刻），而非产品名称。

### 5. 液冷技术渗透率预测差异
**争议**：各来源对2026年液冷渗透率的预测从40%到70%不等。传统数据中心改造成本高（$2-3M/MW）可能造成滞后。

### 6. 核能数据中心的时间线
**未解问题**：技术公司签署了20GW+ SMR 采购协议，但第一批 SMR 最早2030年后才能供电（中国玲龙一号是例外）。短期（2026-2027）数据中心仍将主要依赖天然气。

### 7. Anthropic 的 OAuth 封锁的真实动机（最佳切入点）
**争议**：官方说法是"防止用户滥用订阅"，但核心是：一个 Claude Max ($200/月) 用户通过 OpenClaw 跑 Agent 任务，可以消耗相当于正常 API 费用的**数千美元**算力，Anthropic 在赔本。这一细节本身就是"算力涟漪"的绝佳例证——**一个月 $200 的订阅竟然能消耗掉数千美元的推理算力**。

---

## 一手源清单

| 类型 | 标题/机构 | URL |
|------|-----------|-----|
| 官方公告 | Anthropic Series G 公告 | https://www.anthropic.com/news/anthropic-raises-30-billion-series-g-funding-380-billion-post-money-valuation |
| 官方公告 | Anthropic Claude 3.7 Sonnet & Claude Code 发布 | https://www.anthropic.com/news/claude-3-7-sonnet |
| 官方报告 | IDC FutureScape 2026 Agent Adoption | https://www.idc.com/resource-center/blog/agent-adoption-the-it-industrys-next-great-inflection-point/ |
| 研究报告 | Deloitte 2026 TMT Predictions - Compute | https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html |
| 研究报告 | SemiAnalysis "Claude Code is the Inflection Point" | https://newsletter.semianalysis.com/p/claude-code-is-the-inflection-point |
| 研究报告 | IEA Energy and AI 2025 | https://www.iea.org/reports/energy-and-ai/energy-supply-for-ai |
| 官方财报 | NVIDIA Q3 FY2026 财报 | https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2026 |
| 新闻报道 | CNBC: Anthropic $30B 融资 | https://www.cnbc.com/2026/02/12/anthropic-closes-30-billion-funding-round-at-380-billion-valuation.html |
| 新闻报道 | CNBC: Broadcom AI 芯片销售翻倍 | https://www.cnbc.com/2025/12/11/broadcom-avgo-q4-earnings-2025.html |
| 新闻报道 | TechCrunch: Peter Steinberger 加入 OpenAI | https://techcrunch.com/2026/02/15/openclaw-creator-peter-steinberger-joins-openai/ |
| 新闻报道 | The Register: Anthropic 禁止第三方 OAuth | https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access/ |
| 分析报道 | VentureBeat: NVIDIA $200亿押注 Groq | https://venturebeat.com/infrastructure/inference-is-splitting-in-two-nvidias-usd20b-groq-bet-explains-its-next-act |
| 分析报道 | SDxCentral: 2026年推理市场大开 | https://www.sdxcentral.com/analysis/ai-inferencing-will-define-2026-and-the-markets-wide-open/ |
| 分析报道 | VAST Data: 2026年推理之年 | https://www.vastdata.com/blog/2026-the-year-of-ai-inference |
| 官方文档 | Claude Code 官方文档（Token 成本管理） | https://code.claude.com/docs/en/costs |
| 能源分析 | Goldman Sachs: 核能与 AI 数据中心 | https://www.goldmansachs.com/insights/articles/is-nuclear-energy-the-answer-to-ai-data-centers-power-consumption |
| 能源分析 | MARA "Powering the Inference Era of AI" | https://www.mara.com/posts/powering-the-inference-era-of-ai |
| 中文数据 | 证券时报: AI催生巨量Token消耗 算力租赁供不应求 | https://www.stcn.com/article/detail/3648600.html |

---

## 潜在配图素材

| 图表类型 | 内容描述 | 建议来源/制作方式 |
|----------|----------|-----------------|
| 折线图 | 推理 vs 训练算力占比演变（2023: 1/3 → 2025: 1/2 → 2026: 2/3） | 根据 Deloitte 数据自制 |
| 数据图 | Claude Code ARR 增长曲线（$5亿→$12.5亿→$25亿，配合 GitHub commits 占比增速） | 根据公开财报数据自制 |
| 对比图 | AI Agent 7x Token 倍数效应示意图（单次 Chat vs Agent 任务的 Token 消耗对比） | 示意图自制 |
| 信息图 | "1000倍涟漪"：从1个 Claude Code 用户 → Token 消耗 → 芯片需求 → 数据中心 → 电网 → 核能的全链路 | 原创信息图 |
| 财务图 | NVIDIA 推理市场份额预测（90%+ 2025年 → 20-30% 2028年预测）vs Broadcom ASIC 崛起 | 根据分析师预测数据自制 |
| 地图/数据 | 全球 AI 数据中心资本支出分布图（$4000-4500亿，重点标注 hyperscaler 项目） | 参考 Deloitte 数据 |
| 对比图 | 液冷 vs 风冷极限（风冷上限41kW vs Blackwell需求100kW+，直观展示为何液冷成为刚需） | 根据 enkiai 数据自制 |
| 新闻截图 | OpenClaw GitHub 14.5万 stars 页面截图 | GitHub OpenClaw 页面 |

---

## 核心写作线索（给智子/涟漪人设）

**最佳切入点**：OpenClaw 事件是一块石头投入水中——$200/月的订阅，能消耗数千美元的推理算力。Anthropic 封禁 OAuth，不是因为安全，是因为赔不起。这才是涟漪的真实刻度。

**叙事结构建议**：
1. 开篇：OpenClaw 事件（石头入水）
2. 第一圈涟漪：Agent 的 Token 倍增效应（7x普通 → 100x扩展思维）
3. 第二圈涟漪：推理超越训练，成为算力主战场（1/3→2/3）
4. 第三圈涟漪：谁在造芯片？NVIDIA vs ASIC 的暗战
5. 第四圈涟漪：机房喝水，电网撑腰，液冷和核能登场
6. 被忽视的机会：液冷、边缘推理、推理优化软件（vLLM等）
7. 结尾：这不是 AI 泡沫，是基础设施的一次范式更替
