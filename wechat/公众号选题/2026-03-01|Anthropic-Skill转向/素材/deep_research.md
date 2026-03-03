以下是完整的素材报告：

---

# 素材报告：Anthropic-Skill转向
采集时间：2026-03-03

---

## 核心事实（已验证）

**1. Anthropic 提出"别造 Agent，改造 Skill"**
- Anthropic 工程师 Barry Zhang 和 Mahesh Murag 在 AI Engineer Code Summit（约2025年11-12月）发表演讲，题为《Don't Build Agents, Build Skills Instead》
- 核心论断：专用 Agent 架构在企业落地中是失败的，通用 Agent + Skills 才是正确路径
- 信源：[bagrounds.org/videos/dont-build-agents-build-skills-instead](https://bagrounds.org/videos/dont-build-agents-build-skills-instead-barry-zhang-mahesh-murag-anthropic)

**2. Anthropic 官方承认 2025 年 Agent 热潮"失败了"**
- Kate Jensen（Anthropic 美洲区负责人），2026年2月24日：**"2025 年本应是 Agent 改变企业的一年，但热潮被证明是提前的。这不是努力不够，而是方法错了。"**
- 信源：[TechCrunch 2026-02-24](https://techcrunch.com/2026/02/24/anthropic-launches-new-push-for-enterprise-agents-with-plug-ins-for-finance-engineering-and-design/)

**3. Agent Skills 正式发布**
- 2025年10月16日：Anthropic 发布 Agent Skills，面向 Pro/Max/Team/Enterprise 用户
- 信源：[claude.com/blog/skills](https://claude.com/blog/skills) / [anthropic.com/news/skills](https://www.anthropic.com/news/skills)

**4. Agent Skills 成为开放标准**
- 2025年12月18日：Anthropic 将 Agent Skills 规范公开为行业开放标准，托管于 agentskills.io
- 2025年12月20日（两天后）：OpenAI 宣布 Codex 采用该标准
- 信源：[SiliconAngle 2025-12-18](https://siliconangle.com/2025/12/18/anthropic-makes-agent-skills-open-standard/)

**5. Anthropic 的开放标准路线图（已形成规律）**
- 2024年11月：发布 MCP → 2025年12月9日捐献给 Linux 基金会（Agentic AI Foundation），OpenAI、Google、Microsoft 联合加入
- 2025年10月：发布 Agent Skills → 2025年12月开放标准，OpenAI、Microsoft 立即跟进
- 信源：[anthropic.com/news/donating-the-model-context-protocol](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)

---

## 关键人物/公司

| 人物/机构 | 角色 | 关键数据点 |
|-----------|------|-----------|
| **Barry Zhang**（Anthropic） | 演讲者，核心论断提出者 | "Don't Build Agents, Build Skills Instead" 演讲 |
| **Mahesh Murag**（Anthropic） | 演讲者，工程师 | 同上 |
| **Kate Jensen**（Anthropic 美洲区负责人） | 产品战略发声 | "2025 Agent 热潮是方法错了，不是努力不够" |
| **Dario Amodei**（Anthropic CEO） | 战略定调者 | 指导整体开放标准策略 |
| **Simon Willison**（独立技术观察者） | 核心评论者 | 称 Spec 为 "deliciously tiny"；记录 OpenAI 两天内跟进这一关键事实 |
| **Holger Mueller**（Constellation Research 分析师） | 怀疑派 | "单一厂商很难靠自己制定标准" |
| **OpenAI** | 竞争/跟随者 | Dec 20, 2025 采用 Agent Skills 标准 |
| **首批 Skills 伙伴** | 生态 | Atlassian、Canva、Cloudflare、Figma、Notion、Stripe、Zapier |

---

## 时间线

| 日期 | 事件 |
|------|------|
| 2024-11 | Anthropic 发布 MCP（Model Context Protocol） |
| 2024-12 | Anthropic 发布《Building Effective Agents》研究报告，奠定"简单优先"哲学 |
| 2025-10-16 | **Agent Skills 正式发布**，面向 Pro/Max/Team/Enterprise 用户 |
| 2025-11/12 | Barry Zhang & Mahesh Murag 在 AI Engineer Code Summit 发表"别造 Agent，造 Skill"演讲 |
| 2025-12-09 | Anthropic 将 MCP 捐献给 Linux 基金会，成立 Agentic AI Foundation；OpenAI、Block 联合创立 |
| 2025-12-18 | **Agent Skills 发布为开放标准**（agentskills.io），7大合作伙伴入驻 |
| 2025-12-19 | Simon Willison 发表分析，记录生态快速跟进 |
| 2025-12-20 | **OpenAI 宣布 Codex 采用 Agent Skills 标准**（两天内！） |
| 2026-02-05 | Anthropic 发布 Claude Opus 4.6，含"Agent Teams"（协作子 Agent）功能 |
| 2026-02-24 | Anthropic 发布企业插件（Claude Cowork），垂直覆盖金融/工程/HR/设计 |
| 2026-02-25 | Anthropic 收购 Vercept（计算机使用 AI 初创公司） |

---

## 多方观点

### 官方/支持方

**Anthropic（工程博客）：**
> "传统做法会为每个用例创建碎片化的定制 Agent，这带来了无法管理的复杂度……Skills 解决了这个问题。"

**Barry Zhang（演讲核心论点）：**
> "我们以为不同领域的 Agent 会长得很不一样，结果发现底层 Agent 比我们想象的更通用。"

**Kate Jensen（2026-02-24）：**
> "2025 年失败的不是努力，是方法。"

### 技术分析方（正面）

**Simon Willison：**
> Spec"小得令人愉悦"（deliciously tiny），可读性极强。OpenAI 在两天内跟进是生态认可的强信号。

**53AI（中文技术博客）：**
> 正确架构：单 Agent 起步 → Skills 沉淀方法论 → MCP 负责连接。推理层不该包含具体流程，那是 Skills 的工作。

### 怀疑/批评方

**Holger Mueller（Constellation Research 分析师）：**
> "单一厂商很难靠自己制定标准，MCP 被全行业采纳是特例，不代表 Agent Skills 一定会重复这个结果。"

**Tom MacWright（技术开发者，实测后）：**
> Anthropic 自己的工具没把 Skills 创建在正确的目录，安全建议"过度乐观"——指望用户审计所有 Skill 代码是不现实的。

**arXiv 安全研究论文（2602.12430）：**
> 对 42,447 个社区 Skills 的扫描：**26.1% 存在漏洞**（提示注入、数据外泄、权限提升）；包含可执行脚本的 Skills 出现漏洞的概率是其他的 2.12 倍；单一恶意行为者通过模板化仿冒制造了 54.1% 的漏洞 Skills。
> 信源：[arxiv.org/html/2602.12430v1](https://arxiv.org/html/2602.12430v1)

---

## 技术对照表：Skill vs. 专用 Agent

| 维度 | Skill | 专用 Agent |
|------|-------|-----------|
| 架构 | 通用 Agent + 指令覆盖层 | 独立定制系统 |
| 可移植性 | 跨平台（开放标准） | 锁定特定部署 |
| 可组合性 | 多 Skills 可叠加 | Agent 之间难组合 |
| 维护成本 | 用 Git 版本管理，普通人可写 | 需要工程团队维护 |
| 创建门槛 | 非技术人员（HR/法务/财务）30分钟可完成 | 需要专业工程师 |
| 上下文 | 按需加载，权限临时 | 持续运行/目标导向 |

**渐进式披露架构（3层）：**
- Level 1：启动时只扫描 name + description（约100 token/个）
- Level 2：判断相关后加载完整 SKILL.md（<5000 token）
- Level 3：执行过程中按需加载引用文件（理论无限）

**文件结构极简：**
```
my-skill/
├── SKILL.md          # 必须：YAML frontmatter + Markdown 指令
├── reference.md      # 可选：补充文档
├── scripts/          # 可选：Python/Bash 脚本
└── assets/           # 可选：模板、示例
```

---

## 数据表

| 数据 | 数值 | 信源 | 可信度 |
|------|------|------|--------|
| Agent Skills GitHub stars | 81,500+ stars，8,600+ forks | GitHub 直接观测 | 高 |
| 社区 Skills 漏洞率 | 26.1%（42,447个Skills样本） | arXiv 2602.12430 | 高（学术论文） |
| Claude Sonnet 4.6 OSWorld 得分 | 72.5%（从2024年底的<15%上升） | Anthropic Vercept 收购页 | 高（一手源） |
| Skills 渐进披露 token 节省 | 60-80% | 腾讯云博客/53AI | 低（非 Anthropic 官方数据） |
| Anthropic 企业客户 | 300,000+（2025年8月），500+ 年均消费 $1M+ | 媒体报道 | 中（多源交叉） |
| Anthropic ARR | $1B（2024年12月）→ $14B（2026年2月） | 媒体报道 | 中（不同来源数字有差异） |
| OpenAI 跟进速度 | 2天（12月18日→12月20日） | Simon Willison 直接记录 | 高 |
| Agentic AI Foundation 年承诺资金 | $5M+ | PulseMCP | 低（未见一手源） |

---

## 争议点和未解问题

**1. "转向"的边界在哪里？**
Anthropic 并没有"停止"建 Agents——Claude Opus 4.6 同期还发布了"Agent Teams"（子 Agent 协作）。准确表述是：不要为每个垂直域建一个专用 Agent，而是建一个通用 Agent + 用 Skills 装载领域知识。这个区别容易被媒体夸大。

**2. 开放标准 vs. Claude 优化的矛盾**
SKILL.md 格式是开放的，但 description 字段的优化逻辑是针对 Claude 的语义理解调校的——同一个 Skill，在 GPT-4o 或 Gemini 上可能需要重写 description 才能达到最佳路由效果。"开放标准"有名实之争。

**3. 安全漏洞没有被官方正视**
arXiv 论文（2602.12430）实测了26.1%漏洞率，但 Anthropic 官方文档给出的安全建议是"请用户审计所有 Skill 代码"——MacWright 指出这是"wildly optimistic"，不现实。这是生态扩张中尚未解决的核心风险。

**4. MCP 先例是否可复制？**
MCP 的全行业采纳（Google、OpenAI、Microsoft 全部跟进）被视为 Anthropic 开放标准策略的成功案例。但 Holger Mueller 提出：MCP 是基础管道，而 Skills 更靠近应用层，生态动力可能不同。Anthropic 能否再次定义行业标准？

**5. Barry Zhang 演讲原始视频未直接抓取**
演讲广被引用，但视频本体可能有限制。[lilys.ai 记录了笔记/摘要](https://lilys.ai/en/notes/agent-skills-20251225/build-skills-not-agents)，多源交叉一致，可信度较高，但仍属转述。

---

## 一手源清单

| 类型 | 来源 | URL |
|------|------|-----|
| 官方产品公告 | Anthropic | https://www.anthropic.com/news/skills |
| 官方工程博客 | Anthropic Engineering | https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills |
| 官方概念区分 | Anthropic | https://claude.com/blog/skills-explained |
| 官方研究论文 | Anthropic Research | https://www.anthropic.com/research/building-effective-agents |
| 开放标准捐献 | Anthropic | https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation |
| GitHub 规范 | anthropics/skills | https://github.com/anthropics/skills |
| 开放标准站 | agentskills.io | https://agentskills.io |
| API 文档 | Claude Platform | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| 核心演讲 | AI Engineer Code Summit | https://bagrounds.org/videos/dont-build-agents-build-skills-instead-barry-zhang-mahesh-murag-anthropic |
| 演讲笔记/摘要 | Lilys.ai | https://lilys.ai/en/notes/agent-skills-20251225/build-skills-not-agents |
| 安全研究论文 | arXiv 2602.12430 | https://arxiv.org/html/2602.12430v1 |
| 企业扩张报道 | TechCrunch 2026-02-24 | https://techcrunch.com/2026/02/24/anthropic-launches-new-push-for-enterprise-agents-with-plug-ins-for-finance-engineering-and-design/ |
| 开放标准报道 | SiliconAngle | https://siliconangle.com/2025/12/18/anthropic-makes-agent-skills-open-standard/ |
| 技术深度分析 | Lee Hanchung | https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/ |
| 独立开发者实测 | Tom MacWright | https://macwright.com/2025/10/20/agent-skills |
| 生态观察 | Simon Willison | https://simonwillison.net/2025/Dec/19/agent-skills/ |
| MCP+Skills 关系解析 | cra.mr | https://cra.mr/mcp-skills-and-agents/ |
| 中文战略分析 | 知乎 | https://zhuanlan.zhihu.com/p/1986726969799358152 |
| 中文开放标准分析 | 知乎 | https://zhuanlan.zhihu.com/p/1985262409338868139 |
| 中文架构解析 | 腾讯云开发者社区 | https://cloud.tencent.com.cn/developer/article/2614419 |
| 中文实践指南 | 53AI | https://www.53ai.com/news/LargeLanguageModel/2026021218294.html |
| 中文视频 | Bilibili | https://www.bilibili.com/video/BV1fBqSBcEXP/ |

---

## 潜在配图素材

| 配图类型 | 说明 | 来源建议 |
|----------|------|----------|
| Skill 目录结构截图 | 展示 SKILL.md 文件结构，直观展现"能力即文件"概念 | 从 GitHub anthropics/skills 截图 |
| 渐进式披露架构图 | 3层架构（元数据/指令/资源）的对比图 | 自制或取自 Anthropic 工程博客 |
| 时间线对比图 | MCP 路径（2024→开放标准）vs Skills 路径（2025→开放标准）的同构对比 | 自制 |
| Skills vs 专用Agent 对比表 | 上文技术对照表可视化 | 自制 |
| OpenAI 两天内跟进截图 | Simon Willison 记录的时间戳截图 | simonwillison.net |
| arXiv 安全漏洞率图表 | 26.1% 漏洞率的分布图 | arxiv.org/html/2602.12430v1 中的原始图表 |
| agentskills.io 官网截图 | 开放标准首页 + 合作伙伴 logo 墙 | 直接截图 |
| 完整生态栈图 | Agent Loop → Runtime → MCP → Skills 四层架构 | 自制 |

---

**采集说明：**
- 核心事实（Kate Jensen 引用、OpenAI 跟进时间线、arXiv 漏洞数据）均有一手源背书
- Barry Zhang 演讲引用来自多源交叉摘要，视频本体访问受限，注意在文章中标明
- "60-80% token 节省"为第三方测算数据，非 Anthropic 官方，建议不做主要论据
- 争议最大的问题：这究竟是真正的技术转向，还是一次标准制定的生态策略？两者都是，但叙事角度不同，适合作为文章的核心张力