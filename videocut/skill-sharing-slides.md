---
marp: true
theme: uncover
paginate: true
style: |
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
  section {
    font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: #0f0f23;
    color: #e0e0e0;
  }
  h1 { color: #fff; font-weight: 900; }
  h2 { color: #f0f0f0; font-weight: 700; }
  h3 { color: #ccc; }
  strong { color: #ffd700; }
  em { color: #88c0d0; font-style: normal; }
  code { background: #1a1a3e; color: #88c0d0; font-size: 0.85em; }
  pre { background: #1a1a3e !important; border-radius: 8px; }
  blockquote { border-left: 4px solid #ffd700; padding-left: 16px; color: #ccc; font-style: italic; }
  table { font-size: 0.8em; }
  th { background: #2a2a4a; color: #ffd700; }
  td { background: #1a1a3e; }
  a { color: #88c0d0; }
  section.lead h1 { font-size: 2.5em; }
  section.lead h2 { font-size: 1.3em; color: #888; }
  .columns { display: flex; gap: 40px; }
  .col { flex: 1; }
---

<!-- _class: lead -->

# Don't Build Agents
# Build Skills

**Agent 应用基础架构组 · 内部分享**

2026.03

---

## 今天聊什么

| 模块 | 内容 |
|------|------|
| **开场** | 一个类比：为什么 Agent 不够 |
| **来龙去脉** | 从 MCP 到 Skill 的完整时间线 |
| **技术剖析** | Skill 到底是什么、怎么设计的 |
| **行业生态** | 48 小时席卷全行业的开放标准 |
| **对我们的启示** | Skill 平台 + 运行沙箱该怎么想 |

---

<!-- _class: lead -->

# Part 1
## 一个类比

---

## 数学家 vs 税务师

你要报税，面前两个人：

<div class="columns">
<div class="col">

### 世界顶级数学家
- 智商 180
- 什么都能推理
- 但没报过一天税

</div>
<div class="col">

### 20 年老税务师
- 你这个州的税法全背下来了
- 知道哪些坑能避
- 闭着眼给你报完

</div>
</div>

**你选谁？**

<!-- Barry Zhang 在 AI Engineering Summit 上的开场 -->

---

## 今天的 Agent = 那个数学家

- 推理能力很强 ✅
- 能连接各种工具（MCP） ✅
- **但缺乏领域专业知识** ❌
- **不会从组织经验中学习** ❌

> "Agents today are brilliant, but they lack expertise...
> They can't absorb your expertise super well,
> and they don't learn over time."
> — *Barry Zhang, Anthropic*

---

## 核心问题

<br>

# 瓶颈不是智力
# 是**专业知识的注入和复用**

<br>

我们一直在造更聪明的 Agent
但真正该解决的是：**怎么把专家脑子里的东西给 Agent**

---

<!-- _class: lead -->

# Part 2
## 从 MCP 到 Skill：来龙去脉

---

## 时间线（上半段）

```
2024-11   Anthropic 发布 MCP 开放标准
          → 解决：Agent 怎么连接外部工具和数据
          → 类比：USB 接口标准

2025-03   OpenAI 采纳 MCP（Agents SDK、ChatGPT Desktop）

2025-04   Google DeepMind 确认 Gemini 支持 MCP

2025-11   MCP 规范大升级（异步、无状态、身份认证）
          → MCP 成为事实行业标准
```

MCP 用 **1 年时间**统一了"Agent 怎么连工具"的问题

---

## 时间线（下半段）

```
2025-11-21  Anthropic 首次公开提出 Skill 范式
            → AI Engineering Summit 演讲

2025-12-09  MCP 捐赠给 Linux Foundation（AAIF）
            → 不再是 Anthropic 私有标准

2025-12-18  Agent Skills 开放标准发布（agentskills.io）
            → 48 小时内 Microsoft + OpenAI 采纳 🔥

2026-01     Google / Vercel / Cursor / Copilot 全面跟进
            → 30+ 平台兼容

2026-01-29  Anthropic 发布 32 页 Skill 建设指南
```

MCP 捐出去 → 立刻推 Skill → **同一套剧本再演一次**

---

## MCP 解决了什么，**没**解决什么

```
┌──────────────────────────────────────┐
│              Agent                    │
│                                       │
│  ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ MCP  │ │ MCP  │ │ MCP  │ ← 连接层 │
│  │Slack │ │GitHub│ │ DB   │    管道   │
│  └──────┘ └──────┘ └──────┘          │
│                                       │
│  ┌──────────────────────────┐         │
│  │         ???               │ ← 知识层│
│  │  领域专业知识从哪来？      │   缺失！│
│  └──────────────────────────┘         │
└──────────────────────────────────────┘
```

---

## 两层模型

| | **MCP** | **Skill** |
|---|---|---|
| 解决什么 | Agent ↔ 外部工具**连接** | Agent 的**领域知识** |
| 类比 | 电话线路 | 对话剧本 |
| 技术层 | 协议 + Server | 文件夹 + Markdown |
| 谁写 | 开发者 | 开发者 **或** 领域专家 |

<br>

> 光有线路，不知道怎么跟客户说话 → 没用
> **MCP 是管道，Skill 是知识**

---

<!-- _class: lead -->

# Part 3
## Skill 到底是什么

---

## 一句话定义

<br>

# Skill = 一个文件夹
# 装着 Agent 在运行时**动态加载**的程序化知识

<br>

最小形态：一个 `SKILL.md` 文件

---

## 最小示例

```yaml
---
name: code-review
description: 按团队规范做 Code Review。当用户提交 PR 时使用。
---

## Code Review 流程

1. 先检查是否有测试覆盖
2. 检查命名规范是否符合项目约定
3. 检查是否有安全隐患（OWASP Top 10）
4. 给出具体修改建议，而非笼统评价
5. 区分 must-fix 和 nice-to-have
```

**就这？** 对，就这。YAML frontmatter + Markdown 正文。

---

## 完整结构

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

开放标准规范：**agentskills.io/specification**

| 必须字段 | 说明 |
|----------|------|
| `name` | ≤64字符，kebab-case |
| `description` | ≤1024字符，做什么 + 什么时候用 |

---

## 设计哲学：Progressive Disclosure

```
第一层：Metadata（~100 tokens）
  → 启动时加载所有 Skill 的 name + description
  → Agent 知道"我有哪些能力"

第二层：Instructions（< 5000 tokens）
  → 激活时才加载 SKILL.md 正文
  → Agent 知道"这个任务怎么做"

第三层：Resources（按需）
  → 只在需要时加载 scripts/、references/
  → Agent 获得"详细参考和工具"
```

**为什么？** Context Window 是稀缺资源。
100 个 Skill 的 metadata 才 ~10K tokens，全部正文可能 500K+

---

## 范式转变：关键区分

<div class="columns">
<div class="col">

### 旧范式：多 Agent
"这个任务该**哪个 Agent** 处理？"

```
┌──────┐ ┌──────┐ ┌──────┐
│Agent │ │Agent │ │Agent │
│客服   │ │代码   │ │数据   │
│专用   │ │专用   │ │专用   │
│逻辑   │ │逻辑   │ │逻辑   │
└──────┘ └──────┘ └──────┘
```

更换域 = **重建 Agent**
知识**锁死**在 Agent 里

</div>
<div class="col">

### 新范式：一 Agent + N Skill
"这个任务需要**什么 Skill**？"

```
┌────────────────────┐
│   通用 Agent        │
│                     │
│ ┌────┐┌────┐┌────┐ │
│ │Sk1 ││Sk2 ││Sk3 │ │
│ └────┘└────┘└────┘ │
│  动态加载、可组合    │
└────────────────────┘
```

更换域 = **换一组 Skill**
知识**独立于** Agent 存在

</div>
</div>

---

## 核心洞察

> **"Code is the universal interface for agent execution."**

给 LLM 文件系统访问 + 代码执行能力
→ 一个 Agent 循环就能处理一切
→ 不需要为每个用例造一个新 Agent

<br>

**Thin Scaffolding 原则**：
Bash + 文件系统 = 足够轻量的基础设施
**Agent 的脚手架尽可能薄，复杂度放在 Skill 里**

---

<!-- _class: lead -->

# Part 4
## 行业采纳与生态

---

## MCP 的剧本再演一次——但更快

| 标准 | 发布 | 核心价值 | 采纳速度 |
|------|------|----------|----------|
| MCP | 2024-11 | Agent ↔ 工具连接 | ~6 个月 |
| Agent Skills | 2025-12-18 | Agent 知识注入 | **48 小时** |

<br>

为什么更快？因为 MCP 已经教育了市场——**开放标准是正确的路**

---

## 谁在用

| 平台 | 状态 |
|------|------|
| **Claude Code** | 原生支持，Skill 发源地 |
| **GitHub Copilot** | VS Code 集成 Agent Skills |
| **OpenAI Codex** | "structurally identical architecture" |
| **Cursor** | 全面兼容 |
| **Google Antigravity** | 2026-01 正式集成 |
| **Vercel skills.sh** | 第一个 Skill **包管理器** |
| **30+ 其他** | 持续增长 |

> 同一个 Skill 文件夹 → 所有平台通用 → **零迁移成本**

---

## 生态三层结构

```
┌───────────────────────────────────────────┐
│           Enterprise Skills                │ ← 企业最佳实践（不公开）
│     部署流程 · 代码规范 · 安全审查          │
├───────────────────────────────────────────┤
│           Partner Skills                   │ ← 工具厂商随产品分发
│     Figma 设计转代码 · Sentry 错误分析      │
├───────────────────────────────────────────┤
│         Foundational Skills                │ ← 社区 / 开源
│     Code Review · Git 工作流 · 文档生成     │
└───────────────────────────────────────────┘
```

Fortune 100 企业已在法务/财务/招聘/工程部门部署 Skills

---

## Agent 自己写 Skill

演讲中最关键的 demo：

> Agent 执行完一个任务后
> **自动把学到的步骤写成新的 SKILL.md**
> 存入 Skill 文件夹供下次使用

<br>

Skill 不只是**人写给 Agent** 的
Agent **自己也能写** Skill

→ Runtime 变成了**操作系统**

---

## 企业价值

| 指标 | 效果 |
|------|------|
| **成本** | 定制 Agent ~$500K → Skill 复用降至 10-20% |
| **新域接入** | 快 60-80% |
| **人才瓶颈** | 从"找 AI 工程师"→"让领域专家写 Skill" |
| **持续改进** | Agent 自生成 Skill，飞轮转起来 |

---

<!-- _class: lead -->

# Part 5
## 对我们的启示

---

## 对 Skill 平台的思考

**1. Skill Registry 是核心基础设施**
- 发现、分发、版本管理
- 企业级需要权限控制（哪些 Skill 可全组织部署）

**2. 质量保证很关键**
- Skill 本质是 Prompt + 脚本，质量参差不齐
- 需要验证框架（已有 `skills-ref validate`）
- 企业场景需要审批流程

**3. Skill 编排 > Agent 编排**
- 复杂度从"多 Agent 通信" → "Skill 选择策略"

---

## 对运行沙箱的思考

**1. 安全边界是刚需**
- `scripts/` 可包含任意 Python、Bash、JS
- Agent 有执行权限 → 沙箱隔离不可或缺

**2. 三层加载需要 runtime 配合**
- Metadata 常驻 → Instructions 按需 → Scripts 隔离执行
- 这个 Progressive Loading 机制需要 runtime 支撑

**3. 跨平台一致性**
- 同一 Skill 跑在多个 Agent 平台
- 沙箱提供一致的执行环境（文件系统、网络、工具集）

---

<!-- _class: lead -->

# 总结

---

## 三句话

<br>

# Agents 负责**思考**
# Skills 负责**知道怎么做**

<br>

# MCP 解决**连接**问题
# Skills 解决**知识**问题

<br>

# 不是造 100 个 Agent
# 而是 **1 个 Agent + 100 个 Skill**

---

## 参考资料

- [Don't Build Agents, Build Skills Instead (视频)](https://www.youtube.com/watch?v=CEvIs9y1uog)
- [Agent Skills 开放标准](https://agentskills.io/specification)
- [Claude Code Skills 文档](https://code.claude.com/docs/en/skills)
- [32 页 Skill 建设指南 (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- [Anthropic Skills GitHub](https://github.com/anthropics/skills)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills/)

---

<!-- _class: lead -->

# Q&A

