# World Labs / 李飞飞 结构化素材

> 调研时间：2026-03-10
> 数据截止：2026-02-18（最新融资公告）

---

## 1. World Labs 基本信息

| 字段 | 内容 | 信源 | 可信度 |
|------|------|------|--------|
| 成立时间 | 2024年1月（一说4月）；2024年9月13日走出隐身模式 | [Crunchbase](https://news.crunchbase.com/ai/world-labs-launches-a16z-nventures/)、[TechCrunch](https://techcrunch.com/2024/09/13/fei-fei-lis-world-labs-comes-out-of-stealth-with-230m-in-funding/) | ★★★★★ |
| 总部 | 旧金山 San Francisco | [Bloomberg](https://www.bloomberg.com/news/articles/2026-02-18/ai-pioneer-fei-fei-li-s-startup-world-labs-raises-1-billion) | ★★★★★ |
| 定位 | 前沿AI研究+产品公司，专注spatial intelligence（空间智能） | [官网 About](https://www.worldlabs.ai/about) | ★★★★★ |
| 使命 | 构建能感知、生成、推理并与3D世界交互的基础世界模型 | [官网](https://www.worldlabs.ai/about) | ★★★★★ |

### 核心团队

| 姓名 | 角色 | 背景 | 信源 |
|------|------|------|------|
| **李飞飞 Fei-Fei Li** | 联合创始人 & CEO | 斯坦福大学AI教授，ImageNet创建者，"AI教母" | [官网](https://www.worldlabs.ai/about)、[a16z](https://a16z.com/announcement/investing-in-world-labs/) |
| **Justin Johnson** | 联合创始人 | 李飞飞实验室博士，密歇根大学教授，风格迁移（style transfer）先驱 | [a16z](https://a16z.com/announcement/investing-in-world-labs/) |
| **Ben Mildenhall** | 联合创始人 | NeRF（Neural Radiance Fields）发明人，开创了3D重建子领域 | [a16z](https://a16z.com/announcement/investing-in-world-labs/) |
| **Christoph Lassner** | 联合创始人 | Pulsar（球形可微渲染器）开发者，为Gaussian Splatting奠基；曾任Meta Reality Labs、Epic Games | [a16z](https://a16z.com/announcement/investing-in-world-labs/) |

**可信度**：★★★★★（官网 + a16z 投资公告一手源）

---

## 2. 融资历程

| 轮次 | 时间 | 金额 | 估值 | 领投方 | 其他投资方 | 信源 |
|------|------|------|------|--------|-----------|------|
| Seed | 2024年春 | ~$130M | ~$2亿 | a16z | Radical Ventures | [Crunchbase](https://news.crunchbase.com/ai/world-labs-launches-a16z-nventures/) |
| Series A | 2024年6-7月 | $100M | >$10亿 | NEA | a16z, Radical Ventures | [TechCrunch](https://techcrunch.com/2024/08/14/nea-led-a-100m-round-into-fei-fei-lis-new-ai-startup-now-valued-at-over-1b/) |
| （出隐身时累计） | 2024年9月 | 总计$230M | ~$10亿 | a16z + NEA + Radical | NVentures (Nvidia), Sanabil (沙特), Temasek (新加坡) | [TechCrunch](https://techcrunch.com/2024/09/13/fei-fei-lis-world-labs-comes-out-of-stealth-with-230m-in-funding/) |
| **B轮** | **2026年2月18日** | **$10亿** | **~$50亿** | **a16z** | **AMD, Autodesk ($2亿), Emerson Collective, Fidelity, NVIDIA, Sea** | [官方公告](https://www.worldlabs.ai/blog/funding-2026)、[TechCrunch](https://techcrunch.com/2026/02/18/world-labs-lands-200m-from-autodesk-to-bring-world-models-into-3d-workflows/)、[Bloomberg](https://www.bloomberg.com/news/articles/2026-02-18/ai-pioneer-fei-fei-li-s-startup-world-labs-raises-1-billion) |

### 知名天使投资人（2024年轮次）

Jeff Dean (Google DeepMind首席科学家)、Geoffrey Hinton (图灵奖)、Marc Benioff (Salesforce CEO)、Reid Hoffman (LinkedIn创始人)、Eric Schmidt (前Google CEO)、Ashton Kutcher

**可信度**：★★★★★（TechCrunch + Bloomberg + 官方公告交叉验证）

---

## 3. 产品 Marble

### 基本信息

| 字段 | 内容 | 信源 |
|------|------|------|
| 发布时间 | 2025年11月12日 | [TechCrunch](https://techcrunch.com/2025/11/12/fei-fei-lis-world-labs-speeds-up-the-world-model-race-with-marble-its-first-commercial-product/) |
| 产品网址 | [marble.worldlabs.ai](https://marble.worldlabs.ai/) | 官网 |
| World API 发布 | 2026年1月21日（公开API） | [官方博客](https://www.worldlabs.ai/blog/funding-2026) |
| 定位 | 首个商用世界模型产品——生成式多模态世界模型 | [官方博客](https://www.worldlabs.ai/blog/marble-world-model) |

### 核心能力

1. **多模态输入**：文本提示词、单张/多张图片、视频、全景图、粗略3D布局（Chisel工具）
2. **3D世界生成**：从输入生成空间连贯、高保真、持久化的3D世界
3. **世界编辑**：AI原生工具支持局部编辑（物体移除/修饰）和结构性修改（物体替换/风格变换）
4. **Chisel 3D雕刻**：将结构与风格解耦——粗略3D布局定义构图，文字提示词控制美学
5. **世界扩展与合成**：单步扩展放大世界、合成模式将多个世界拼接成大型可穿越空间
6. **视频增强**：保持像素级精确镜头控制，同时添加细节和动态元素

### 输出格式

- Gaussian Splats（高斯溅射，最高保真度）
- Triangle Meshes（三角网格，用于物理碰撞/视觉保真）
- 视频渲染（像素级精确镜头控制）
- **可导出至 Unreal Engine 和 Unity**

### 定价（信源：[Marble 定价页](https://marble.worldlabs.ai/pricing)）

| 层级 | 月价 | 生成次数 | 关键特性 |
|------|------|----------|---------|
| Free | $0 | 4次 | 文本/图片/全景输入 |
| Standard | $20 | 12次 | 多图/视频输入 + 高级编辑 |
| Pro | $35 | 25次 | 场景扩展 + **商用授权** |
| Max | $95 | 75次 | 全部功能 |

### 技术路线：Spatial Intelligence（空间智能）

Marble 的技术路线核心是"空间智能"——不是生成2D视频，而是**生成可穿越的持久化3D世界**。

与竞品的关键区别：**离散生成 + 持久化下载**（不是实时流式生成）。

**可信度**：★★★★★（官方博客+产品页一手源）

---

## 4. 世界模型路线对比

| 维度 | World Labs Marble | LeCun JEPA (AMI Labs) | OpenAI Sora 2 | NVIDIA Cosmos | DeepMind Genie 3 |
|------|-------------------|----------------------|----------------|---------------|-------------------|
| **技术路线** | 多模态→持久化3D世界生成 | 联合嵌入预测架构，学习抽象表征，不需标签 | 视频生成+学习物理约束 | 生成式世界基础模型，9000万亿token训练 | 自回归逐帧生成，保持一致性 |
| **核心目标** | 空间智能：感知/生成/推理/交互3D世界 | 通用世界模型→规划→因果推理→AGI | 物理一致的视频世界模拟 | 机器人/自动驾驶的合成训练数据 | 实时交互通用世界模型 |
| **输出** | 可下载3D环境（Gaussian Splat/Mesh） | 抽象表征用于规划（无直接产品） | 视频 | 合成训练数据 | 实时交互24fps 3D世界 |
| **商用状态** | ✅ 已商用（2025.11） | ❌ 筹备中（€5亿融资，€30亿估值） | 部分（Sora 2 Pro） | ✅ 已商用（200万+下载） | ❌ 研究预览 |
| **应用场景** | 创意/游戏/影视/建筑 | 通用AGI/机器人规划 | 视频创作/模拟 | 机器人/自动驾驶/物理AI | 交互式环境/游戏 |
| **关键优势** | 首个商用产品；可导出行业工具；VR支持 | 理论基础最深（LeCun图灵奖）；解决LLM幻觉 | OpenAI生态整合；物理合规性 | 工业级规模；已有Figure AI/Uber等客户 | 实时24fps；自学物理 |
| **关键劣势** | 离散生成非实时；初期限于创意领域 | 零产品零验证；执行风险大 | 主要是研究工具，非显式世界模型 | 紧耦合机器人/自动驾驶场景 | 仅研究预览；一致性几分钟后崩坏 |
| **资金** | $12.3亿（累计） | €5亿（融资中） | （OpenAI整体） | （NVIDIA整体） | （Google整体） |
| **掌门** | 李飞飞 | Yann LeCun | OpenAI | NVIDIA | Google DeepMind |

**信源**：[Themesis对比文](https://themesis.com/2026/01/07/world-models-five-competing-approaches/)、[Introl博客](https://introl.com/blog/world-models-race-agi-2026)、[TechCrunch](https://techcrunch.com/2025/11/12/fei-fei-lis-world-labs-speeds-up-the-world-model-race-with-marble-its-first-commercial-product/)

**可信度**：★★★★（行业分析 + 一手产品信息交叉验证）

### 路线本质区别总结

1. **Marble vs Sora**：Marble生成**可下载的持久化3D世界**，Sora生成**2D视频**。Marble面向3D创作者工作流（导出到Unreal/Unity），Sora面向视频内容创作。
2. **Marble vs JEPA**：Marble是工程产品路线（从产品出发，research↔product紧耦合），JEPA是理论研究路线（从抽象表征出发，目标是通用规划/AGI）。Marble已有商用产品，JEPA零产品。
3. **Marble vs Cosmos**：Marble面向创意/设计工作者，Cosmos面向机器人/自动驾驶的**合成训练数据**。Cosmos是基础设施层，Marble是应用层。
4. **Marble vs Genie 3**：Marble是离散生成+下载，Genie是**实时交互**（24fps）。Genie更接近"可玩的世界"，Marble更接近"可编辑的场景"。

---

## 5. 李飞飞公开言论：核心观点

### 定义：什么是空间智能

> "Spatial Intelligence is the scaffolding upon which our cognition is built."
> （空间智能是我们认知构建的脚手架。）

> "I'm not a philosopher, but I know well that, at least for AI, the world is far more than just words. Spatial intelligence represents the frontier beyond language — it is an ability that integrates imagination, perception, and action."
> （至少对AI来说，世界远不止文字。空间智能代表语言之外的前沿——它是整合想象、感知和行动的能力。）

**信源**：[Substack 万字长文](https://drfeifei.substack.com/p/from-words-to-worlds-spatial-intelligence)、[TIME](https://time.com/7339693/fei-fei-li-ai/) | 可信度：★★★★★

### 批评当前LLM

> "Yet they remain wordsmiths in the dark — eloquent but inexperienced, knowledgeable but ungrounded."
> （它们仍然是黑暗中的文字匠——能言善辩但缺乏经验，知识渊博但缺乏根基。）

**信源**：[TIME](https://time.com/7339693/fei-fei-li-ai/) | 可信度：★★★★★

### 为什么空间智能是下一个前沿

> "Sight turned into insight; Seeing became understanding; Understanding led to action. All these gave rise to intelligence."
> （视觉变成洞察；看见变成理解；理解导致行动。这一切催生了智能。）

> "The next decade of AI will be about building machines with spatial intelligence."
> （AI的下一个十年将是关于构建具有空间智能的机器。）

**信源**：[TED Talk 2024](https://www.ted.com/talks/fei_fei_li_with_spatial_intelligence_ai_will_understand_the_real_world)、[Substack](https://drfeifei.substack.com/p/from-words-to-worlds-spatial-intelligence) | 可信度：★★★★★

### 世界模型的三要素

李飞飞定义空间智能世界模型必须具备三个特性：
1. **Generative（生成式）**：创造具有感知、几何和物理一致性的世界
2. **Multimodal（多模态）**：处理多样输入（图像、视频、文本、手势、动作）
3. **Interactive（交互式）**：根据输入动作输出下一个世界状态

**信源**：[Substack](https://drfeifei.substack.com/p/from-words-to-worlds-spatial-intelligence) | 可信度：★★★★★

### AGI与空间智能

> "AGI will not be complete without spatial intelligence."
> （没有空间智能，AGI就不完整。）

**信源**：[Substack](https://drfeifei.substack.com/p/from-words-to-worlds-spatial-intelligence) | 可信度：★★★★★

### 人文立场

> "AI must augment human capability, not replace it."
> （AI必须增强人类能力，而不是取代它。）

> "For the first time in history, we're poised to build machines that we can rely on as true partners in greatest challenges."

**信源**：[TIME](https://time.com/7339693/fei-fei-li-ai/) | 可信度：★★★★★

### 应用愿景三大方向

1. **创意**：电影人/建筑师无需传统设计流程即可创建可探索的3D世界
2. **机器人**：空间感知机器作为实验室/家庭/医院的协作伙伴（不限于人形）
3. **科学**：药物发现、分子建模、医疗诊断、沉浸式教育

---

## 6. 一手源 URL 汇总

### 官方一手源（可信度 ★★★★★）

| 来源 | URL | 内容 |
|------|-----|------|
| World Labs 官网 | https://www.worldlabs.ai/about | 公司介绍、团队 |
| Marble 产品页 | https://marble.worldlabs.ai/ | 产品体验入口 |
| Marble 技术博客 | https://www.worldlabs.ai/blog/marble-world-model | 产品技术细节 |
| 2026融资公告 | https://www.worldlabs.ai/blog/funding-2026 | B轮$10亿融资 + World API |
| 李飞飞 Substack 万字长文 | https://drfeifei.substack.com/p/from-words-to-worlds-spatial-intelligence | 空间智能完整论述 |
| 李飞飞 TED Talk 2024 | https://www.ted.com/talks/fei_fei_li_with_spatial_intelligence_ai_will_understand_the_real_world | 空间智能核心演讲 |
| Marble 定价页 | https://marble.worldlabs.ai/pricing | 订阅层级 |

### 权威媒体（可信度 ★★★★☆~★★★★★）

| 来源 | URL | 内容 |
|------|-----|------|
| TechCrunch - Marble发布 | https://techcrunch.com/2025/11/12/fei-fei-lis-world-labs-speeds-up-the-world-model-race-with-marble-its-first-commercial-product/ | 首款商用产品发布 |
| TechCrunch - B轮融资 | https://techcrunch.com/2026/02/18/world-labs-lands-200m-from-autodesk-to-bring-world-models-into-3d-workflows/ | $10亿融资+Autodesk合作 |
| TechCrunch - NEA领投 | https://techcrunch.com/2024/08/14/nea-led-a-100m-round-into-fei-fei-lis-new-ai-startup-now-valued-at-over-1b/ | 早期$100M融资 |
| Bloomberg - B轮 | https://www.bloomberg.com/news/articles/2026-02-18/ai-pioneer-fei-fei-li-s-startup-world-labs-raises-1-billion | $10亿融资确认 |
| Bloomberg - $50亿估值谈判 | https://www.bloomberg.com/news/articles/2026-01-23/fei-fei-li-s-ai-startup-world-labs-in-funding-talks-at-5-billion-valuation | 估值$50亿 |
| TIME - 空间智能 | https://time.com/7339693/fei-fei-li-ai/ | 李飞飞署名文章 |
| a16z 投资公告 | https://a16z.com/announcement/investing-in-world-labs/ | 团队背景详细介绍 |
| Crunchbase | https://news.crunchbase.com/ai/world-labs-launches-a16z-nventures/ | 出隐身模式报道 |

### 行业分析（可信度 ★★★★☆）

| 来源 | URL | 内容 |
|------|-----|------|
| Themesis - 五大路线对比 | https://themesis.com/2026/01/07/world-models-five-competing-approaches/ | Marble vs JEPA vs Sora vs Cosmos vs Genie |
| Introl - 世界模型竞赛 | https://introl.com/blog/world-models-race-agi-2026 | 2026世界模型全景 |
| Contrary Research | https://research.contrary.com/company/world-labs | 公司深度分析 |

### 学术（可信度 ★★★★★）

| 来源 | URL | 内容 |
|------|-----|------|
| arXiv - Thinking in Space | https://arxiv.org/abs/2412.14171 | VSI-Bench 空间智能基准测试论文（李飞飞合著） |
