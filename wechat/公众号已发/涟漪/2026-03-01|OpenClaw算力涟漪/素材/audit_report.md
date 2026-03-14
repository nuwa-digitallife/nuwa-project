Both checks complete. Here's the full audit report:

---

# 审计报告：OpenClaw算力涟漪

## 关键实体清单

**公司/机构 (50+):** OpenClaw, Inferact, Ollama, vLLM, Red Hat, NVIDIA, Cadence, Broadcom, Marvell, Google, OpenAI, Meta, Microsoft, Amazon, Oracle, Anthropic, Axelera AI, EdgeCortix, Mirai, Celestial AI, Iceotope, Supermicro, ASUS, Constellation Energy, Kairos Power, Energy Northwest, TerraPower, Oklo, Helion Energy, Baidu, Rockchip, Sugon, HappyCapy, NanoClaw, KiloClaw, Dify, Tidy, IronClaw, EasyClaw, MaxClaw, Kimi Claw, 扣子, 百度千帆, CoPaw, LobsterAI

**产品/技术 (20+):** vLLM, TensorRT-LLM, SGLang, KTransformers, EAGLE-3, FlashAttention 4, Titan ASIC, TPU v7, Kunlun M100, RK182X, ChipStack AI, BitNet b1.58, 玲龙一号, CBAM, Xe-100

**人物:** Richard Ho, Simon Mo, Sam Altman, Dylan Patel

---

## 覆盖检查结果

### ✅ 已覆盖（充分）
- 推理框架生态（vLLM/SGLang/TensorRT-LLM/KTransformers/Ollama/EAGLE-3）
- 液冷技术与 ROI（PUE 数据、厂商、渗透率）
- 核能 SMR 供应链（玲龙一号、Constellation、Kairos、TerraPower、Oklo）
- Anthropic 定价套利经济学
- 芯片战略（OpenAI Titan、Google TPU、Broadcom ASIC）
- 边缘推理创业（Axelera、EdgeCortix、Mirai）
- 中国推理芯片（Kunlun M100、RK182X）
- OpenClaw 竞品生态（40+竞争者）
- EU CBAM 间接冲击
- 能耗反方观点（MIT、BitNet）

### ⚠️ 需要补充

| 优先级 | 缺失实体/主题 | 理由 |
|--------|--------------|------|
| **高** | **AMD MI350/MI355X** | NVIDIA 推理硬件最大竞争者，性能 4x MI300X。芯片竞争叙事缺 AMD 不完整 |
| **高** | **Marvell Technology** | 第二大定制 ASIC 设计商（20-25%份额），服务 OpenAI/Meta/Google。已提 Broadcom 但漏 Marvell |
| **高** | **OpenHands / Cline / Aider** | 开源编程 Agent 头部项目（OpenHands 65K+ stars）。提了40+竞品但缺头部具名 |
| **中** | **X-energy (Xe-100)** | AWS 的 SMR 核心合作方（$500M 投资），核能阵营漏了这个 |
| **中** | **NVIDIA Rubin** | Blackwell 之后的下一代平台（H2 2026），前瞻性缺失 |
| **中** | **CoreWeave** | GPU 云基础设施独角兽，2026 预计 $10B+ 收入，代表 IaaS 层 |
| **中** | **MoE 架构作为推理降本机制** | 3-5x 成本降低，与 BitNet/量化等并列的重要推理优化手段 |
| **低** | **HBM4 内存** | 下一代芯片的内存瓶颈/使能技术 |
| **低** | **ASIC 份额从 15%→40%** | 量化 GPU→ASIC 转移趋势的关键统计 |
| **低** | **MCP (Model Context Protocol)** | Agent 生态标准化协议趋势 |

---

## 时效性检查结果

### ✅ 最新（已确认）
- **OpenAI Titan ASIC** — 2026年底部署，TSMC N3，Broadcom 合作，均已确认
- **Google TPU 产能 3.1-3.2M** — 仍准确，另 Anthropic 租购 1M+ TPU 已公开
- **Axelera AI $250M** — 准确（总融资超 $450M，BlackRock 新加入）
- **Claude API Opus $5/$25** — 仍准确（Opus 4.6 同价位，另有 fast mode $30/$150）
- **HappyCapy** — 准确，2026/2/11 Product Hunt 上线
- **Baidu Kunlun M100** — 准确，2026年初商用，昆仑芯片部门已独立（估值 210 亿元）
- **Meta 租用 Google TPU** — 已确认，multi-billion deal，2026 租用 → 2027 直购
- **Ollama $3.2M 收入** — 准确但注意这是 **2024 年数据**

### ⚠️ 需要更新

| 实体 | 旧值 | 新值 | 来源 |
|------|------|------|------|
| **Inferact 融资轮次** | "Series A" | **Seed 轮**（$150M 金额和 $800M 估值正确，但轮次标注错误） | [Bloomberg](https://www.bloomberg.com/news/articles/2026-01-22/andreessen-backed-inferact-raises-150-million-in-seed-round) |
| **Celestial AI** | 独立公司，"2026目标$200M融资" | **已被 Marvell 以 $32.5 亿收购**（2026/2/2 完成，$1B 现金 + 27.2M 股票） | [SDxCentral](https://www.sdxcentral.com/news/marvell-completes-325b-acquisition-of-photonic-startup-celestial-ai/) |
| **Stargate 项目规模** | "$1.4 万亿" | **~$6000 亿**（2030年前）。Abilene 2.0GW 扩建 2026/3 谈判破裂，执行遇阻 | [Invezz](https://invezz.com/news/2026/03/09/who-wins-as-oracle-openais-500b-stargate-project-stalls/) |
| **Broadcom ASIC 市场份额** | "超 80%" | **70-80%**（共识约 70%），Counterpoint 预计 2027 降至 ~60% | [Yahoo Finance](https://finance.yahoo.com/news/broadcom-set-dominate-custom-ai-163116560.html) |
| **EU CBAM 证书销售** | "2027/2 开始购买证书" | 证书销售 **从 2026/1/1 推迟至 2027/2/1**，新增 50 吨 de minimis 门槛 | [EU Taxation](https://taxation-customs.ec.europa.eu/news/cbam-successfully-entered-force-1-january-2026-2026-01-14_en) |
| **玲龙一号并网时间** | "2026上半年" | 公开来源仅确认 **"2026年并网"**，未明确上/下半年 | [中国能源报](http://paper.people.com.cn/zgnyb/pc/content/202501/06/content_30051222.html) |

---

## 审计结论

**FAIL**

**关键问题（必修）：**
1. **Celestial AI 已被收购** — 素材中仍作为独立创业公司提及，事实已过时
2. **Stargate $1.4万亿 → ~$6000亿** — 缩水 57%，且扩建谈判破裂，叙事需大幅调整
3. **Inferact "Series A" → Seed 轮** — 事实性错误
4. **AMD 完全缺失** — 芯片竞争格局少了最大 NVIDIA 对手
5. **Marvell 缺失** — ASIC 双寡头只提了一半

**次要问题：** Broadcom 份额微调、玲龙一号时间精度、CBAM 时间线细节、OpenClaw 头部竞品具名不足。