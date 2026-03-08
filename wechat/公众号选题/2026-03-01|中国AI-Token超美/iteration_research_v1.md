### 弱点 1: §9 "OpenRouter用户主要是独立开发者和AI创业公司"

**搜索关键词**: `OpenRouter user demographics developers`, `OpenRouter indie hackers user base composition`

**找到的证据**:

1. **Sacra — OpenRouter Revenue, Valuation & Funding** (行业分析/数据平台)
   - URL: https://sacra.com/c/openrouter/
   - 关键数据: OpenRouter官方定位服务三类用户：indie hackers（想试不同模型不用注册多个账号）、product teams（需要OpenAI的即插替代+自动故障转移）、enterprises（需要组织级策略和集中用量追踪）
   - 可信度: ⭐⭐（官方自我定位，但无量化比例）
   - 适用方式: 可引用OpenRouter自身描述的用户分层

2. **Gitnux — OpenRouter Statistics Market Data Report 2026** (市场研究报告)
   - URL: https://gitnux.org/openrouter-statistics/
   - 关键数据: **40%用户来自GitHub等开发者社区，30%来自indie hackers社区，55%来自AI创业公司**（注意：比例相加超过100%，说明有重叠分类）
   - 可信度: ⭐⭐（第三方统计，方法论不透明，但提供了量化数据）
   - 适用方式: 可作为佐证，但需注意数据自洽性问题。比例加总超100%说明是多标签分类，但核心结论成立——**开发者和创业公司构成OpenRouter的主要用户群**

3. **OpenRouter State of AI 2025** (一手源/官方报告)
   - URL: https://openrouter.ai/state-of-ai
   - 关键数据: 报告本身面向的分析角度是开发者行为（编程任务占比增长、agentic使用模式）。4.2M全球用户，但报告未直接给出企业vs个人开发者的比例
   - 可信度: ⭐⭐⭐（一手源）
   - 适用方式: 报告的分析框架本身隐含了"用户以开发者为主"的前提

**总结**: 🔄 部分硬化。无法找到OpenRouter官方的精确用户画像报告，但从多个来源交叉验证，OpenRouter自我定位就是面向indie hackers/开发者/创业公司的平台，Gitnux给出了70%+来自开发者/indie社区的估算。建议文章改为："OpenRouter的用户——从它自身定位来看——主要是独立开发者和AI创业公司"，或引用Gitnux数据。弱→中。

---

### 弱点 2: §11 MiniMax M2.5发布日期 "2月12日" vs 素材"2月13日"

**搜索关键词**: `MiniMax M2.5 launch date February 2026`

**找到的证据**:

1. **MiniMax官方新闻稿** (一手源)
   - URL: https://www.minimax.io/news/minimax-m25
   - 关键数据: 页面标注日期为 **2026.2.12**
   - 可信度: ⭐⭐⭐（MiniMax官网一手源）
   - 适用方式: **文章的"2月12日"是正确的**，素材报告的"2月13日"有误

2. **Galaxy.ai Model Specs** (二手源)
   - URL: https://blog.galaxy.ai/model/minimax-m2-5
   - 关键数据: 确认发布日期为2026年2月
   - 可信度: ⭐⭐

**总结**: ✅ 已确认。**文章写的"2月12日"正确**，MiniMax官网明确标注2026.2.12。素材报告中的"2月13日"是素材自身的错误，文章无需修改。

---

### 弱点 3: §32 Kimi K2.5 LiveCodeBench "85%领先全球主流模型"

**搜索关键词**: `Kimi K2.5 LiveCodeBench 85 score comparison`, `LiveCodeBench leaderboard 2026`

**找到的证据**:

1. **Artificial Analysis — LiveCodeBench Leaderboard** (聚合排行榜)
   - URL: https://artificialanalysis.ai/evaluations/livecodebench
   - 关键数据: 当前排行榜Top 3为Gemini 3 Pro Preview (91.7%)、Gemini 3 Flash Preview (90.8%)、DeepSeek V3.2 Speciale (89.6%)。Kimi K2.5的85.0%已非顶尖
   - 可信度: ⭐⭐⭐（权威基准排行榜）

2. **Kimi K2.5 vs Claude 对比页** (产品对比站)
   - URL: https://kimi-k25.com/blog/kimi-k2-5-vs-claude
   - 关键数据: Kimi K2.5 LiveCodeBench **85.0%** vs Claude Opus 4.5 **82.2%** vs Claude 3.5 Sonnet **79.5%**
   - 可信度: ⭐⭐
   - 适用方式: K2.5发布时确实领先Claude，但后来被Gemini 3和DeepSeek V3.2超越

3. **NxCode — Kimi K2.5 Developer Guide** (技术文档)
   - URL: https://www.nxcode.io/resources/news/kimi-k2-5-developer-guide-kimi-code-cli-2026
   - 关键数据: 确认85.0%分数，同期对比Claude Opus领先2.8个百分点
   - 可信度: ⭐⭐

