# 播客 & YouTube 监控方案

> 2026-02-27 · AI 信息源头追踪
> 目标：比所有中文 AI 媒体快 1-7 天看到同一信息

---

## 一、核心发现：谁在控制 AI 话语权

**关键事实**：中文 AI 媒体（51CTO、InfoQ、AI前线）的"人物观点"文章，90% 来自以下 5 个播客主持人的节目。你直接听源头，信息密度更高，而且早 3-7 天。

### 播客主持人影响力排名

| # | 主持人 | 播客 | 为什么重要 | 获取大佬能力 |
|---|--------|------|-----------|------------|
| 1 | **Dwarkesh Patel** | Dwarkesh Podcast | 当前 AI 圈最炙手可热的访谈者。2-3 小时深度研究型访谈 | Dario×2, Ilya, Shane Legg, Karpathy, Satya, Musk |
| 2 | **Lex Fridman** | Lex Fridman Podcast | 3-5 小时旗舰访谈，数千万播放量 | Demis Hassabis, Yann LeCun, Dario |
| 3 | **Sarah Guo + Elad Gil** | No Priors | 投资人+研究者双视角，每周四固定更新 | Jensen Huang, 李飞飞, OpenAI 工程师 |
| 4 | **Kevin Roose + Casey Newton** | Hard Fork (NYT) | 主流影响力最大，AI+政策+社会 | Dario, Amanda Askell |
| 5 | **Alex Kantrowitz** | Big Technology | CEO 级战略访谈 | Sam Altman, Demis Hassabis, Dario |
| 6 | **swyx + Alessio** | Latent Space | 工程层（推理/Agent/GPU infra） | Greg Brockman, Karpathy, Jeff Dean |
| 7 | **Nathan Labenz** | Cognitive Revolution | 技术 builder 视角 | OpenAI 医疗AI, MiniMax RL 团队 |
| 8 | **Hannah Fry** | DeepMind Podcast | DeepMind 官方叙事渠道 | Demis, Shane Legg |

---

## 二、必监控清单（按优先级）

### Tier 1 — 每期必听（信息密度最高）

| 播客 | 频率 | RSS | 有转录 | 重点 |
|------|------|-----|--------|------|
| **Dwarkesh Podcast** | 周更 | `https://api.substack.com/feed/podcast/69345.rss` | ✅ 官方 | AI CEO 深度访谈，2026.2 Dario 最新访谈在此首发 |
| **Lex Fridman** | 月 1-2 期 | `https://lexfridman.com/feed/podcast/` | ✅ 官方 | 3h+ 旗舰访谈，Demis #475 等 |
| **No Priors** | 每周四 | `https://feeds.megaphone.fm/nopriors` | ❌ | 投资人看 AI，Jensen/李飞飞等 |
| **Latent Space** | 周更 | `https://rss.flightcast.com/vgnxzgiwwzwke85ym53fjnzu.xml` | ✅ 详细 | 工程层：Agent/推理/infra，17.1万订阅 |

### Tier 2 — 选择性听（按嘉宾决定）

| 播客 | 频率 | RSS | 有转录 | 重点 |
|------|------|-----|--------|------|
| **Hard Fork (NYT)** | 每周五 | `https://feeds.simplecast.com/l2i9YnTd` | NYT 付费 | 主流视角+政策，Amanda Askell 等 |
| **Big Technology** | 周更 | bigtechnology.com (Megaphone) | 部分 | CEO 战略访谈 |
| **Cognitive Revolution** | 周更 | `https://feeds.megaphone.fm/RINTP3108857801` | ✅ | 技术 builder |
| **TWIML AI** | 4 天/期 | `https://feeds.megaphone.fm/MLN2155636147` | ✅ | ML 学术前沿 |
| **80,000 Hours** | 不定 | 80000hours.org/podcast | ✅ | Chris Olah/Amanda Askell 深度访谈 |

### Tier 3 — 补充信源

| 播客 | 频率 | RSS | 重点 |
|------|------|-----|------|
| **BG2Pod** (Brad Gerstner + Bill Gurley) | 双周 | bg2pod.com | 投资人看 AI infra |
| **All-In** | 周更 | `https://allinchamathjason.libsyn.com/rss` | VC 宏观 + AI 经济影响 |
| **20VC** (Harry Stebbings) | 周 3-4 期 | thetwentyminutevc.libsyn.com | VC/创业融资角度 |
| **Possible** (Reid Hoffman) | 周更 | possible.fm | AI + 跨领域（医疗/教育） |
| **MLST** (Machine Learning Street Talk) | 双周 | Apple/Podbean | 纯学术深度 |
| **Eye On AI** | 双周 | `https://rss.com/podcasts/eyeonai/` | 记者视角的 AI 追踪 |

---

## 三、公司官方 YouTube 频道

### 必关注

