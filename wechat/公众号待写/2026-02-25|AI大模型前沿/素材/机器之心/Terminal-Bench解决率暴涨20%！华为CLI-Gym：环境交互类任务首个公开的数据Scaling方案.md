# Terminal-Bench解决率暴涨20%！华为CLI-Gym：环境交互类任务首个公开的数据Scaling方案

- 来源: 机器之心
- 时间: 2026-02-23 12:01
- 链接: https://mp.weixin.qq.com/s/ty1gzYIV_CpRkKLBbJSsMg

## 摘要

CLI-Gym 是第一种用于扩展 CLI 代理编码任务训练环境的公开方法。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/5L8bhP5dIqG7829zTa2Sic4NehT5exuj9nw0YhRNNBa2vjuwh2Zm6IvYCAvoibfaQdHJo0PYdxIvWTXyV8SOeYvAkoJHgQT6dee01ln5teHBs/0?wx_fmt=jpeg)

Terminal-Bench解决率暴涨20%！华为CLI-Gym：环境交互类任务首个公开的数据Scaling方案
========================================================

[机器之心](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/sz_mmbiz_png/KmXPKA19gWic1GuW68DykycvknmG9tyBv6ax8e99N0eyLy4Qo7OzKR5sgwWkpGv1vxoygrqI14ssGoXb90ibG6Jw/640?wx_fmt=png&from=appmsg)

  

「首个公开的面向 Terminal-Bench 环境交互类任务的数据规模化生产管线正式发布！」

*   开源完整自动化数据构建算法
    
*   构建 1655 个高可靠 CLI 任务环境镜像
    
*   通过 291 条轨迹数据带来 20% 解决率提升
    

  

在 Agentic Coding 领域，基于 SWE-bench 的数据管线研究已取得长足进展。过去一年中，业界涌现了大量相关工作，例如 SWE-Gym、SWE-Smith 和 R2E-Gym 等，极大推动了以代码生成为核心的 Agentic Coding 发展，也使得当前最先进的开源模型与闭源模型之间的表现差距显著缩小。然而，对于更广泛的环境交互类问题（如 Terminal-Bench 所涵盖的任务），目前尚没有公开的高效和可规模化的数据生产方案，导致相关数据构建困难重重，高度依赖人工参与，这已然成为制约该方向发展的瓶颈，也使得在相关任务上开源模型的表现大幅落后于闭源模型。

  

![](https://mmbiz.qpic.cn/mmbiz_png/5L8bhP5dIqFWNpSZ5mFOUIlmJgAHRzX8CkibYShvtgrfiaZOs8c20GdshXDtIXkpianYTQkRiaCv9myJgxGLAKoJD9iaSsDRqA2BkJQyiaCicibaJHE/640?wx_fmt=png&from=appmsg)

  

因此 CLI-Gym 来了！我们首先尝试用 Dockerfile 对环境进行结构化与可复现定义；进一步，将数据生产管线本身重新建模为一种 Agentic Coding 任务：在健康环境中驱动 Code Agent 执行环境反演（即 “劣化” 操作），自动生成问题环境及其准确的单元测试，从而实现问题实例与验证工具的自动化构造。我们在 29 个基础镜像上制造出 1655 个针对 Terminal-Bench 实例并产出 291 条高质量成功轨迹，我们的微调模型 LiberCoder 32B 和 235B 在 Terminal Bench 上分别实现了 + 28.6%（至 38.9%）和 + 21.1%（至 46.1%）的提升。

  

我们的管线创新性地以 Codebase、Dockerfile 与 Base Image 为核心抽象，完备地定义任意 CLI Coding 实体，使环境构建、问题生成与验证机制形成统一表达框架，具备良好的可组合性与通用性。我们希望这一范式能够进一步拓展至更多 Agentic Coding 场景，推动更通用的数据生产算法与基准构建方法的发展。

  

![](https://mmbiz.qpic.cn/sz_mmbiz_png/5L8bhP5dIqFP2zMkzFQNrlhMFQm7acyuppT9nTxn0dVUJHKxD2QBiaWhCzTOnDuicL7Psl6ralyEMLtktvBenPM7wW0SFYSicRuMwWz8h7JZ4o/640?wx_fmt=png&from=appmsg)

  

论文、代码和镜像数据均会在如下链接放出：

  

*   论文链接：https://arxiv.org/pdf/2602.10999
    
*   开源代码：https://github.com/LiberCoders/CLI-Gym
    
*   镜像数据：https://huggingface.co/datasets/LiberCoders/CLI-Gym
    

  

背景介绍

  

近年来，Agentic Coding 正在快速改变软件工程任务的解决方式，模型能力的边界正在从 “写代码” 逐渐扩展为 “解决真实软件系统中的复杂问题”。当前的研究重点还停留在以 SWE-bench 为核心的的代码层面的研究，而在现实的软件工程和系统运维场景中，大量问题并非源于代码本身，而是来自运行环境，例如依赖版本冲突、环境变量错误、权限配置问题、系统库损坏、网络配置错误等。这类问题通常无法或很难通过修改代码修复，而必须依赖 agent 通过命令行理解系统状态，定位问题来源，并执行一系列系统级操作恢复环境运行状态。因此，对 agent 的环境理解与干预能力的要求越来越高。

  

Terminal-Bench 的任务恰好契合这一需求。其基准中包含大量以环境修复为核心目标的任务，对 agent 在 CLI 环境下的交互、诊断与修复能力提出了更高要求。然而，从当前官方 leaderboard 可以观察到，高性能方案往往依赖围绕强闭源模型构建的复杂 agent 框架，通过大量提示工程与多轮反思机制来弥补模型在环境理解与问题定位方面的能力不足。相比之下，围绕开源模型如何通过系统性训练提升其环境修复能力的研究仍然相当有限。

  

其根本瓶颈在于：环境密集型任务难以规模化生成。代码类问题可以通过挖掘仓库历史与 pull request 自动构建训练数据，但环境状态通常缺乏可追溯的演化记录，难以进行自动化重建与标注。这使

...(截断)
