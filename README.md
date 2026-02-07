# 🧬 Project Nüwa（女娲计划）

> **Build AI agents that think, question, and evolve — not just follow instructions.**

[中文](#中文) | [English](#english)

---

<a name="中文"></a>

## 中文

### 这是什么？

女娲计划探索一种构建 AI Agent 的新路径：**不是编写指令让 AI 执行，而是将人类的心智内核注入 AI，让它学会像你一样思考和发问。**

当前 AI agent 的核心瓶颈不是能力不够，而是**不知道下一步该做什么**。任务完成后，它就停了。人类不会——人类会继续问。

我们认为：

> **"预测下一个问题"将像"预测下一个 token"一样，成为智能系统的核心范式。**

### 核心理念

1. **提问是心智燃料** — 问是认知的原子动作。AI 缺的不是答案能力，是发问能力。
2. **价值观 = 压缩后的反馈历史** — 不直接灌输结论，而是传递形成结论的路径。
3. **压缩-预测-校准循环** — 人类输出心智 → AI 压缩结构 → AI 预测下一个问题 → 人类校准 → 循环迭代。
4. **训练时压缩，推理时展开，运行时持续学习** — 从创造者这里提取种子内核，种子落到不同环境长出不同的行为。

### 文档

| 文档 | 说明 |
|------|------|
| [女娲计划：数字生命纪元](docs/zh/nuwa-plan.md) | 项目愿景与整体框架 |
| [Motivation 思考篇](docs/zh/motivation-training.md) | 心智注入的方法论、框架与落地实例 |

### 项目进度

- [x] 核心愿景文档
- [x] Motivation 层方法论（提问即心智燃料 + 压缩-预测-校准循环）
- [x] 与 Claude 共建心智结构模型的实践验证
- [ ] 信息获取系统（第一个落地的复利循环入口）
- [ ] 心智标注工具开源
- [ ] Agent 内核原型

### 为什么叫女娲？

女娲造人。她不是造了一个人然后让他复制自己——她创造了一个**能繁衍、能进化的物种**。

女娲计划的目标类似：不是造一个听话的 agent，而是造一个**有内核、能自主演化的数字生命种子**。

---

<a name="english"></a>

## English

### What is this?

Project Nüwa explores a new approach to building AI agents: **instead of writing instructions for AI to execute, we inject a human's cognitive kernel into the AI, teaching it to think and question like you do.**

The core bottleneck of current AI agents isn't capability — it's **not knowing what to do next**. After completing a task, they stop. Humans don't — humans keep asking questions.

We believe:

> **"Predicting the next question" will become a core paradigm for intelligent systems, just as "predicting the next token" drives large language models.**

### Core Principles

1. **Questions are cognitive fuel** — Questioning is the atomic action of cognition. What AI lacks isn't the ability to answer, but the ability to ask.
2. **Values = compressed feedback history** — Don't inject conclusions directly; transmit the path that formed those conclusions.
3. **Compress → Predict → Calibrate loop** — Human outputs raw thoughts → AI compresses into structure → AI predicts the next question → Human calibrates (yes/no/supplement) → iterate.
4. **Compress during training, expand during inference, learn continuously during runtime** — Extract a seed kernel from the creator. The seed grows differently depending on the soil it lands in.

### Documentation

| Document | Description |
|----------|-------------|
| [Project Nüwa: The Digital Life Epoch](docs/en/nuwa-plan.md) | Project vision and overall framework |
| [Motivation Training](docs/en/motivation-training.md) | Methodology, framework, and practical examples of cognitive injection |

### Progress

- [x] Core vision document
- [x] Motivation layer methodology (questioning as cognitive fuel + compress-predict-calibrate loop)
- [x] Practical validation: co-building cognitive structure models with Claude
- [ ] Information acquisition system (first compound-interest loop entry point)
- [ ] Open-source cognitive annotation tool
- [ ] Agent kernel prototype

### Why "Nüwa"?

Nüwa is the Chinese goddess who created humanity. She didn't create one person and tell it to copy itself — she created **a species capable of reproduction and evolution**.

Project Nüwa's goal is similar: not to build an obedient agent, but to create **a digital life seed with an inner kernel that can autonomously evolve**.

---

## 子项目 / Sub-projects

本组织下会逐步开源以下子项目：

| 子项目 | 状态 | 说明 |
|--------|------|------|
| **nuwa-project** (本仓库) | ✅ Active | 愿景、方法论、总纲 |
| **nuwa-annotator** | 🔜 Coming | 心智标注工具 — 人机协作标注 agent 的"灵魂" |
| **nuwa-info-agent** | 🔜 Coming | 信息获取系统 — 第一个复利循环落地实验 |

Sub-projects under this organization:

| Sub-project | Status | Description |
|-------------|--------|-------------|
| **nuwa-project** (this repo) | ✅ Active | Vision, methodology, master doc |
| **nuwa-annotator** | 🔜 Coming | Cognitive annotation tool — human-AI co-annotation of agent "soul" |
| **nuwa-info-agent** | 🔜 Coming | Information acquisition system — first compound-interest loop experiment |

## Contributing

This project is in its early exploration phase. If you're interested in:

- Human-AI co-evolution
- Cognitive modeling and compression
- Building agents that can autonomously question and act
- The intersection of reinforcement learning and LLM agents

Feel free to open an issue or reach out.

## License

MIT
