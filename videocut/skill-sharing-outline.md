# Don't Build Agents, Build Skills
## Agent 应用基础架构组 内部分享（20分钟）

---

## 分享结构（20 分钟分配）

| 时间 | 模块 | 内容 |
|------|------|------|
| 0-3 min | 开场：一个类比 | 数学家 vs 税务师 → 引出核心问题 |
| 3-8 min | 从 MCP 到 Skill：来龙去脉 | 时间线 + 为什么 MCP 不够 |
| 8-14 min | Skill 到底是什么 | 技术规范 + 架构思想 + 与 Agent 的关系 |
| 14-18 min | 行业采纳与生态 | 开放标准 + 各家平台落地 |
| 18-20 min | 对我们的启示 | 对 Skill 平台和运行沙箱的思考 |

---

## 第一部分：开场——一个类比（3 min）

### 数学家 vs 税务师

> Barry Zhang 在 AI Engineering Summit 上的开场：
>
> 你要报税，面前两个人——一个是世界顶级数学家，一个是在你所在州干了 20 年的税务师。你选谁？

答案显而易见。**通用智能 ≠ 专业能力**。

现在的 Agent 就是那个数学家：
- 推理能力很强 ✅
- 能连接各种工具 ✅
- **但缺乏领域专业知识** ❌
- **不会从组织经验中学习** ❌

> "Agents today are brilliant, but they lack expertise... They can't absorb your expertise super well, and they don't learn over time."
> — Barry Zhang, Anthropic

**核心问题**：我们一直在造更聪明的 Agent，但真正的瓶颈不是智力，是**专业知识的注入和复用**。

---

## 第二部分：从 MCP 到 Skill——来龙去脉（5 min）

### 时间线

```
2024-11  Anthropic 发布 MCP（Model Context Protocol）开放标准
         → 解决的问题：Agent 怎么连接外部工具和数据
         → 类比：USB 接口标准

2025-03  OpenAI 采纳 MCP（Agents SDK、ChatGPT Desktop）
2025-04  Google DeepMind 确认 Gemini 支持 MCP
2025-11  MCP 规范大升级（异步操作、无状态、服务端身份认证）
         → MCP 已经成为事实标准

2025-11-21  Barry Zhang & Mahesh Murag 在 AI Engineering Summit 演讲
            → 标题："Don't Build Agents, Build Skills Instead"
            → 这是 Anthropic 第一次公开提出 Skill 范式

2025-12-09  Anthropic 将 MCP 捐赠给 Linux Foundation (AAIF)
            → 完全放手，不再是 Anthropic 的私有标准

2025-12-18  Anthropic 发布 Agent Skills 开放标准（agentskills.io）
            → 48 小时内：Microsoft (VS Code) + OpenAI (Codex) 采纳
            → GitHub 仓库破 20,000 星

2026-01  Google Antigravity 正式集成
         Vercel 推出 skills.sh（第一个 Skill 包管理器）
         OpenAI、GitHub Copilot、Cursor 全面支持

2026-01-29  Anthropic 发布 32 页《The Complete Guide to Building Skills for Claude》

2026-02  已有 30+ 平台兼容 Agent Skills 标准
         企业部署数千个 Skills（法务、财务、招聘、工程……）
```

### MCP 解决了什么，没解决什么

```
┌─────────────────────────────────────────────┐
│                  Agent                       │
│                                              │
│  ┌────────┐  ┌────────┐  ┌────────┐         │
│  │ MCP    │  │ MCP    │  │ MCP    │  ← 连接层│
│  │Server 1│  │Server 2│  │Server 3│   管道    │
│  └────────┘  └────────┘  └────────┘         │
│                                              │
│  ┌─────────────────────────────────┐        │
│  │          ???                     │  ← 知识层│
│  │  领域专业知识从哪来？             │   缺失！ │
│  └─────────────────────────────────┘        │
└─────────────────────────────────────────────┘
```

- **MCP = 管道层（Plumbing）**：Agent 怎么连 Slack、GitHub、数据库
- **Skill = 能力层（Capability）**：Agent 怎么用好这些连接，按照专业流程干活

> 类比：MCP 是电话线路，Skill 是对话剧本。光有线路，不知道怎么跟客户说话，没用。

---

## 第三部分：Skill 到底是什么（6 min）

### 一句话定义

**Skill = 一个文件夹，里面装着 Agent 在运行时动态加载的程序化知识。**

### 最小结构

```
my-skill/
└── SKILL.md          # 唯一必须文件
```

SKILL.md 示例：

```yaml
---
name: code-review
description: 按团队规范做 Code Review。当用户提交 PR 或要求代码审查时使用。
---

## Code Review 流程

1. 先检查是否有测试覆盖
2. 检查命名规范是否符合项目约定
3. 检查是否有安全隐患（OWASP Top 10）
4. 给出具体修改建议，而非笼统评价
5. 区分 must-fix 和 nice-to-have
```

