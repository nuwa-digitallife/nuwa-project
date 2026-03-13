## 证据硬度审计

### 逐段评估

| 段落位置 | 核心断言 | 硬度 | 问题 | 优先级 |
|----------|----------|------|------|--------|
| L3-5 | 上一篇涟漪引用 + 叙事开场 | 纯修辞 | — | — |
| L7-8 | 2026年1月Anthropic封号，Claude Max $200/月 | 强 | Anthropic官方+The Register报道，时间线精确到1月9日 | — |
| L9 | OpenClaw 72h 6万星，**截至3月初突破25万星** | **弱** | 素材仅有TechCrunch 2月数据14.5万星，25万无来源 | **P1** |
| L9 | Steinberger 2月15日加入OpenAI，项目移交基金会 | 强 | TechCrunch确认 | — |
| L11-13 | $200订阅消耗数千美元算力 | 中 | 基于API定价推算（Opus $5/$25 vs Max $200），非Anthropic官方披露亏损数字 | P2 |
| L19-23 | Agent团队模式token消耗是普通对话的7倍 | 强 | 归因"Anthropic开发者文档"，素材确认来源SDK文档 | — |
| L25 | 扩展思维算力是普通推理的100倍以上 | 强 | Deloitte 2026 TMT Predictions明确给出 | — |
| L27 | 粗估700-70,000x | 纯修辞 | 明确标注"粗估""简化推算""即便打折扣"，读者知道这是推算 | — |
| L31 | IDC预测2027年Agent 10x，token 1000x | 强 | IDC FutureScape 2026一手源 | — |
| L35-37 | 推理占比 1/3→1/2→2/3→3/4 | 强 | Deloitte+Brookfield数据交叉确认 | — |
| L39 | 训练一次性 vs 推理持续 | 纯修辞 | 行业常识性判断 | — |
| L43 | NVIDIA 90%+市场、360万积压、$570亿季报 | 强 | NVIDIA FY2026 Q3官方财报 | — |
| L45 | 训练vs推理对芯片要求不同 | 纯修辞 | 技术常识性判断 | — |
| L47 | NVIDIA推理份额2028年降至20-30% | 中 | "多位行业分析师预测"——归因模糊，VentureBeat/SDxCentral有引述但非单一权威源 | P2 |
| L55 | Broadcom 70-80%份额，Marvell 20-25% | 强 | 审计报告已修正（原80%→70-80%），Counterpoint/Yahoo Finance交叉确认 | — |
| L55 | Google TPU占Broadcom ASIC收入78%，Q4 $65亿+74% | 强 | SemiAnalysis + CNBC Broadcom财报 | — |
| L57 | Marvell以$32.5亿收购Celestial AI | 强 | SDxCentral确认2026/2/2完成 | — |
| L59 | OpenAI Titan：3nm、40人、Mizuho估$1500-2000亿 | 强 | TrendForce + SemiAnalysis + Mizuho分析 | — |
| L61 | Google TPU 310-320万片，成本NVIDIA 1/5 | 强 | SemiAnalysis/Investing.com确认（从400万下调） | — |
| L61 | Meta租用Google TPU | 强 | 知乎/多来源确认，multi-billion deal | — |
| L63 | AMD MI350性能4倍上一代 | 中 | AMD营销宣称，非独立基准测试 | P2 |
| L63 | NVIDIA约$200亿收购Groq | 中 | VentureBeat报道（"押注"表述），交易细节可能随时间变化 | — |
| L65 | Blockquote：造铲子的公司 | 纯修辞 | — | — |
| L67 | Cadence ChipStack AI 10x效率，客户含NVIDIA/Qualcomm | 强 | Cadence官方新闻稿2026年2月 | — |
| L71 | Blackwell 100kW/机柜，风冷极限41kW | 强 | 多来源交叉确认（enkiai/行业标准） | — |
| L73 | 液冷PUE 1.1-1.2，年省电40%，1.5年回本 | 中 | 行业报告/分析数据，非单一权威源但多来源一致 | — |
| L75 | 液冷市场$28亿→$210亿，中国14%→47% | 强 | 集邦咨询+行业报告 | — |
| L75 | 中科曙光750kW/柜PUE 1.03 | 强 | 曙光产品规格 | — |
| L81 | IEA数据中心1000TWh，Goldman 160% | 强 | IEA Energy and AI报告 + Goldman Sachs研究 | — |
| L81 | PJM**电力容量定价飙升超过10倍** | **弱** | 素材仅说"容量定价飙升"和"部分地区电价上升20%+"，**"超过10倍"无直接来源** | **P1** |
| L83 | 核能购电协议：Microsoft 837MW、Google 500MW、Amazon 960MW、Meta 4GW | 强 | CNBC/Fortune/各公司公告 | — |
| L83 | Altman："AI瓶颈是电力" | 强 | DataCenterDynamics引述 | — |
| L85 | 美国SMR最早2028 | 纯修辞 | 从已列项目中的逻辑推断 | — |
| L87 | 玲龙一号2025里程碑+2026并网 | 强 | 中国能源报/每日经济新闻（审计报告注：仅确认"2026年"，未明确上/下半年） | — |
| L87 | "比美国最快项目早至少两年" | 强 | 2026 vs Constellation 2028 = 2年，逻辑无误 | — |
| L89 | 130种SMR技术路线 | 强 | NEA（核能机构）统计 | — |
| L91 | Blockquote：标准化 | 纯修辞 | — | — |
| L99 | Inferact $1.5亿种子轮，$8亿估值，a16z | 强 | SiliconAngle/Bloomberg确认（审计报告已纠正"Series A"→"Seed"，文章用词正确） | — |
| L101 | vLLM吞吐Ollama 16.6倍 | 强 | NVIDIA TensorRT-LLM官方文档（8033 vs 484 tokens/s） | — |
| L101 | 新加坡fintech省$6000/月（5→3张H100） | 中 | Red Hat技术报告案例 | — |
| L101 | SGLang 2-5倍 | 中 | 技术评测报告 | — |
| L101 | EAGLE-3 H200 3.6倍 | 强 | OpenReview论文 | — |
| L103 | "中文媒体和行业分析师最少系统讨论的环节" | 纯修辞 | 主观判断 | — |
| L105 | MIT Tech Review报道SMR 2030前无法规模化 | 强 | MIT Technology Review（国家杂志奖提名报道） | — |
| L105 | BitNet b1.58 能耗降12倍 | 强 | Nature Scientific Reports论文 | — |
| L105 | 联合优化50%+能耗降低 | 中 | Nature论文推算 | — |
| L109 | Blockquote：软件是最快减压阀 | 纯修辞 | — | — |
| L113 | Claude Code ARR $25亿，翻倍 | 强 | Anthropic Series G官方公告（注：融资场景自报数据） | — |
| L113 | GitHub 4% commits来自Claude Code | 中 | SemiAnalysis分析（可重现的GitHub抓取，非官方统计） | — |
| L113 | SemiAnalysis预测年底20%+ | 中 | 分析师外推预测 | — |
| L115-119 | 结论段 | 纯修辞 | — | — |

