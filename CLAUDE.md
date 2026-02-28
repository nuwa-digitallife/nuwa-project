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

## 干预日志（循环2种子）

**暗号**：用户说"记下这次干预"（或"记一下干预"、"log intervention"等类似表达），立刻追加一条到 `logs/interventions.jsonl`。

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