| 公司 | 频道 | 订阅量 | 内容类型 | 重点关注 |
|------|------|--------|---------|---------|
| **Anthropic** | `youtube.com/@anthropic-ai` | ~309K / 140 videos | 产品发布、技术讲解、会议演讲（Code at Claude 17 期）、AI 教育系列 | Claude 新功能发布、安全研究 |
| **Google DeepMind** | `youtube.com/@GoogleDeepMind` | 大频道 | Hannah Fry 播客视频版、纪录片 "The Thinking Game"(2亿播放)、研究 demo | 纪录片/播客视频版 |
| **OpenAI** | `youtube.com/@OpenAI` | 大频道 | 产品 demo、DevDay 演讲、播客视频版 | DevDay 演讲、新产品发布 |

### 补充

| 公司 | 频道 | 内容类型 |
|------|------|---------|
| **NVIDIA** | `youtube.com/@NVIDIA` | GTC 主题演讲(Jensen)、研究 demo |
| **Meta AI** | AI at Meta | 开源模型(Llama)、PyTorch 生态、安全研究 |
| **Y Combinator** | `youtube.com/@ycombinator` | Karpathy "Software Is Changing Again" 等 AI 主题演讲 |

### 公司自有播客

| 公司 | 播客名 | RSS / 平台 | 频率 | 价值 |
|------|--------|-----------|------|------|
| **Google DeepMind** | Google DeepMind: The Podcast (Hannah Fry) | `https://feeds.simplecast.com/JT6pbPkg` | 季播制 | Demis/Shane Legg 亲自出镜，最权威一手叙事 |
| **OpenAI** | The OpenAI Podcast (Andrew Mayne) | `shows.acast.com/openai-podcast` | 月更 | 内部视角（CFO Sarah Friar 等） |
| **NVIDIA** | NVIDIA AI Podcast | `https://feeds.megaphone.fm/nvidiaaipodcast` | 每周三 | AI 应用落地（25min/期） |
| **Anthropic** | Anthropic on Spotify | `open.spotify.com/show/4WRWnvgM5qTua4yhsRMkXe` | 不定 | 主要是会议演讲重发 |

---

## 四、关键人物播客出现图谱

### Anthropic 系

| 人物 | 角色 | 活跃度 | 最近出现 | 在哪 |
|------|------|--------|---------|------|
| **Dario Amodei** | CEO | 🔥🔥🔥 极高 | 2026.2 Dwarkesh "We are near the end of the exponential" | Dwarkesh×2, Lex, Hard Fork, Nikhil Kamath, Big Technology |
| **Daniela Amodei** | President | 🔥🔥 中高 | 2026.2 Sixth Street Podcast | CNBC, Notion First Block |
| **Amanda Askell** | 人格对齐 | 🔥🔥 中 | 2026.1 Hard Fork "Model Spec/宪法" | Crooked Media "Offline", 80,000 Hours |
| **Chris Olah** | 可解释性 | 🔥 低（但极有价值） | 2025.10 "首次长访谈" | 80,000 Hours |

### DeepMind 系

| 人物 | 角色 | 活跃度 | 最近出现 | 在哪 |
|------|------|--------|---------|------|
| **Demis Hassabis** | CEO | 🔥🔥🔥 极高 | 2026.1 CNBC "每天和 Google CEO 通话" | Lex #475, DeepMind Podcast 季终, Big Technology, All-In Summit |
| **Shane Legg** | 首席 AGI 科学家 | 🔥🔥 中 | 2025.12 DeepMind Podcast "AGI的到来" | Dwarkesh |

### 其他关键人物

| 人物 | 角色 | 活跃度 | 最近出现 | 在哪 |
|------|------|--------|---------|------|
| **Ilya Sutskever** | SSI 创始人 | 🔥 极低（罕见但重磅） | 2025.11 Dwarkesh "从 scaling 时代到 research 时代" | 仅 Dwarkesh |
| **Andrej Karpathy** | Eureka Labs | 🔥🔥🔥 极高 | 2025.12 "2025 LLM Year in Review" | Dwarkesh, YC 演讲, 自有 YouTube, Latent Space |
| **Sam Altman** | OpenAI CEO | 🔥🔥 中高 | 2025.12 Big Technology "OpenAI's Plan to Win" | Tyler Cowen, Cleo Abram |
| **Jensen Huang** | NVIDIA CEO | 🔥🔥 中 | GTC 主题演讲 | BG2Pod, No Priors, GTC |

---

## 五、落地实施方案

### Phase 1：立即设置（30 分钟）

**RSS 聚合** — 用 Miniflux 或 Feedly 订阅以下 RSS：

```
# Tier 1 播客（必听）
https://api.substack.com/feed/podcast/69345.rss          # Dwarkesh
https://lexfridman.com/feed/podcast/                      # Lex Fridman
https://feeds.megaphone.fm/nopriors                       # No Priors
https://rss.flightcast.com/vgnxzgiwwzwke85ym53fjnzu.xml  # Latent Space

# Tier 2 播客（选听）
https://feeds.simplecast.com/l2i9YnTd                    # Hard Fork NYT
https://feeds.megaphone.fm/RINTP3108857801                # Cognitive Revolution
https://feeds.megaphone.fm/MLN2155636147                  # TWIML AI

# 公司官方播客
https://feeds.simplecast.com/JT6pbPkg                    # DeepMind Podcast
https://feeds.megaphone.fm/nvidiaaipodcast                # NVIDIA AI Podcast

# 公司官方博客（配合播客）
# Anthropic: https://www.anthropic.com/blog
# OpenAI: https://openai.com/blog
# DeepMind: https://blog.google/technology/ai/
```

