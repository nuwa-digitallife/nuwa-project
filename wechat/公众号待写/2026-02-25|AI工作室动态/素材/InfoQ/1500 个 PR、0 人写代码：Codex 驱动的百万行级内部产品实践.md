# 1500 个 PR、0 人写代码：Codex 驱动的百万行级内部产品实践

- 来源: InfoQ
- 时间: 2026-02-24 15:35
- 链接: https://mp.weixin.qq.com/s/HTGvy5C6SYyr5XQhTfTfzw

## 摘要

OpenAI 内部实验：构建 100% 由 Agent 生成、无人工代码的软件系统。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/hLLZnAbUwNiaftjrQIo974lgn3ZlNQvoypXoC4fcibhRRL9pbceibA8ZdUvlj4RtueBvsqWmITibgWibgD6K51Pm7ZobjZ7ZjHB9JUXUMkhkiaWkc/0?wx_fmt=jpeg)

1500 个 PR、0 人写代码：Codex 驱动的百万行级内部产品实践
====================================

[InfoQ](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/mmbiz_gif/YriaiaJPb26VPQqHC66RJFpttVIMWG83T3lWHahUD4bvhxlKSayjeV2ibvC5ydqklP9QHDPD3qHJM07TV3IfHstjA/640?wx_fmt=gif)

作者 | Ryan Lopopolo

译者 | 田橙

策划 | Tina

在过去的五个月里，我们团队进行了一项挑战：开发并发布一款完全没有人工编写代码的内部测试产品。

目前，该产品已经拥有内部日活用户和外部 Alpha 测试人员。它在真实的开发环境中运行、部署、报错并接受修复。其独特之处在于，从应用逻辑到测试脚本，再到 CI 配置、文档、可观测性及内部工具，每一行代码都出自 Codex 之手。据我们估算，这种开发模式的效率极高，耗时仅为手动开发代码的 10%。

**人类掌舵，Agent 执行。**

我们特意设定了这个限制，就是想看看工程效能能否实现量级上的突破。当时我们需要在短短几周内交付上百万行代码，这迫使我们必须重新思考：如果工程师不再把“写代码”当成主业，而是转去设计环境、定义意图并构建反馈循环，好让 Codex Agent 产出可靠的成果，那么研发模式到底会发生什么变化？

在这篇文章中，我们将分享通过 Agent 团队构建全新产品的心得，包括哪些尝试失败了，哪些产生了复利效应，以及如何最大化利用我们最宝贵的资源：人类的时间与注意力。

从空仓库起步

2025 年 8 月底，我们向这个空仓库提交了第一次 Commit。

初始脚手架由 Codex CLI 调用 GPT-5 生成，并辅以少量现有模板作为引导，涵盖了仓库结构、CI 配置、格式化规则、包管理器设置以及应用框架。甚至连指导 Agent 如何在仓库中工作的初始 AGENTS.md 文件，也是由 Codex 亲笔完成。

这里没有任何预存的人工代码来作为系统的“锚点”。从一开始，整个仓库的形态就是由 Agent 塑造的。

五个月后，该仓库已拥有约 100 万行代码，涵盖应用逻辑、基础设施、工具链、文档和内部开发组件。在此期间，一支仅有 3 名工程师的小团队驱动 Codex 开启并合并了约 1500 个 PR。这意味着平均每位工程师每天产出 3.5 个 PR。令人惊讶的是，随着团队扩大到 7 人，人均产出率反而进一步提升。

更重要的是，这并非为了刷量而产出：该产品已被数百名内部用户使用，其中包括每天重度使用的核心用户。在整个开发过程中，人类从未直接贡献过任何一行代码。这成了团队的核心哲学：**拒绝人工编写代码。**

重新定义工程师的角色

由于不再亲自动手写代码，工程师的工作重心转向了系统设计、脚手架搭建和杠杆效能。

早期的进展比预期要慢，这并非因为 Codex 能力不足，而是因为环境的“规范度”不够。Agent 缺乏实现高层目标所需的工具、抽象和内部结构。于是，工程团队的首要任务变成了：赋能 Agent 开展有效工作。

在实践中，这意味着采用深度优先的工作方式：将宏大目标拆解为微小的构建块（设计、代码、评审、测试等）。驱动 Agent 构建这些块。利用这些已有的块去解锁更复杂的任务。当任务失败时，修复方案几乎从不是“再试一次”。因为必须通过 Codex 来推进工作，人类工程师会介入并思考：“缺失了什么能力？我们如何让这种能力对 Agent 而言既清晰可见又强制执行？”

人类与系统的交互几乎完全通过 提示词 完成：工程师描述一项任务，运行 Agent，并授权其开启一个 Pull Request。为了推进 PR 最终合入，我们会指示 Codex 在本地审查自己的代码改动，并请求其他特定的 Agent（无论是在本地还是云端）进行交叉评审。Codex 会根据人类或 Agent 给出的反馈进行响应，并在循环中不断迭代，直到所有 Agent 评审员都感到满意——这实际上形成了一个所谓的 “拉尔夫·维格姆循环”（Ralph Wiggum Loop）【见译注】。Codex 直接调用我们的标准开发工具（如 GitHub CLI gh、本地脚本以及集成在仓库中的技能），自主获取上下文，无需人类手动在命令行中复制粘贴。

译注：Ralph Wiggum Loop：这是一个来自《辛普森一家》的梗（那个坐在教室后面自言自语的小男孩），在软件工程语境下，通常指代一种“自给自足、闭环且带有某种幽默色彩的自推导循环”。

虽然人类可以审查 PR，但这并非强制要求。随着时间的推移，我们已将几乎所有的评审工作都交给了 “Agent 对 Agent” 的协作模式。

增加应用的“可读性”

随着代码产出率的提升，我们的瓶颈变成了人类的 QA 能力。由于人类的时间和注意力始终是唯一的稀缺资源，我们致力于通过让应用 UI、日志和指标对 Codex 直接可见且可理解，从而为 Agent 增加更多能力。

例如，我们使应用能够针对每个 Git 工作树（worktree）独立启动，这样 Codex 就可以为每一次代码变更运行并驱动一个实例。我们还将 Chrome DevTools Protocol 接入 Agent 运行时，并创建了处理 DOM 快照、截图和导航的技能。这使得 Codex 能够直接复现 Bug、验证修复结果并推导 UI 行为。

![此处输入图片的描述](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNia5U9njVMnZlNh3Mty4D5erfgEGWbd2JuyicjqYmHF6lVk

...(截断)