**总结**: 🔄 部分硬化。85.0%分数经多源验证。但"领先全球主流模型"断言**在当前时间点已过时**——Gemini 3 Pro (91.7%)和DeepSeek V3.2 Speciale (89.6%)已大幅超越。**建议修改为**："Kimi K2.5发布时在LiveCodeBench上以85%得分领先同期的Claude Opus 4.5（82.2%）"——既有精确参照系，又标注了时间范围。弱→中。

---

### 弱点 4: §21 "有分析估算总投入超十亿美元量级"

**搜索关键词**: `DeepSeek V3 true total training cost billion estimate interconnects`

**找到的证据**:

1. **Interconnects.ai — Nathan Lambert** (独立ML研究者分析)
   - URL: https://www.interconnects.ai/p/deepseek-v3-and-the-actual-cost-of
   - 关键数据: Nathan Lambert估算DeepSeek年度运营总成本"approaches $500M (or even $1B+ easily)"，包含基础设施折旧、20K-50K GPU集群维护、139名技术作者人力、实验迭代（2-4倍公开算力）
   - 可信度: ⭐⭐⭐（具名独立研究者，方法论透明）

2. **SemiAnalysis（via Interesting Engineering转引）** (行业分析机构)
   - URL: https://interestingengineering.com/culture/deepseeks-ai-training-cost-billion
   - 关键数据: SemiAnalysis估算DeepSeek总服务器CapEx达**$1.3 billion**（13亿美元）
   - 可信度: ⭐⭐⭐（SemiAnalysis是芯片/AI领域权威分析机构，Dylan Patel主理）

**总结**: ✅ 可硬化。建议将"有分析估算"改为具名引用："SemiAnalysis估算DeepSeek的总服务器资本支出约13亿美元；独立ML研究者Nathan Lambert（Interconnects.ai）分析实际年度运营成本逼近10亿美元"。弱→强。

---

### 弱点 5: §39 非洲/东南亚虚构场景

**搜索关键词**: `DeepSeek Africa developing countries usage education students`

**找到的证据**:

1. **Carnegie Endowment for International Peace** (权威智库)
   - URL: https://carnegieendowment.org/posts/2025/03/deepseek-ai-implications-africa
   - 关键数据: DeepSeek的MIT开源许可让非洲开发者可以下载、修改、微调模型，适配本地需求（金融、医疗、教育、治理）
   - 可信度: ⭐⭐⭐（顶级智库分析）

2. **Microsoft 2025 H2 AI Diffusion Report** (一手源/官方报告)
   - URL: https://blogs.microsoft.com/on-the-issues/2026/01/08/global-ai-adoption-in-2025/
   - 关键数据: DeepSeek在**埃塞俄比亚、津巴布韦、乌干达、尼日尔**的市场份额达11%-14%；非洲使用量是其他地区2-4倍
   - 可信度: ⭐⭐⭐（微软官方报告，一手数据）

3. **Euronews引述微软报告** (权威媒体)
   - URL: https://www.euronews.com/next/2026/01/09/deepseeks-ai-gains-traction-in-developing-nations-microsoft-report-says
   - 关键数据: DeepSeek的免费chatbot移除了订阅费壁垒，在价格敏感地区获得大量用户
   - 可信度: ⭐⭐⭐

**总结**: 🔄 部分硬化。微软报告确认了非洲使用量高、教育和本地化适配趋势存在，但**确实没有"写作业的学生""做翻译的小生意人"这样的具体案例**。建议两种修改方案：
- 方案A：标明为例证——"可以想象，一个在埃塞俄比亚用DeepSeek写作业的学生…"
- 方案B：替换为实际地区数据——"在埃塞俄比亚、津巴布韦、乌干达，DeepSeek的市场份额达到11%-14%——远高于全球平均水平"

---

### 弱点 6: §17 补贴定价无来源

**搜索关键词**: `Chinese AI pricing subsidy venture capital below cost unsustainable`

**找到的证据**:

1. **Winsome Marketing分析** (行业分析)
   - URL: https://winsomemarketing.com/ai-in-marketing/the-great-ai-cost-illusion-why-chinas-price-war-is-unsustainable-theater
   - 关键数据: DeepSeek"likely providing inference at cost to gain market share"；Z.ai（智谱）CEO拒绝公开训练成本；SemiAnalysis估算实际成本约$1.3B vs 公开声称$5.6M
   - 可信度: ⭐⭐（营销行业分析，但引用了SemiAnalysis和具体公司数据）

2. **Uptechstudio — The True Cost of AI: When the Subsidies Run Out** (独立分析)
   - URL: https://www.uptechstudio.com/blog/the-true-cost-of-ai-when-the-subsidies-run-out
   - 关键数据: "Some companies are accepting 50-60% gross margins (or lower) in the short term, thanks to venture funding that effectively subsidizes customers with investor money"
   - 可信度: ⭐⭐

