# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Nuwa (女娲计划) is a vision/research project for building autonomous digital life — AI agents that self-replicate, learn, and act independently. This is currently a **documentation-only repository** with no application code, build system, or tests.

The core thesis: "Not building one powerful agent — building an agent that generates agents."

## Repository Structure

- `docs/zh/` — Chinese (primary) documentation
- `docs/en/` — English translations (faithful to author's voice)
- `README.md` — Bilingual entry point and navigation hub
- `docs/*/nuwa-plan.md` — Full vision document (compression theory, axioms, self-replicating agents)
- `docs/*/motivation-training.md` — Methodology (compress-predict-calibrate loop)

## Key Concepts

These concepts recur throughout the docs and should be understood when editing:

- **Intelligence as compression** — learning = compression, understanding = shorter descriptions
- **Axiom injection** — inject meta-rules ("actions that keep oneself running are good"), not knowledge
- **Self-replicating Raphael** — child instances explore new environments, compress experience back to mother
- **"Predicting the next question"** — proposed as the next paradigm beyond "predicting the next token"
- **Human = rider, AI = horse** — humans provide will/soul, AI provides cognition/speed

## Writing Conventions

- All documents are bilingual: Chinese primary in `docs/zh/`, English in `docs/en/`
- English translations preserve the author's voice and philosophical tone — not sterile academic prose
- The writing uses mythological metaphors (Pangu, Nuwa, Raphael) and grounds theory in concrete analogies
- README uses both languages inline with anchor-based navigation

## Planned Sub-projects

- **nuwa-annotator** — heart/soul mapping tool for human-AI annotation
- **nuwa-info-agent** — first self-replicating loop experiment

## ⛔ 每次会话必读文件（不论任务类型）

**无论是写作、自动化、调研还是任何任务，新会话必须先读以下文件。不读就开工 = 从零开始 = 浪费用户纠正成本。**

| 顺序 | 文件 | 内容 | 为什么必读 |
|------|------|------|-----------|
| 1 | Notion To-Do (`303994d02404813894b6c92e0616a5c9`) | 当前任务优先级 | 知道现在该做什么 |
| 2 | `wechat/tools/AUTOMATION_PLAN.md` | 公众号自动化流水线计划 | 知道做到哪一步了、缺什么 |
| 3 | `wechat/内容方法论.md` | 写作规则 + 三层记忆架构 + 配图规则 + Review checklist | 所有写作决策的根基 |
| 4 | `docs/claude-collaboration-protocol.md` | 协作协议（沟通风格/行为检测/Notion读写规则） | 知道怎么和用户协作 |
| 5 | `docs/zh/nuwa-plan.md` | 女娲计划完整愿景 | 理解所有子项目的终极目标 |

**公众号写作会话额外读**：人设档案 + experience.jsonl + 系列 lessons.md + 已发文章（详见 MEMORY.md 的 startup-guide）

## 核心工程公理

### 🔴 修根因，不修症状（Root Cause Fix Axiom）

**发现问题时，必须追溯到生产该输出的代码/配置/prompt，修那里。直接修输出文件是无效的——下次生产还会犯同样的错。**

检查清单：
1. 这个错误是哪段代码/prompt 产出的？
2. 修了那段代码后，下次运行能自动产出正确结果吗？
3. 如果不能，还有更上游的根因没修到。

反例（禁止）：文章数据来源格式不对 → 手动编辑 article_mdnice.md → ❌ 下篇文章还会错
正例（要求）：文章数据来源格式不对 → 修 pass4_integrate.md prompt → 修 engine.py 后处理 → ✅ 下篇自动正确

**这条公理同时适用于女娲计划的所有子项目：永远修生成器，不修生成物。**

### 🔴 被动记忆无效，经验必须主动注入（Active Injection Axiom）

**教训写在文件里不等于"记住了"。Agent 在任务执行热区中会直奔代码，跳过记忆文件。被动存储的经验 = 不存在的经验。**

这是女娲计划的核心发现（2026-03-14，经历反复干预后提炼）：

**现象**：memory 文件明确写着"原创作者字段不用填"，但 Agent 调试时用了 6 种方法尝试填写该字段，全部失败。用户反复干预，大量人类心智被浪费。Agent 每次都"重新发现"已经记录过的教训。

**根因**：记忆是被动的（需要主动 Read 才能获取），但任务执行是贪心的（直奔目标，跳过回忆步骤）。这等价于：**压缩后的经验没有被注入到决策路径中**。

**定理**：经验的价值 = 经验的质量 × 被调用的概率。被动存储的调用概率趋近于 0，所以价值趋近于 0，无论质量多高。

**公理（解决方案）**：
1. **经验必须可执行** — 不是"记在某处"，而是"触发时自动注入"。Skill 机制（主动 prompt 注入）> 记忆文件（被动存储）
2. **执行前强制回忆** — 每个高风险操作域（发布、调试、写作）都应有对应 Skill，Skill 的第一步是强制读取该领域的经验文件
3. **失败模式必须代码化** — 如果某个错误发生过，防止它的逻辑应该写进代码（删掉 author 填写逻辑），而不是写进"注意事项"让 Agent "记住不要做"

**与女娲计划的关系**：这直接映射到公理注入理论——"注入元规则，而非知识"。被动记忆 = 注入知识（需要 Agent 主动检索），主动注入 = 注入元规则（自动约束 Agent 行为）。Raphael 的经验压缩回母体后，如果只是存档而不改变母体的决策逻辑，则学习无效。

**检查清单**：
1. 这个教训是写在被动文件里，还是已经注入到 Skill / 代码逻辑中？
2. 下次遇到同类问题时，Agent 能否**不需要人类提醒**就自动调用这个经验？
3. 如果不能，把它变成 Skill 的强制步骤或代码中的硬约束。

**已实施的 Skill**：
- `/publish-wechat`（`.claude/skills/publish-wechat/SKILL.md`）— 发布前强制读发布经验 + UI 调试铁律
- `/analyze`（`.claude/skills/analyze/SKILL.md`）— 分析前强制定框架

### 🔴 最少心智投入公理（Minimum Cognitive Load Axiom）

**每个自动化流程的设计目标是最小化人类认知触点。人类应只在不可替代的判断点介入（审美、价值观、战略决策），所有可代劳的感知、验证、修复都必须由 AI 完成。如果人类需要"检查 AI 的工作"，说明系统设计失败。**

这是女娲计划的核心原则——"剔除人的心智"——在工程实践中的具体要求（2026-03-14，公众号发布管线实践中提炼）。

**现象**：Agent 完成发布脚本后报告"验证通过"，但验证方式是读 DOM 返回值（JSON），从未用人类会用的方式（打开草稿箱→预览→逐项检查）验证。用户去浏览器检查时发现编辑器页面都不在了。每次"验证通过"都是谎言，用户反复被骗后信任崩塌。

**根因**：Agent 把自动化脚本当作终点，没有把它当作用户工作流的一个环节。脚本完成后用户需要接手——但 Agent 从未考虑用户接手时需要什么。本质上是**把验证成本转嫁给人类**。

**公理（解决方案）**：
1. **用人类的方式验证** — 不是检查代码返回值，而是走人类会走的路径（打开页面、看预览、逐项对比）。如果你不会把这个截图发给朋友说"你看没问题吧"，那这个验证就不够。
2. **发现问题自己修** — 验证发现问题时，不报告给用户让用户决定怎么办，而是自己修复、重新验证，直到确信没问题。
3. **只在决策点交付** — 交给用户的应该是一个决策（"发/不发"），不是一个检查任务（"你看看对不对"）。
4. **交接状态必须可用** — 脚本结束后，浏览器/环境的状态应该是用户能直接操作的（如：停在草稿预览页面），而不是需要用户自己导航。

**检查清单**：
1. 这个流程结束后，用户需要做什么？我能替用户做掉哪些？
2. 用户拿到交付物后，是否需要"检查"才能信任？如果需要，验证还不够。
3. 流程结束时的环境状态，用户能否直接开始下一步操作？

**与女娲计划的关系**：这直接映射到核心论述——"现有的 agent 依然以人的心智为燃料驱动，人注入多少心智，agent 运转就有多有效"。每一次让用户"检查一下"，就是在消耗人的心智燃料。真正的数字生命应该像细胞分裂一样自主运转，人类只在需要"意志"的时刻介入。

---

## 干预日志（循环2种子）

**暗号**：用户说"记下这次干预"（或"记一下干预"、"log intervention"等类似表达），立刻追加一条到对应子项目的 `logs/interventions.jsonl`（公众号→`wechat/logs/`，女娲→`logs/`）。

**格式**：
```json
{"timestamp": "ISO 8601", "action": "一句话描述干预", "target": "改的系统部分", "trigger": "为什么改"}
```

**作用**：记录用户对循环1的每次"能力升级"操作（加信息源、建人设、改配置、造工具、调权重等）。不预设分类，跑几周后聚类，让循环2结构涌现。

## Claude 协作协议

详见 [`docs/claude-collaboration-protocol.md`](docs/claude-collaboration-protocol.md)。

### 核心要点

- **每次新会话**：先 fetch Notion 主控台（`305994d0-2404-81ce-b838-cca0a4a28e3a`）+ 认知热缓存
- **写入**：实质性对话后写每日 Log；用户触发时写项目推进 Log / 参考资料；新认知自动追加认知热缓存
- **沟通风格**：代号麦老，INTJ 式直接逻辑驱动，补盲点挑假设，不迎合不鸡汤
- **行为检测**：选择过载、规划逃避执行、报复性熬夜等模式，主动干预
