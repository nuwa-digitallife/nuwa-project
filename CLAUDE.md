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

### 🔴 Agent LLM 选型下限：sonnet

任何需要"思考"的步骤（文件定位、编辑生成、意图分类等）至少用 sonnet。haiku 判断力不够，省的 token 不值返工成本。

### 🔴 性能问题修根因，不截断

prompt 太长导致 LLM 慢 → 找哪个文件/内容不该被加载，而不是一刀切截断所有文件。截断是掩盖问题，定位多余输入才是根因。

### 🔴 四要素链路（子项目运转公理）

**每个子项目由四个要素驱动，必须对齐、可追溯。断链 = 瞎搞。**

```
方法论 → 执行计划 → 流程 → 产物
 (为什么/怎么做)  (做什么/优先级)  (谁来执行/代码)  (输出什么/在哪)
```

| 要素 | 定义 | 文件形态 | 改动频率 |
|------|------|---------|---------|
| **方法论** | 质量标准、评估维度、铁律。是"宪法" | `方法论.md` / `内容方法论.md` | 低（公理层） |
| **执行计划** | 当前目标、优先级、里程碑、阻塞项。是"作战地图" | `AUTOMATION_PLAN.md` | 高（每次会话可能更新） |
| **流程** | 执行计划的代码/工具/技能。计划的"手脚" | 代码文件 + `skills/` | 中（开发时改） |
| **产物** | 流程的输出物。计划的"交付件" | 作品、日志、数据库等 | 每次执行产生 |

**对齐规则**：
- 执行计划中每个任务必须写明：用哪条方法论 → 走哪个流程 → 产出什么文件
- 流程（代码）必须能追溯到计划中的某个任务
- 产物必须能追溯到流程中的某个步骤
- 方法论变更 → 必须检查下游流程和计划是否需要同步更新

**各子项目的四要素位置**：

| 子项目 | 方法论 | 计划 | 流程 | 产物 |
|--------|--------|------|------|------|
| 公众号 | `wechat/内容方法论.md` | `wechat/tools/AUTOMATION_PLAN.md` | `wechat/tools/` | `wechat/公众号选题/` |
| 文学外包 | `wechat/文学外包/文学方法论.md` | `wechat/文学外包/AUTOMATION_PLAN.md` | `wechat/文学外包/agent/skills/` | `wechat/文学外包/作品/` + `已投稿/` |
| 金融管家 | `qqinvest/金融管家/方法论.md` | `qqinvest/金融管家/AUTOMATION_PLAN.md` | `qqinvest/金融管家/monitor.py` + `db.py` + `app.py` | `qqinvest/金融管家/market.db` |

**自主模式的特殊要求**：Agent 每日自动运营前，必须读计划确认当前目标和优先级，读方法论确认质量标准。不读就写 = 无根之木。

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
