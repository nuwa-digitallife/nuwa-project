# MiniMax 成为 Token 调用第一后，模型厂商必须面对的 AgentOS 现实

- 来源: InfoQ
- 时间: 2026-02-23 17:25
- 链接: https://mp.weixin.qq.com/s/0vAWHzlEZnhZYolHTvM1bg

## 摘要

AgentOS友好的LLM，是模型厂商的下一个战场

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/hLLZnAbUwNia1Z9IDlZoZKNnogQB5icXtLmAib4b557yF6W9ib2AV6Hfn86KLnb1NG8GgWicXLBI4C9fia1khSUVb6JibBicHTRJOZiaGicVmZgzwIHlQ/0?wx_fmt=jpeg)

MiniMax 成为 Token 调用第一后，模型厂商必须面对的 AgentOS 现实
===========================================

原创 姚戈 姚戈 [InfoQ](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/mmbiz_gif/YriaiaJPb26VPQqHC66RJFpttVIMWG83T3lWHahUD4bvhxlKSayjeV2ibvC5ydqklP9QHDPD3qHJM07TV3IfHstjA/640?wx_fmt=gif)

作者 | 姚戈

就在今年春节假期期间，OpenRouter 上出现了一组耐人寻味的数据变化。

![图片](https://mmbiz.qpic.cn/sz_mmbiz_png/hLLZnAbUwNgvibv3fW1EN4TnSZ3s9u1kfdQM0p7rrY0HEoW1fruJEgrNVOicsUs8vWPlM35ORv3juwNOevFBibtPtdxGuPAumT6XVNL2SA9ib54/640?wx_fmt=png&from=appmsg)作为目前全球最主要的大模型 API 聚合网关之一，**OpenRouter 的 Token 调用量在 2026 年 1 月下旬出现了明显跃升**。自 1 月 26 日当周开始，平台 Token 周增量首次突破 1.5T，这一幅度在过去的调用曲线中并不常见。时间点同样值得玩味——这一轮增长几乎与 OpenClaw 的迅速传播高度重合。人们开始发现，OpenClaw 简直就是 Token 碎纸机。

**2 月 13 日发布的 MiniMax M2.5，在上线不到一周内便迅速登顶 OpenRouter Token 调用榜首**。在 2 月 9 日至 2 月 15 日这一统计周期内，OpenRouter 的 Token 周调用量较此前一周激增 3.19T Tokens，其中仅 MiniMax M2.5 就贡献了 1.44T Tokens，调用规模超过 Kimi K2.5 、GLM-5、DeepSeek V3.2 的总和。

随后，OpenRouter 官方披露了另一项关键信号：过去数周内，平台长文本生成需求显著上升，在 100K 至 1M Token 区间，MiniMax M2.5 的调用量处于领先位置。这个 Token 区间正是 Agent 工作流中最具代表性的消耗范围。

从定价维度看，MiniMax M2.5 的确呈现出极具冲击力的成本结构：其每百万 token 的输入与输出单价分别低至 0.103 美元和 1.34 美元。作为对比，即便是以低价著称的 Kimi K2.5，其单价也达到了 0.254 美元和 2.84 美元，Gemini 2.5 Flash 为 0.278 美元和 3.00 美元，而 Claude Opus 4.6 更是高达 2.52 美元和 25.31 美元（以上数据均基于 2 月 23 日 OpenRouter 官网统计）。

然而，如果只将 M2.5 的调用激增理解为“价格驱动”，就很难看到数据背后的结构性变化。

从 MiniMax 此次在 OpenRouter 上的“异常波动”中可以看到，以 Openclaw 为代表的 AgentOS ，并非只是放大了 Token 消耗，它同时迫使模型厂商将 Agent 与 LLM 的关系视作基础设施问题。在这一意义上，M2.5 的增长也呈现出不同于传统模型竞争的特征：此前因成本过高或推理效率不足而难以落地的 Agent 场景，开始具备了现实可行性。

**当 AgentOS 成为 Token 的重要传输渠道，成为人和机器与 LLM 打交道的重要媒介，它必定会改变 LLM 厂商，对 LLM 技术架构的设计，甚至商业模式。**

AgentOS 来了

AgentOS 的兴起，本质上并不是产品类别的变化，而是对 LLM 使用方式的重构。

以 OpenClaw 为例，这个最初由 Peter Steinberger 在周末构建的“小玩具”，在短短数月内，演变为能直接操控本地文件系统的开源 Agent 内核。

尽管它的安全架构、工程设计仍遭人诟病，处于风暴的中心的 OpenClaw 依旧向科技行业证明了 AgentOS 这个概念的吸引力：行业快速接受了“模型直接参与操作系统级任务执行”这件事。

这意味着，大模型开始从“受限于云端沙箱的文本生成器”，转向“具备环境操作能力的执行节点”。模型的输出不再只是语言，而是可以通过工具链条转化为对真实系统状态的改变。

**更重要的是，AgentOS 让 Token 的 ROI 衡量更加明确了。**

在对话式产品中，Token 的消耗对应的是文本输出；而在 AgentOS 框架下，Token 的消耗可以直接转化任务结果。Token 从交互成本转变为行动成本，模型推理首次具备了可计量的现实产出。

**当 AgentOS 开始成为 Token 的主要传输渠道，并逐渐演变为人机交互与任务执行的重要媒介，大模型厂商面临的便不再只是模型能力问题，而是一次更底层的系统适配挑战：模型如何在复杂的执行环境中保持效率与稳定性？**

从模型架构与训练范式的角度看，这种变化至少带来了五个层面的影响。

第一，从“提示词工程”转向“系统级适配”。

Axiom Partners 的 AI 负责人在剖析 OpenClaw 开源代码后指出，其核心设计理念在于将智能体定义为磁盘上的文件集合，而非单纯的代码或需反复注入的提示词。记忆以 Markdown 文件的形式持久化存在于工作区中。

这一转变将智能体从一次性脚本升维为可版本控制的基础设施，进而倒逼模型厂商在构建 LLM 时，必须确保模型具备处理模块化、动态组装指令堆

...(截断)
