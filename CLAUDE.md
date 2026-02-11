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