### 统计

- **强**: 22段
- **中**: 10段
- **弱**: 2段
- **纯修辞**: 13段
- **证据硬度评分: 8/10**（仅2个弱点，但其中1个是核心叙事数字）

### 叙事连贯性检测

| 位置 | 问题类型 | 描述 | 优先级 |
|------|----------|------|--------|
| L67 Cadence段 | 轻微突兀引入 | 从AMD/NVIDIA/Groq三方竞争直接跳到EDA工具层，过渡句"还有一个容易被忽视的环节"虽有缓冲但逻辑层级跳跃较大（从芯片产品竞争→芯片设计工具） | P2 |
| L81 PJM | 信源断裂 | "电力容量定价飙升超过10倍"是全段最具冲击力的数字，但在IEA和Goldman Sachs的权威数据中间插入了一个无来源的断言，削弱了该段整体可信度 | P1 |
| 无其他逻辑断裂 | — | 整体叙事从"封号→Agent→芯片→散热→电力→软件→回到起点"的涟漪结构清晰，段间过渡句承担论证功能，无悬空引用 | — |

### 优先加强清单（按优先级排序）

1. **P1: L9 OpenClaw "截至3月初已突破25万颗星"**
   - 当前写法: "截至3月初已突破25万颗星，成为GitHub增长最快的开源项目"
   - 问题: 素材最后记录为14.5万（2月中旬TechCrunch数据），25万无来源。如果实际未达25万，这是文章开头第二段的事实性错误，影响读者对全文的信任
   - 需要的证据类型: GitHub仓库实时数据 / 3月媒体报道
   - 搜索建议: `"OpenClaw" OR "open-claw" github stars 2026 march`、直接检查GitHub页面

2. **P1: L81 PJM"电力容量定价飙升超过10倍"**
   - 当前写法: "电力容量定价飙升超过10倍，电费面临持续上涨压力"
   - 问题: 素材中PJM段仅提到"容量定价飙升"和"电价上升20%+"，"超过10倍"无直接来源。注：PJM 2024年BRA拍卖确实出现过约10倍跳涨（$28→$269/MW-day），但文章未标注具体是哪次拍卖，也未在参考素材中
   - 需要的证据类型: PJM BRA拍卖公开数据 / 能源行业报道
   - 搜索建议: `PJM capacity auction price 2024 2025 "tenfold" OR "10x" OR "$269"` 或 `PJM BRA results 2025/2026 delivery year`

3. **P2: L11-13 "$200→数千美元"核心叙事前提**
   - 当前写法: "实际消耗的计算资源折算成API价格，高达数千美元"
   - 问题: 这是全文叙事的起点。虽然从API定价可以推算出来（Opus $5/$25/Mtok × heavy Agent usage），但文章说"工程师们发现"，暗示有内部数据，实际是外部分析推断
   - 改进建议: 不需要改数字，但可明确"按API公开价格折算"而非暗示内部发现
   - 搜索建议: `Anthropic Claude Max API cost subsidy "thousands" agent usage`

4. **P2: L47 NVIDIA推理份额降至20-30%**
   - 当前写法: "多位行业分析师的预测：到2028年，NVIDIA在推理市场的份额将从90%以上降到20-30%"
   - 问题: "多位分析师"过于模糊。VentureBeat引述了具名分析师，可以加至少一个名字提升硬度
   - 搜索建议: `NVIDIA inference market share 2028 prediction analyst name`

5. **P2: L63 AMD MI350"号称性能是上一代的4倍"**
   - 当前写法: 直接引用性能数据
   - 问题: "号称"一词已适当降低了硬度，但4x是AMD自家宣称（vs MI300X），无独立基准验证。当前处理可接受
   - 搜索建议: `AMD MI350 MI355X benchmark independent review 2026`

### 收敛判断

→ **VERDICT: NEEDS_IMPROVEMENT**（P1 × 2）

**修复建议优先级**：
1. OpenClaw 25万星——核实后调整数字（可能降回14.5万+并标注时间，或找到3月新数据）
2. PJM 10倍——补上PJM BRA拍卖的具体来源，或改为"容量定价飙升数倍"等有据可依的表述

两个P1均为具体数字的来源缺失问题，不影响文章的叙事结构和核心论证逻辑。修复成本低，修复后可达 **ALL_STRONG**。