### 完整结构（进阶）

```
my-skill/
├── SKILL.md              # 主指令（必须，建议 < 500 行）
├── scripts/
│   └── validate.py       # Agent 可执行的脚本
├── references/
│   └── api-spec.md       # 详细参考文档（按需加载）
└── assets/
    └── template.html     # 模板、图表等静态资源
```

### 开放标准规范要点（agentskills.io）

| 字段 | 必须 | 说明 |
|------|------|------|
| `name` | ✅ | ≤64字符，kebab-case（如 `code-review`） |
| `description` | ✅ | ≤1024字符，描述做什么 + 什么时候用 |
| `license` | ❌ | 开源协议 |
| `compatibility` | ❌ | 环境要求（如需要 docker, git） |
| `metadata` | ❌ | 任意 KV 扩展字段 |
| `allowed-tools` | ❌ | 预授权工具列表（实验性） |

**设计哲学：Progressive Disclosure（渐进式披露）**

```
第一层：metadata（~100 tokens）
  → 启动时加载所有 Skill 的 name + description
  → Agent 知道"我有哪些能力"

第二层：instructions（< 5000 tokens）
  → 激活某个 Skill 时才加载 SKILL.md 正文
  → Agent 知道"这个任务怎么做"

第三层：resources（按需）
  → 只在需要时加载 scripts/、references/
  → Agent 获得"详细参考和工具"
```

**为什么这很重要？** Context Window 是稀缺资源。不能一次塞几十个 Skill 的全部内容进去。

### Skill 与 Agent 的关系——关键区分

```
旧范式：                          新范式：
"这个任务该哪个 Agent 处理？"      "这个任务需要什么 Skill？"

┌──────┐ ┌──────┐ ┌──────┐       ┌──────────────────────┐
│Agent │ │Agent │ │Agent │       │   通用 Agent          │
│客服   │ │代码   │ │数据   │       │                      │
│      │ │      │ │      │       │  ┌────┐ ┌────┐ ┌────┐ │
│专用   │ │专用   │ │专用   │       │  │Sk1 │ │Sk2 │ │Sk3 │ │
│逻辑   │ │逻辑   │ │逻辑   │       │  └────┘ └────┘ └────┘ │
└──────┘ └──────┘ └──────┘       │  动态加载、可组合      │
                                  └──────────────────────┘
每个 Agent 都是定制品              一个 Agent + N 个 Skill
更换域 = 重建 Agent               更换域 = 换一组 Skill
知识锁死在 Agent 里               知识独立于 Agent 存在
```

### 核心洞察

> **"Code is the universal interface for agent execution."**
> 给 LLM 文件系统访问 + 代码执行能力，一个 Agent 循环就能处理一切。
> 不需要为每个用例造一个新 Agent。

**Thin Scaffolding 原则**：Bash + 文件系统 = 足够轻量的基础设施。Agent 的脚手架应该尽可能薄，复杂度放在 Skill 里。

---

## 第四部分：行业采纳与生态（4 min）

### 开放标准的胜利——MCP 的剧本再演一次

| 标准 | 发布时间 | 核心价值 | 采纳速度 |
|------|----------|----------|----------|
| MCP | 2024-11 | Agent ↔ 工具连接 | 6个月内主流平台全采纳 |
| Agent Skills | 2025-12-18 | Agent 知识注入 | **48 小时** Microsoft + OpenAI 采纳 |

### 谁在用

| 平台 | 实现方式 |
|------|----------|
| **Claude Code** | 原生支持，Skill 发源地 |
| **GitHub Copilot** | VS Code 集成 Agent Skills |
| **OpenAI Codex** | "structurally identical architecture" |
| **Cursor** | 全面兼容 |
| **Google Antigravity** | 2026-01 正式集成 |
| **Vercel skills.sh** | 第一个 Skill 包管理器 |
| **30+ 其他平台** | 持续增长 |

### 可移植性

> 一个为 OpenAI Codex 创建的 Skill，不做任何修改，就能在 Claude Code、GitHub Copilot、Cursor、Google Antigravity 里运行。

这就是开放标准的力量。

### Skill 生态三层结构

```
┌───────────────────────────────────┐
│       Enterprise Skills            │ ← 企业内部最佳实践
│  部署流程、代码规范、安全审查...      │    不对外公开
├───────────────────────────────────┤
│       Partner Skills               │ ← 工具厂商提供
│  Figma 设计转代码、Sentry 错误分析   │    随产品分发
├───────────────────────────────────┤
│       Foundational Skills          │ ← 社区 / 开源
│  Code Review、Git 工作流、文档生成   │    agentskills.io
└───────────────────────────────────┘
```

### 企业价值（数据来源：早期企业部署报告）