### Phase 2：自动摘要流水线（可扩展 auto_import）

利用现有的 `auto_import.py` 框架，扩展一个播客摘要模块：

```
流程：
RSS 新 episode 检测
  → 下载音频（youtube-dl / yt-dlp）
  → Whisper 转录（或直接用官方 transcript）
  → LLM 生成中文摘要（3-5 个要点 + 关键引用）
  → 输出到 digests/podcasts/YYYY-MM-DD.md
```

**关键优化**：Dwarkesh 和 Lex 已有官方转录，直接抓文本比转音频更快更准。

### Phase 3：YouTube 监控

```
# 用 yt-dlp 监控频道新视频
yt-dlp --flat-playlist --print "%(upload_date)s %(title)s %(url)s" \
  "https://www.youtube.com/@anthropic-ai/videos" | head -5

# 或用 YouTube RSS（每个频道都有）
# 格式: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

YouTube 频道 RSS 示例：
```
Anthropic:   https://www.youtube.com/feeds/videos.xml?channel_id=UCKUhFf3P7dSnBVLP25OhwCA
DeepMind:    https://www.youtube.com/feeds/videos.xml?channel_id=UCgUvWB1_FxfhfqpDc1P5miw
OpenAI:      https://www.youtube.com/feeds/videos.xml?channel_id=UCXZCJLdBCCmpLJkO0vJT5fQ
NVIDIA:      https://www.youtube.com/feeds/videos.xml?channel_id=UCHuiy8bXnmK5nisYHUd1J5g
YCombinator: https://www.youtube.com/feeds/videos.xml?channel_id=UCcefcZRL2oaA_uBNeo5UOWg
```

---

## 六、信息流路径总结

```
源头层（你直接监控这里）
├── 播客访谈（Dwarkesh/Lex/No Priors...）—— 大佬亲口说
├── 公司 YouTube（Anthropic/DeepMind/OpenAI）—— 官方一手视频
├── 公司博客（anthropic.com/blog 等）—— 官方一手文字
└── Twitter/X —— 实时碎片信息

       ↓ 3-7 天延迟

二手层（51CTO/InfoQ/AI前线 在这里加工）
├── 翻译播客摘要 → "图灵奖得主说了XXX！"
├── 翻译博客 → "Anthropic发布重磅研究！"
└── 整合多源 → "一周AI大事件"

       ↓ 1-3 天延迟

三手层（量子位/AI信息Gap 再加工）
├── 标题党化 → "刚刚，XXX！"
└── 加入国内视角 → "对中国意味着什么"
```

**你的位置应该在源头层**。直接从播客/YouTube/博客获取信息，用自己的判断框架（三体人设）重新加工，产出差异化内容。

---

## 七、近期必听清单（按重要度排序）

| # | 内容 | 人物 | 平台 | 日期 | 为什么必听 |
|---|------|------|------|------|-----------|
| 1 | "We are near the end of the exponential" | Dario Amodei | Dwarkesh | 2026.2.13 | 最新 Anthropic 战略思考，scaling laws 在 RL regime 的新变化 |
| 2 | Claude Model Spec / 宪法 | Amanda Askell | Hard Fork | 2026.1.25 | 如何教 AI 伦理，直接关系 Claude 行为设计 |
| 3 | "从 scaling 时代到 research 时代" | Ilya Sutskever | Dwarkesh | 2025.11.25 | SSI 创始人罕见发声，预训练极限 + 新学习方法 |
| 4 | AGI 的到来 | Shane Legg | DeepMind Podcast | 2025.12.11 | DeepMind AGI 框架，2028 AGI 预测 |
| 5 | Simulating reality, path to AGI | Demis Hassabis | Lex #475 | 2025.7.23 | DeepMind CEO 长访谈，世界模型+科学研究 |
| 6 | OpenAI's Plan to Win | Sam Altman | Big Technology | 2025.12.18 | OpenAI 战略：个性化/记忆/基础设施经济学 |
| 7 | RL is terrible but everything else is worse | Andrej Karpathy | Dwarkesh | 2025.10.17 | 模型坍塌/AGI 还需 10 年/教育未来 |
| 8 | "The Thinking Game" 纪录片 | DeepMind 团队 | YouTube | 2025.11.25 | 5 年深度跟拍 DeepMind，2 亿播放 |
| 9 | 可解释性研究（首次长访谈） | Chris Olah | 80,000 Hours | 2025.10 | 神经网络内部在发生什么，从悲观转乐观 |
| 10 | Anthropic "do more with less" | Daniela Amodei | CNBC | 2026.1.3 | Anthropic 财务策略/可能 IPO |
