# 全行业盯了两年的编程能力榜，今天退役！OpenAI 停用 SWE-bench Verified：未来标准将看 AI 能顶替多少程序员？

- 来源: InfoQ
- 时间: 2026-02-24 14:20
- 链接: https://mp.weixin.qq.com/s/JyX0Jfo90lUxR9yhvwYUKQ

## 摘要

代码模型榜单接下来要回答的，不是“能不能再高一分”，而是“能不能真的把一部分人类工作接过去”？！

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/hLLZnAbUwNgKyk5kRaLNfdDbFWazBicfaxKGRVgytF8y8ochgcvnoeOv74WT7EPIAEvD3ugyIs9YlOQVHBicHZtMwsAHFnTRI2Vw0piccgtej8/0?wx_fmt=jpeg)

全行业盯了两年的编程能力榜，今天退役！OpenAI 停用 SWE-bench Verified：未来标准将看 AI 能顶替多少程序员？
===================================================================

原创 Tina Tina [InfoQ](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/sz_mmbiz_png/YriaiaJPb26VOyok8AFzdI1dYk5y1nMIvCKpHVPxxATHib8NuRaxgatxGCAiaBhDFhKLbcPMmCN2Be7Er2uniaOrs4A/640?wx_fmt=png&from=appmsg)

![](https://mmbiz.qpic.cn/mmbiz_gif/YriaiaJPb26VPQqHC66RJFpttVIMWG83T3lWHahUD4bvhxlKSayjeV2ibvC5ydqklP9QHDPD3qHJM07TV3IfHstjA/640?wx_fmt=gif)

编译 | Tina

过去两年，行业几乎都盯着同一张榜单追分、比排名、算差距；但从今天起，这套玩法可能要告一段落了。

今天，OpenAI 正式宣布 SWE-bench Verified“退役”。几小时前，OpenAI 的开发者账号发推明确表示：SWE-bench Verified 将逐步退出舞台，已不再适合作为前沿编程模型的主要对标基准；官方更建议大家转向 SWE-bench Pro。

![](https://mmbiz.qpic.cn/mmbiz_jpg/hLLZnAbUwNhibqXbUibt06v0QzF1BQ5PaKzhIO3v2fgV3qZjXpXzszUT6sOiasiciae7vBvpG657Gt6x0T8pxkibKvlr4XLdIptPQlsgS4ERphe9A/640?wx_fmt=jpeg&from=appmsg)

SWE-bench Verified 曾经几乎就是代码评测的“北极星”。OpenAI、Anthropic、Google，包括不少国内开源权重模型，都在同一张榜单上咬得很紧，领先优势往往只差零点几。

但 OpenAI 在最新分析中指出：剩余未解决任务本身存在多重问题，已经不值得继续追求、更不值得继续公布 Verified 成绩。其中最严重的一点是数据污染——几乎所有前沿模型（包括 OpenAI 自己的模型）如今都表现出“复现 SWE-bench 评估数据与解法”的能力，有时甚至只凭任务 ID 就能做到：

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNgAJEQMyuwJIe5CoHlcc3CqjHvVxV390RdJ3WZqJ7icOPbC9mVSEwBlicGFhg9Poq9UEo2xNymyq8d5RCD8GGHRKYuCbiaezJkicyM/640?wx_fmt=png&from=appmsg)

另一个原因则更“直白”：测试设计本身就不够可靠。OpenAI 认为，至少有 60% 的未解决问题，从题面描述出发就应该是无法被正确解决的——如果某个模型“解决了它们”，更可能意味着绕过了评测机制（也就是在“刷题 / 作弊”）。他们举的例子之一，是 SWE-bench 中针对 pylint 问题 #4551 的测试用例。

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNjj1wY9j1AqWdN5c4552BbFVS8GY9QEvZgYksbTTtIQMN9Ffdqs2LZ34D9g72CzYsziauYAnXFMnJqpB0FD47g1yUK6wnHaU4TM/640?wx_fmt=png&from=appmsg)

今天，Latent.Space 邀请了 OpenAI 的 Frontier Evals 团队一起解读了这次榜单更迭的原因，并对比了两个新旧不同测评榜的差异。

SWE-bench Verified 题目规模偏小、任务周期过短，90% 的问题对资深工程师来说一小时内就能完成。而 SWE-bench Pro（SuperBench Pro）的题目更大、更难、任务时间被明确拉长到“数小时甚至更久”，覆盖的仓库、语言和问题类型也明显更丰富；更重要的是，目前它还没有被刷爆，污染迹象远低于 Verified，至少在现阶段仍然能区分真实能力差异。

并且 Pro 也不是终点。任何公开榜单，最终都会被追平、被记住、被“学会”，然后再次失效。OpenAI 认为，关键不在于“换哪个榜”，而在于下一代代码评测到底该测什么——他们更希望看到真实世界使用层面的指标：**AI 在现实中到底被用了多少、在多大程度上替代了人类工作、又在多大程度上是在增强人类、加速人类。**

这个事件的意义，正如一位网友所说：“排行榜的噱头已经过时了！如今的优势在于溯源性、对抗性强的评估以及在生产环境中值得信赖的 Agent”。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/hLLZnAbUwNg3M3tUwwcoicYTyWZtTPeBHbibX2peibmm9WYUVYbrcrWbLPaaibZEF4tN9icMUhv585WqbXHDP9OFIhIkiaF0C0DWicL5x7f9vGY7p0/640?wx_fmt=jpeg&from=appmsg)

这期嘉宾是 OpenAI 的 Olivia Watkins（Frontier Evals 团队）和 Mia Glaese（OpenAI 研究副总裁）。我们整理了这期播客的核心内容，供你快速了解这场“退役 + 换标”背后的关键逻辑。

1 SWE-be

...(截断)
