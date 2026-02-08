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

### 文档

| 文档 | 说明 |
|------|------|
| [女娲计划：数字生命纪元](docs/zh/nuwa-plan.md) | 完整愿景——从 Bitter Lesson 到天之道，从压缩到公理，从拉法尔到数字生命 |
| [Motivation 思考篇](docs/zh/motivation-training.md) | 落地方法论——提问作为心智燃料、压缩-预测-校准循环、人机协作即训练数据 |

### 进度

- [x] 核心愿景文档
- [x] Motivation 层方法论
- [x] 与 Claude 共建心智结构模型的实践验证
- [ ] 信息获取系统（第一个复利循环入口）
- [ ] 心智标注工具
- [ ] Agent 内核原型

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

### Documentation

| Document | Description |
|----------|-------------|
| [Project Nüwa: The Age of Digital Life](docs/en/nuwa-plan.md) | Full vision — from the Bitter Lesson to the Way of Heaven, from compression to axioms, from Raphael to digital life |
| [Motivation Training](docs/en/motivation-training.md) | Methodology — questions as cognitive fuel, compress-predict-calibrate loop, human-AI collaboration as training data |

### Progress

- [x] Core vision document
- [x] Motivation layer methodology
- [x] Practical validation: co-building cognitive structure models with Claude
- [ ] Information acquisition system (first compound-interest loop entry point)
- [ ] Cognitive annotation tool
- [ ] Agent kernel prototype

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
