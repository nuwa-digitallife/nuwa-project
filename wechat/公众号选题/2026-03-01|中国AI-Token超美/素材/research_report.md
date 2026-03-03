# 素材报告：中国AI-Token超美
采集时间：2026-03-03

---

## 核心事实（已验证）

### 事实1：超越时间点与规模
- **2026年2月9日-15日当周**，中国AI模型在OpenRouter平台的token调用量**首次超越**美国模型
  - 中国模型：4.12万亿 Token
  - 美国模型：2.94万亿 Token
  - 来源：OpenRouter平台周数据（二手源，媒体报道引用）
- **2月16日-22日**，差距进一步扩大：
  - 中国模型：5.16万亿 Token（三周内涨127%）
  - 美国模型：2.7万亿 Token（下降）
  - 来源：[36氪英文报道](https://eu.36kr.com/en/p/3700980530851712)
- **中国模型占OpenRouter前10大模型token消耗总量的61%**（5.3万亿/8.7万亿）
  - 来源：[Dataconomy](https://dataconomy.com/2026/02/25/chinese-ai-models-hit-61-market-share-on-openrouter/)，[SCMP](https://www.scmp.com/tech/tech-trends/article/3344587/chinas-minimax-moonshot-top-ai-token-use-ranking-ending-year-us-dominance)

### 事实2：平台背景
- **OpenRouter** 是全球最大AI模型API聚合平台，汇聚数百种大语言模型，用户超500万开发者
- OpenRouter 2025年全年分析了**超100万亿个token**，发布了《State of AI》报告
- 来源：[OpenRouter State of AI 2025](https://openrouter.ai/state-of-ai)，[arXiv论文版](https://arxiv.org/html/2601.10088v1)
- **重要局限（待关注）**：有批评者指出OpenRouter仅占全球AI消费约2%，大企业用户（Fortune 500、Salesforce、Microsoft）直接接入OpenAI/Anthropic官方API，不通过OpenRouter

### 事实3：OpenRouter全年趋势（一手源：官方报告）
- 2025年全年，中国开源模型从占总用量**1.2%增长到约30%的周用量**
- DeepSeek全年贡献14.37万亿token，Qwen贡献5.59万亿token（OpenRouter内部数据）
- 编程类任务已从2025年初的11%增长到全年超50%的token消耗占比
- 来源：[OpenRouter State of AI PDF](https://openrouter.ai/assets/State-of-AI.pdf)，[a16z解读](https://a16z.com/state-of-ai/)

---

## 关键人物/公司

### MiniMax（极光）
- **核心产品**：MiniMax M2.5（2026年2月13日发布）
- **关键数据**：发布不到一周即登顶OpenRouter周调用量榜首，单周2.45万亿Token，环比增197%
- **技术定位**：全球首款专为Agentic工作流原生设计的生产级模型
- **基准成绩**：SWE-Bench Verified 80.2%，Multi-SWE-Bench 51.3%，BrowseComp 76.3%
- **官方定价**：输入$0.30/百万token，输出$1.20/百万token（一手源：[MiniMax官方文档](https://platform.minimax.io/docs/pricing/overview)）
- **速度**：100 token/秒原生推理，接近其他前沿模型速度的2倍

### Moonshot AI（月之暗面）/ Kimi
- **核心产品**：Kimi K2.5
- **关键数据**：OpenRouter周调用量第二名，1.21万亿Token（环比-20%，但仍保持第二）
- **公司里程碑**：2026年2月成为中国史上最快达到"十亿美元独角兽"（Decacorn）的公司（10亿美元估值）
- **融资情况**：2026年2月完成7亿美元融资，估值超100亿美元（Bloomberg报道，目标估值可能达120亿美元）
- **收入爆发**：K2.5上线后20天内的累计收入已超过2025年全年总收入
- **海外突破**：K2.5发布后，海外付费用户增长约4倍，海外收入首次超过国内
- 来源：[TechNode](https://technode.com/2026/02/24/kimis-moonshot-ai-sees-revenue-surge-secures-over-700-million-in-new-funding/)，[SCMP估值](https://www.scmp.com/tech/tech-trends/article/3343927/moonshot-ai-targets-us12-billion-valuation-overseas-revenue-surges-kimi-models)

### 智谱AI（Zhipu AI）
- **核心产品**：GLM-5
- **关键数据**：OpenRouter第三名，7800亿Token（环比增158%）
- **定价**：输入$0.30/百万token，输出$2.55/百万token（来源：媒体报道，待官方核实）

### DeepSeek（深度求索）
- **核心产品**：DeepSeek V3.2（OpenRouter第五名）
- **官方API定价**（一手源：[DeepSeek API文档](https://api-docs.deepseek.com/quick_start/pricing)）：
  - deepseek-chat(V3.2): 输入$0.28/百万token（缓存未命中），缓存命中$0.028，输出$0.42
  - V3.2-Exp实验版：输入降至$0.028（缓存命中），$0.28（缓存未命中），输出$0.42
- **全球市场**：125M月活跃用户（2025年5月），API年化收入约2.2亿美元
- **训练成本**：V3声称仅需550万美元训练成本（此数字存在争议，见争议点）

### 阿里通义千问（Qwen）
- **关键数据**：OpenRouter全球市场份额一度超12.3%，居全球第四（超越OpenAI和Llama系列）
- **中国企业市场**：2025年上半年，中国企业日均大模型消耗10.2万亿Token，其中阿里通义占比17.7%位列第一
- **增长速度**：较2024年下半年，2025年上半年日均调用量暴增363%
- **客户规模**：超100万家客户接入
- 来源：[沙利文报告/证券时报](https://stcn.com/article/detail/3314916.html)（待核实具体报告名称）

---

## 时间线

| 时间 | 事件 |
|------|------|
| 2025年初 | 中国开源模型占OpenRouter总用量约1.2% |
| 2025年1月 | DeepSeek R1发布，引发全球关注；Nvidia市值单日蒸发约6000亿美元 |
| 2025年全年 | 中国开源模型市场份额从1.2%增长到约30%（OpenRouter数据） |
| 2025年5月 | DeepSeek月活跃用户达1.25亿 |
| 2025年12月3日 | 中国激活全球最大分布式AI算力网络（FNTF），跨越40个城市 |
| 2025年下半年 | Chatham House发布报告：中低成本中国AI已在美国本土市占率约80%初创生态 |
| 2026年1月初 | Moonshot AI完成5亿美元C轮融资，估值43亿美元 |
| 2026年2月13日 | MiniMax发布M2.5，定位为全球首款Agentic原生生产级模型 |
| 2026年2月17日 | Bloomberg报道Moonshot AI寻求100亿美元估值新融资 |
| 2026年2月18日 | Moonshot AI完成7亿美元融资，达到Decacorn（十亿独角兽）地位 |
| 2026年2月24日 | OpenRouter发布周报：中国模型首次占据全球前三 |
| **2026年2月9-15日** | **中国模型token调用量（4.12万亿）首次超越美国（2.94万亿）** |
| **2026年2月16-22日** | **中国模型（5.16万亿）vs 美国（2.7万亿），差距拉大** |
| 2026年2月24日 | Moonshot AI：K2.5上线20天收入超2025年全年 |
| 2026年2月28日 | CGTN、观察者网等发布"中国AI调用量超美"相关报道 |

---

## 多方观点

### 支持派：这是真实的产业转移

**Chatham House（英国皇家国际事务研究所）**（中立智库）：
> "约80%的美国AI创业者正在使用中国开源模型。部分美国投资机构选择Kimi K2，因为它'性能更强，价格远低于OpenAI和Anthropic'。"
> 来源：[Chatham House分析](https://www.chathamhouse.org/2025/11/low-cost-chinese-ai-models-forge-ahead-even-us-raising-risks-us-ai-bubble)

**Goldman Sachs**：
> 预计中国AI提供商2026年数据中心投资将超700亿美元，算力需求持续爆炸性增长
> 来源：[Goldman Sachs分析](https://www.goldmansachs.com/insights/articles/chinas-ai-providers-expected-to-invest-70-billion-dollars-in-data-centers-amid-overseas-expansion)

**Microsoft 2026年全球AI采用报告**：
> DeepSeek在发展中国家表现出"强势主导地位"，非洲DeepSeek使用量估计是其他地区的2-4倍
> 来源：[Euronews引述Microsoft报告](https://www.euronews.com/next/2026/01/09/deepseeks-ai-gains-traction-in-developing-nations-microsoft-report-says/)

### 质疑派：61%的数字存在误导性

**GlobalSemiResearch（行业分析机构）**：
> "OpenRouter仅占全球AI消费约2%。真正的消费大户——Fortune 500和大型SaaS厂商（Salesforce、Microsoft等）——消耗了全球90%以上的token，它们绝不会通过OpenRouter调用。61%的份额是在'创新实验室'层面，尚未渗透企业'核心数据中心'。"
> 来源：[China Token Exports分析](https://globalsemiresearch.substack.com/p/china-token-exports-between-statistical)

**使用场景质疑（来自知乎分析）**：
> "中国模型调用中文本生成占68%、代码生成占12%；美国模型调用中代码生成占35%、复杂推理占28%。任务复杂度存在差异，量大不等于价值高。"

**春节效应质疑**：
> 2026年2月恰逢中国春节，国内爆发"AI红包大战"，产生外溢效应，可能人为拉高了数字

### 中立/结构派：价格战是历史必然

**中国AI价格战逻辑**（多位分析师观点）：
- 中国AI企业用VC资金进行补贴定价（"以价换量"战略）
- 但底层原因是真实的成本优势：MoE架构、开源生态、推理优化技术
- DeepSeek用H800等次级芯片实现接近H100的推理效果，将成本降低90%

**Winsomemarketing（批评中立）**：
> "中国价格战是'不可持续的剧场'——中国AI初创企业用投资人的钱做赔本买卖，而西方公司在尝试建立可持续商业模式。"
> 来源：[The Great AI Cost Illusion](https://winsomemarketing.com/ai-in-marketing/the-great-ai-cost-illusion-why-chinas-price-war-is-unsustainable-theater/)

---

## 数据表

### 表1：主要中美AI模型API定价对比（2025年底-2026年初）

| 模型 | 输入价格（/百万token） | 输出价格（/百万token） | 信源 |
|------|-------------------|--------------------|------|
| MiniMax M2.5 | $0.30 | $1.20 | [官方文档](https://platform.minimax.io/docs/pricing/overview) |
| Zhipu GLM-5 | $0.30 | $2.55 | 媒体报道（待官方核实） |
| DeepSeek V3.2 | $0.28（缓存未命中）| $0.42 | [官方文档](https://api-docs.deepseek.com/quick_start/pricing) |
| DeepSeek V3.2-Exp | $0.28（缓存未命中） | $0.42 | [VentureBeat](https://venturebeat.com/ai/deepseeks-new-v3-2-exp-model-cuts-api-pricing-in-half-to-less-than-3-cents) |
| OpenAI GPT-4o | $2.50 | $10.00 | 媒体报道 |
| OpenAI GPT-5.2 | $1.75 | $14.00 | 媒体报道 |
| Anthropic Claude Opus 4.6 | $5.00 | $25.00 | 媒体报道 |

**价格差倍数**：MiniMax M2.5 vs Claude Opus 4.6，输入便宜约17倍，输出便宜约21倍

### 表2：2026年2月OpenRouter周调用量TOP 5

| 排名 | 模型 | 公司 | 国家 | 周调用量（万亿Token） | 环比 |
|------|------|------|------|-----------------|------|
| 1 | MiniMax M2.5 | MiniMax | 中国 | 2.45 | +197% |
| 2 | Kimi K2.5 | Moonshot AI | 中国 | 1.21 | -20% |
| 3 | GLM-5 | 智谱AI | 中国 | 0.78 | +158% |
| 4 | （美国模型）| - | 美国 | - | - |
| 5 | DeepSeek V3.2 | 深度求索 | 中国 | - | - |

数据来源：[36氪](https://eu.36kr.com/en/p/3700980530851712)，[Dataconomy](https://dataconomy.com/2026/02/25/chinese-ai-models-hit-61-market-share-on-openrouter/)（均为二手报道，一手源为OpenRouter平台数据）

### 表3：中美算力与投资对比

| 指标 | 数据 | 来源 |
|------|------|------|
| 美国全球GPU算力份额（2025年5月） | 约75% | Epoch AI |
| 中国全球GPU算力份额（2025年5月） | 约15% | Epoch AI |
| 中国AI数据中心2026年投资预期 | 超700亿美元 | Goldman Sachs |
| 中国数据中心电力需求增长（2026年） | 25% | Goldman Sachs |
| 中国智算中心规模增长（2025年） | 超40% | Global Times |
| DeepSeek V3训练成本（声明值） | 550万美元 | DeepSeek（待核实） |
| OpenAI/Anthropic类似模型训练成本 | 数亿美元级别 | 媒体估算 |

---

## 争议点和未解问题

### 争议1：OpenRouter数据的代表性
- **问题**：OpenRouter仅占全球AI消费约2%，主要是开发者/实验用途，不含大企业直采
- **待验证**：是否有更广口径的中美API调用量比较数据？（例如：包含Azure OpenAI服务的数据）
- **风险**：直接用"全球token超美"表述，容易被专业读者质疑

### 争议2：DeepSeek训练成本550万美元
- David Sacks（白宫AI/加密顾问）曾公开质疑此数字
- 可能不含研发投入、数据成本等隐性成本
- **建议**：写作时用"DeepSeek声称"而非断言

### 争议3：使用场景的质量差异
- 中国模型调用量中Roleplay（角色扮演）占约33%（OpenRouter 2025年报告）
- 美国模型调用中代码/复杂推理占比更高
- 即"量大不等于价值高"——中国模型主导的是低单价、高频、娱乐化场景

### 争议4：价格战可持续性
- 多个分析认为中国模型的低价依赖VC补贴，长期可能不可持续
- 反驳：MoE架构等技术创新带来的效率优势是真实的，非纯粹补贴

### 争议5：春节效应
- 2月超越是否受中国春节"AI红包大战"推动？若3月数据回落，则可能是季节性因素

### 未解问题
1. 除OpenRouter外，是否有其他平台数据支撑这一趋势？
2. 中国企业直接调用美国模型（如通过Azure）的情况如何？
3. 中国模型在企业级市场（非开发者实验）的渗透情况？
4. MiniMax M2.5的2.45万亿Token，是否有大量来自公司自己的"洗量"测试？

---

## 一手源清单

| 来源 | 类型 | URL |
|------|------|-----|
| OpenRouter State of AI 2025报告 | 官方平台报告 | https://openrouter.ai/state-of-ai |
| OpenRouter State of AI PDF全文 | 官方 | https://openrouter.ai/assets/State-of-AI.pdf |
| OpenRouter论文arXiv版 | 学术 | https://arxiv.org/html/2601.10088v1 |
| MiniMax M2.5官方发布博客 | 官方 | https://www.minimax.io/news/minimax-m25 |
| MiniMax官方定价文档 | 官方 | https://platform.minimax.io/docs/pricing/overview |
| MiniMax M2.5 HuggingFace模型卡 | 官方 | https://huggingface.co/MiniMaxAI/MiniMax-M2.5 |
| DeepSeek官方API定价 | 官方 | https://api-docs.deepseek.com/quick_start/pricing |
| DeepSeek API详细定价（USD） | 官方 | https://api-docs.deepseek.com/quick_start/pricing-details-usd |
| Goldman Sachs中国AI数据中心分析 | 权威机构 | https://www.goldmansachs.com/insights/articles/chinas-ai-providers-expected-to-invest-70-billion-dollars-in-data-centers-amid-overseas-expansion |
| Chatham House低成本AI风险分析 | 权威智库 | https://www.chathamhouse.org/2025/11/low-cost-chinese-ai-models-forge-ahead-even-us-raising-risks-us-ai-bubble |
| Kimi K2.5 OpenRouter数据页 | 平台数据 | https://openrouter.ai/moonshotai/kimi-k2.5 |
| OpenRouter官方2025年State of AI公告 | 官方 | https://openrouter.ai/announcements/the-2025-state-of-ai-report |

---

## 关键媒体报道（二手源，用于发现线索）

| 媒体 | 报道标题 | URL |
|------|---------|-----|
| SCMP | China's MiniMax, Moonshot top AI token use ranking | https://www.scmp.com/tech/tech-trends/article/3344587/chinas-minimax-moonshot-top-ai-token-use-ranking-ending-year-us-dominance |
| 36氪（英文） | February Sees Surge in AI Usage | https://eu.36kr.com/en/p/3700980530851712 |
| CGTN | Chinese AI models overtake U.S. rivals | https://news.cgtn.com/news/2026-02-28/Chinese-AI-models-overtake-U-S-rivals-in-global-token-usage-1L8h5rMl26c/p.html |
| Dataconomy | Chinese AI Models Hit 61% Market Share | https://dataconomy.com/2026/02/25/chinese-ai-models-hit-61-market-share-on-openrouter/ |
| TechBriefly | Chinese AI models dominate top 3 | https://techbriefly.com/2026/02/25/chinese-ai-models-dominate-top-3-spots-on-openrouter-platform/ |
| The China Academy | Kimi Moonshot Fastest Decacorn | https://thechinaacademy.org/kimi-moonshot-ai-becomes-chinas-fastest-decacorn-as-20-day-revenue-surpasses-entire-2025-total-china-ai-daily-february-24-2026/ |
| Bloomberg | Moonshot Seeks $10B Valuation | https://www.bloomberg.com/news/articles/2026-02-17/china-ai-startup-moonshot-seeks-10-billion-value-in-new-funding |
| GlobalSemiResearch | 质疑文章：Statistical Illusions | https://globalsemiresearch.substack.com/p/china-token-exports-between-statistical |
| 观察者网 | Token首次全面超越 | https://www.guancha.cn/xinzhiguanchasuo/2026_02_28_808259.shtml |
| MIT Technology Review | What's next for Chinese open-source AI | https://www.technologyreview.com/2026/02/12/1132811/whats-next-for-chinese-open-source-ai/ |

---

## 潜在配图素材

1. **价格对比图**：中国主要模型 vs 美国主要模型的每百万Token价格柱状图
   - 数据来源：各官方API文档（MiniMax、DeepSeek官方；OpenAI、Anthropic官网）
   - 视觉效果：中美价差约10-20倍，强烈视觉冲击

2. **OpenRouter周调用量趋势图**：2025年全年至2026年2月，中美模型份额变化曲线
   - 来源：OpenRouter State of AI报告图表（[PDF](https://openrouter.ai/assets/State-of-AI.pdf)）

3. **全球排名快照**：2026年2月24日当周OpenRouter TOP 10榜单（截图）
   - 可从OpenRouter官网直接截图

4. **Moonshot估值增长图**：从300M种子轮到120亿美元目标的融资时间线
   - 数据：种子轮$300M→A轮→B轮→$43亿→$120亿（目标）

5. **China AI采用地图**：全球南方（非洲、东南亚、南美）DeepSeek采用热力图
   - 可参考 Microsoft Global AI Adoption 2025 报告图表

6. **产业链传导示意图**（需自制）：
   - Token超越→开发者选择→算力需求→数据中心投资→相关公司受益
   - 这是智子人设的核心叙事，建议用流程图形式

---

## 写作注意事项（研究员附注）

1. **核心数据口径务必精确**：数据来自OpenRouter（全球开发者API聚合平台），不是全球全量数据。标题可用"在全球最大AI API平台上，中国模型首次超越美国"，而非"中国AI全面超美"

2. **争议点可作为文章深度**：直接呈现"量大不等于价值高"的质疑，反而增加可信度，符合智子"涟漪观察"人设

3. **MiniMax M2.5是核心催化剂**：文章应把M2.5发布（2月13日）视为触发点，解释为何单周暴增197%

4. **地缘叙事的悖论**：美国芯片制裁→中国被迫在次级芯片上做推理优化→反而产生成本优势→全球开发者"用脚投票"。这是文章最有力的地缘视角

5. **算力投资涟漪**：OpenRouter数据到国内算力股涨停（2月后股市表现），到Goldman Sachs预测700亿投资，是清晰的一阶效应

6. **Moonshot Kimi案例极佳**：20天收入超全年，估值从43亿到120亿，是"调用量→商业变现"最强案例，可作为文章的具体锚点