- **成本**：定制 Agent 方案约 $500K → Skill 复用可降至 10-20%
- **上手速度**：新领域接入快 60-80%
- **人才瓶颈转移**：从"找 AI 工程师"变成"让领域专家写 Skill"
- **持续改进**：Agent 可以自己生成新 Skill 供下次复用

### Agent 自我进化

> 演讲中最值得关注的 demo：Agent 执行任务后，自动把学到的步骤写成新的 SKILL.md，存入 Skill 文件夹供下次使用。

这意味着：**Skill 不只是人写给 Agent 的，Agent 自己也能写 Skill**。Runtime 变成了操作系统。

---

## 第五部分：对我们的启示（2 min）

### 对 Skill 平台的思考

1. **Skill Registry 是核心基础设施**
   - 发现、分发、版本管理
   - 类比：MCP 有 registry，Skill 现在有 skills.sh
   - 企业级需要权限控制（哪些 Skill 可以全组织部署）

2. **质量保证很关键**
   - Skill 本质是 Prompt + 脚本，质量参差不齐
   - 需要验证框架（agentskills 已提供 `skills-ref validate`）
   - 企业场景需要审批流程

3. **Skill 编排 > Agent 编排**
   - 旧模式：编排多个 Agent 协作
   - 新模式：一个 Agent 在不同阶段加载不同 Skill
   - 复杂度从"多 Agent 通信"降到"Skill 选择策略"

### 对运行沙箱的思考

1. **Skill 可以包含任意脚本**
   - `scripts/` 目录里可以是 Python、Bash、JS
   - Agent 有执行权限
   - → 沙箱隔离是刚需（安全边界）

2. **Progressive Loading 需要运行时支持**
   - Metadata 常驻 → Instructions 按需加载 → Scripts 隔离执行
   - 这个三层加载机制需要 runtime 配合

3. **跨平台兼容性**
   - 同一个 Skill 要在多个 Agent 平台运行
   - 沙箱需要提供一致的执行环境（文件系统、网络、工具集）

### 一句话总结

> **Agents 负责思考，Skills 负责知道怎么做。**
> **MCP 解决连接问题，Skills 解决知识问题。**
> **我们不需要造 100 个 Agent，我们需要造 1 个 Agent + 100 个 Skill。**

---

## 参考资料

- [Barry Zhang & Mahesh Murag: "Don't Build Agents, Build Skills Instead" (视频)](https://www.youtube.com/watch?v=CEvIs9y1uog)
- [Agent Skills 开放标准规范](https://agentskills.io/specification)
- [Anthropic Skills GitHub](https://github.com/anthropics/skills)
- [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills)
- [The Complete Guide to Building Skills for Claude (32页 PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- [Anthropic launches enterprise Agent Skills (VentureBeat)](https://venturebeat.com/ai/anthropic-launches-enterprise-agent-skills-and-opens-the-standard)
- [Agent Skills: Anthropic's Next Bid to Define AI Standards (The New Stack)](https://thenewstack.io/agent-skills-anthropics-next-bid-to-define-ai-standards/)
- [Agent Skills Standard: Microsoft, OpenAI Adopt in 48 Hours](https://byteiota.com/agent-skills-standard-microsoft-openai-adopt-in-48-hours/)
- [OpenAI Codex Skills 文档](https://developers.openai.com/codex/skills/)
- [GitHub Copilot Agent Skills Guide](https://code.visualstudio.com/docs/copilot/customization/agent-skills)

---

## Q&A 备用弹药

**Q: Skill 跟 Prompt Engineering 有什么区别？**
> Prompt 是"说服模型"，Skill 是"给模型写行为规范"。Prompt 是一次性的对话技巧，Skill 是可版本化、可分发、可复用的结构化知识。从"每次都要重新说"到"写一次到处用"。

**Q: Skill 会不会只是 Anthropic 的策略，其他厂商不一定跟？**
> 事实已经证明了——48 小时内 Microsoft 和 OpenAI 就采纳了。这跟 MCP 的剧本一模一样。当标准足够简单且开放，没有厂商有动机自己另搞一套。

**Q: 跟 LangChain 的 Tool/Chain 有什么区别？**
> LangChain 的 Tool 是代码级 API 封装，需要开发者写 Python。Skill 是 Markdown + 脚本，领域专家就能写。LangChain 绑定特定框架，Skill 是跨平台标准。两个层次不同。

**Q: 安全性怎么保证？Skill 可以执行任意脚本？**
> 好问题，这正是运行沙箱存在的价值。Skill 的 `allowed-tools` 字段可以限制工具访问权限，但更根本的隔离需要在 runtime 层面做。企业部署需要审批 + 沙箱双重保障。

**Q: Skill 能自动发现和加载吗？**
> 是的。Agent 启动时加载所有 Skill 的 metadata（name + description），根据用户请求自动判断激活哪个 Skill。也支持手动调用（`/skill-name`）。这就是 Progressive Disclosure 设计。
