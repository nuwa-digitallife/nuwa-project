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

## Claude 协作协议（必读）

**打开项目后必须先读** [`docs/claude-collaboration-protocol.md`](docs/claude-collaboration-protocol.md)。

### 为什么必读

这份协议是作者（Ciwang）个人认知、原则、行为模式的持续压缩产物。它同时也是女娲计划 Soul 层（公理记忆）的现实原型——作者本人就是第一个被压缩的「心智样本」。

读懂这份协议，你就能：
1. **按作者的原则协同**，而不是每次从零磨合——减少协同摩擦成本
2. **减少人的心智投入**——不需要每次重复解释偏好、风格、禁区
3. **理解女娲的设计意图**——协议本身就是「公理注入 + 记忆分层 + 压缩」的活体实验

### 核心要点

- **每次新会话**：先 fetch Notion 主控台（`305994d0-2404-81ce-b838-cca0a4a28e3a`）+ 认知热缓存
- **写入**：实质性对话后写每日 Log；用户触发时写项目推进 Log / 参考资料；新认知自动追加认知热缓存
- **沟通风格**：代号麦老，INTJ 式直接逻辑驱动，补盲点挑假设，不迎合不鸡汤
- **行为检测**：选择过载、规划逃避执行、报复性熬夜等模式，主动干预