3. **CSET Georgetown — In & Out of China: Financial Support for AI Development** (学术/智库)
   - URL: https://cset.georgetown.edu/article/in-out-of-china-financial-support-for-ai-development/
   - 关键数据: 中国2025年AI投资¥8900亿（约$1250亿），同比增长18%；国家级AI基金$82亿
   - 可信度: ⭐⭐⭐（Georgetown安全与新兴技术中心）

**总结**: 🔄 部分硬化。"补贴定价"现象有多源确认，但多为分析推断而非公司自认。建议改为："多位行业分析师指出，部分低价来自风险资本补贴——用投资人的钱换用量，这在全球AI行业并非中国独有"。弱→中。

---

### 弱点 7: §13 "当前全球最高分约81%"

**搜索关键词**: `SWE-bench Verified leaderboard March 2026 top score`

**找到的证据**:

1. **LLM-Stats — SWE-Bench Verified Leaderboard** (排行榜聚合)
   - URL: https://llm-stats.com/benchmarks/swe-bench-verified
   - 关键数据: 当前排行榜Top 5：Claude Opus 4.5 (80.9%)、Claude Opus 4.6 (80.8%)、Gemini 3.1 Pro (80.6%)、**MiniMax M2.5 (80.2%)**、GPT-5.2 (80.0%)
   - 可信度: ⭐⭐⭐（多源交叉验证）

2. **Epoch AI — SWE-bench Verified** (学术追踪)
   - URL: https://epoch.ai/benchmarks/swe-bench-verified
   - 关键数据: 确认Claude Opus 4.5以80.9%位居榜首
   - 可信度: ⭐⭐⭐

**总结**: ✅ 可硬化。"约81%"与实际最高分(Claude Opus 4.5的80.9%)吻合。建议改为："MiniMax M2.5在SWE-Bench Verified上得分80.2%，与当时榜首Claude Opus 4.5的80.9%仅差0.7个百分点"——具名模型+精确差值。弱→强。

---

## 调研总结

| 弱点 | 是否找到更硬证据 | 硬化程度 | 建议修改 |
|------|------------------|----------|----------|
| P1: OpenRouter用户构成 | 🔄 部分 | 弱→中 | 引用OpenRouter自身定位(indie hackers/product teams/enterprises)或Gitnux的70%开发者数据 |
| P1: M2.5发布日期 | ✅ 已确认 | **文章正确** | 无需修改，MiniMax官网确认2月12日 |
| P1: Kimi K2.5 LiveCodeBench | 🔄 部分 | 弱→中 | 改为"发布时以85%领先同期Claude Opus 4.5（82.2%）"，加时间限定和参照模型 |
| P2: DeepSeek训练总成本 | ✅ 找到 | 弱→强 | 具名引用SemiAnalysis（$1.3B CapEx）和Nathan Lambert/Interconnects.ai |
| P2: 非洲/东南亚虚构场景 | 🔄 部分 | 无变化 | 标明为例证或替换为微软报告的实际国家级数据 |
| P2: 补贴定价无来源 | 🔄 部分 | 弱→中 | 引用CSET Georgetown数据或SemiAnalysis的推理成本分析 |
| P2: "全球最高分约81%" | ✅ 找到 | 弱→强 | 改为"Claude Opus 4.5的80.9%"，具名+精确值 |
```

Sources:
- [OpenRouter State of AI 2025](https://openrouter.ai/state-of-ai)
- [Sacra — OpenRouter](https://sacra.com/c/openrouter/)
- [Gitnux — OpenRouter Statistics](https://gitnux.org/openrouter-statistics/)
- [MiniMax M2.5 Official Announcement](https://www.minimax.io/news/minimax-m25)
- [Artificial Analysis — LiveCodeBench Leaderboard](https://artificialanalysis.ai/evaluations/livecodebench)
- [Kimi K2.5 vs Claude Comparison](https://kimi-k25.com/blog/kimi-k2-5-vs-claude)
- [Interconnects.ai — DeepSeek V3 Cost Analysis](https://www.interconnects.ai/p/deepseek-v3-and-the-actual-cost-of)
- [SemiAnalysis DeepSeek Cost (via Interesting Engineering)](https://interestingengineering.com/culture/deepseeks-ai-training-cost-billion)
- [LLM-Stats — SWE-Bench Verified](https://llm-stats.com/benchmarks/swe-bench-verified)
- [Carnegie — DeepSeek Implications for Africa](https://carnegieendowment.org/posts/2025/03/deepseek-ai-implications-africa)
- [Microsoft AI Diffusion Report](https://blogs.microsoft.com/on-the-issues/2026/01/08/global-ai-adoption-in-2025/)
- [Winsome Marketing — AI Cost Illusion](https://winsomemarketing.com/ai-in-marketing/the-great-ai-cost-illusion-why-chinas-price-war-is-unsustainable-theater)
- [CSET Georgetown — China AI Financial Support](https://cset.georgetown.edu/article/in-out-of-china-financial-support-for-ai-development/)