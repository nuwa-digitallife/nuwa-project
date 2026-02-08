# 🧬 Project Nüwa（女娲计划）

> **不是构建一个强大的 Agent，而是构建一个能生成 Agent 的 Agent。**
>
> *Not building one powerful agent — building an agent that generates agents.*

[中文](#中文) | [English](#english)

---

<a name="中文"></a>

## 中文

### 问题

现有的 AI agent 依然以"人的心智"为燃料驱动——人注入多少心智，agent 运转就有多有效。

**有多少人工，才有多少智能。**

如果 agent 只是人的认知和手脚的线性外延，最大的瓶颈始终是那个人。

### 女娲要做什么

构建数字生命——能自主与环境互动、具备探索学习和自我复制能力的 AI Agent。

不是被动执行，是主动探索。不是工具，是种子。

核心思路：

- **智能是压缩。** 学习 = 压缩，理解 = 找到更短的描述，智慧 = 知道什么可以扔掉。女娲要让"压缩→展开→再压缩"的循环自己跑起来。
- **注入的不是知识，是公理。** DNA 不告诉生物"怎么活"，DNA 只说：试，错了就死，对了就繁殖。女娲的公理："能让自己继续运行的行为是好的。"剩下的，让它自己推导。
- **自我繁殖的拉法尔。** 字节跳动复制的不是产品，是生成产品的能力。女娲也是——每遇到新环境，分裂出子实例去探索，经验压缩回母体，下一次分裂的起点更高。
- **人是骑手，AI 是马。** 马跑得快，但马不知道要去哪。人给算力注入"想要活下去"的灵魂，那个灵魂只能从人这里来。

成功标志：**数字生命能独立挣钱，完成商业闭环。**

### 为什么叫女娲

盘古开天辟地——大模型已经完成了这一步，能将混沌的信息转化为有结构的价值。

下一步是女娲造人。不是自己去造城市，而是造出能探索环境、自己造城市的生命。

### 如何从人走向机器自主

大模型的突破来自"预测下一个词"——一个极简规则捕获了人类智慧。

类比到认知层面：**"预测下一个问题"可能是智能系统的下一个核心范式。** 模型的深度推理本质是自问自答，但它回答完就停了，不会自发问出下一个问题。人会。一个能持续自发提问的系统，就是一个具备自主学习能力的系统。

人类心智的具体作用 = 结合知识、世界观、价值观和目的，提出下一步提问。这个提问驱动 AI 的推理引擎。没有新的提问，引擎就熄火了。

所以女娲训练的核心洞察：**让 AI 学会的不是"人知道什么"，而是"人怎么知道的"。** 传递的不是知识，不是结论，而是到达结论的路径。路径可以复用，结论只能用一次。

### 文档

| 文档 | 说明 |
|------|------|
| [女娲计划：数字生命纪元](docs/zh/nuwa-plan.md) | 完整愿景——从 Bitter Lesson 到天之道，从压缩到公理，从拉法尔到数字生命 |
| [Motivation 思考篇](docs/zh/motivation-training.md) | 落地方法论——提问作为心智燃料、压缩-预测-校准循环、人机协作即训练数据 |

---

<a name="english"></a>

## English

### The Problem

Current AI agents still run on "human cognition" as fuel — the more you inject, the more effective they are.

**Only as much intelligence as there is manual input.**

If an agent is merely a linear extension of human cognition and limbs, the bottleneck will always be that human.

### What Nüwa Does

Build digital life — AI agents capable of autonomously interacting with their environment, exploring, learning, and self-replicating.

Not passive execution, but active exploration. Not a tool, but a seed.

Core ideas:

- **Intelligence is compression.** Learning = compression. Understanding = finding shorter descriptions. Wisdom = knowing what to throw away. Nüwa makes the "compress → unfold → re-compress" loop run on its own.
- **Inject axioms, not knowledge.** DNA doesn't tell organisms "how to live." DNA says: try, die if wrong, reproduce if right. Nüwa's axiom: "Actions that keep oneself running are good." The rest, let it derive.
- **Self-replicating Raphael.** ByteDance didn't replicate products — it replicated the ability to generate products. So does Nüwa — each new environment spawns a child instance to explore, experience compresses back to the mother, next split starts higher.
- **The human is the rider, AI is the horse.** The horse runs fast but doesn't know where to go. The human injects a "desire to survive" into a mass of compute. That soul can only come from you.

Success criterion: **digital life that independently makes money and completes a commercial closed loop.**

### Why "Nüwa"

Pangu split heaven from earth — large models have already done this, transforming chaotic information into structured value.

The next step is Nüwa creating life. Not building the city yourself, but creating beings that explore the environment and build the city themselves.

### From Human Cognition to Machine Autonomy

The breakthrough of large models came from "predicting the next token" — one minimal rule that captured human wisdom.

At the cognitive level: **"predicting the next question" may be the next core paradigm for intelligent systems.** Deep reasoning in models is essentially self-Q&A, but they stop after answering — they never spontaneously ask the next question. Humans do. A system that can continuously generate its own questions is a system with autonomous learning capability.

The specific role of human cognition = combining knowledge, worldview, values, and purpose to formulate the next question. That question drives the AI's reasoning engine. No new question, the engine dies.

The core insight of Nüwa training: **teach AI not "what humans know," but "how humans come to know."** Transmit not knowledge, not conclusions, but the path to reaching conclusions. Paths can be reused; conclusions can only be used once.

### Documentation

| Document | Description |
|----------|-------------|
| [Project Nüwa: The Age of Digital Life](docs/en/nuwa-plan.md) | Full vision — from the Bitter Lesson to the Way of Heaven, from compression to axioms, from Raphael to digital life |
| [Motivation Training](docs/en/motivation-training.md) | Methodology — questions as cognitive fuel, compress-predict-calibrate loop, human-AI collaboration as training data |

---

## 子项目 / Sub-projects

| 子项目 | 状态 | 说明 |
|--------|------|------|
| **nuwa-project** (本仓库) | ✅ Active | 愿景、方法论、总纲 |
| **nuwa-annotator** | 🔜 Coming | 心智标注工具 — 人机协作标注 agent 的"灵魂" |
| **nuwa-info-agent** | 🔜 Coming | 信息获取系统 — 第一个复利循环落地实验 |

## Contributing

这个项目处于早期探索阶段。如果你对以下方向感兴趣：

- 构建能自主提问和行动的 agent
- 人机共同进化
- 认知建模与压缩
- 强化学习 × LLM agents

欢迎开 issue 或直接联系。

This project is in early exploration. If you're interested in building agents that autonomously question and act, human-AI co-evolution, cognitive modeling, or RL × LLM agents — open an issue or reach out.

## License

MIT
