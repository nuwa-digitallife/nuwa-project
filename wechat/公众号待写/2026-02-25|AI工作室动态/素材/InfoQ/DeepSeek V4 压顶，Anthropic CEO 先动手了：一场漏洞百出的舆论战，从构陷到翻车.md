# DeepSeek V4 压顶，Anthropic CEO 先动手了：一场漏洞百出的舆论战，从构陷到翻车

- 来源: InfoQ
- 时间: 2026-02-25 15:42
- 链接: https://mp.weixin.qq.com/s/C-LxdjTLvWw7ic-CeUQxxA

## 摘要

这段时间，华尔街造了“新神”Anthropic。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/hLLZnAbUwNjkibk9PX2gYZDRcMNFiaYovSVV2fczJPHFKmiboibb0shQPN8D8jHBaEibVDwClYhcnscibtMalIHEzeyLX8HtGIZeUpB8zNEH8dhlE/0?wx_fmt=jpeg)

DeepSeek V4 压顶，Anthropic CEO 先动手了：一场漏洞百出的舆论战，从构陷到翻车
===================================================

[InfoQ](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/sz_mmbiz_png/YriaiaJPb26VOyok8AFzdI1dYk5y1nMIvCKpHVPxxATHib8NuRaxgatxGCAiaBhDFhKLbcPMmCN2Be7Er2uniaOrs4A/640?wx_fmt=png&from=appmsg)

![](https://mmbiz.qpic.cn/mmbiz_gif/YriaiaJPb26VPQqHC66RJFpttVIMWG83T3lWHahUD4bvhxlKSayjeV2ibvC5ydqklP9QHDPD3qHJM07TV3IfHstjA/640?wx_fmt=gif)

整理 | 褚杏娟

这段时间，华尔街造了“新神”Anthropic。

过去一个月里，多次板块级波动都被市场解读为与 Anthropic 的产品发布直接相关：周一 IBM 股价大跌，有交易员将导火索归因于 Anthropic 宣传的一款工具，它可能自动化 IBM 体系里某种编程语言的部分工作；2 月 20 日网络安全板块集体回撤，被归因于 Anthropic PBC 为 Claude 推出的新安全能力；更早一些，法律科技和软件板块在月初的集中抛售，也被一些声音解释为 Anthropic 面向法律行业推出 AI 插件所引发的预期变化。

面对“市场波动都怪你们”的叙事，Anthropic CEO Dario Amodei 的态度显得克制而暧昧。他在软件股下跌期间回应称：“有些人把这归因到我们身上，但我也不确定是不是我们直接造成的……股市里‘到底为什么发生’这种问题，本来就很难说。”

资本层面之外，Anthropic 前两天对中国大模型公司展开“进攻”，称中国三家主要实验室 DeepSeek、Moonshot 和 Minimax 对其模型 Claude 发起了所谓“蒸馏攻击”，使用超过 2.4 万个虚假账户，与 Claude 产生 1600 多万次交互，用于复制模型能力并训练自有模型。Anthropic 同时将问题上升到国家安全层面，称非法蒸馏可能移除安全护栏，使模型能力被用于军事、情报和监控系统。

但该说法很快遭到大量质疑。有用户向 Claude Sonnet 4.6 询问“你是什么模型”，其回答竟是“我是 DeepSeek”，并且有人通过官方 API 复现成功。

马斯克留下一个“😂”。

![图片](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNiaQldNticZQHlLmue3tGURSo9DslshHpevdmL347aBREzGRD079qrs9gxHwqBIZEkOuEaVtqg9E1xflabEdP0j07r5ab5lwL1UI/640?wx_fmt=png&from=appmsg)

几乎同时，关于 DeepSeek V4 的消息频繁曝出，在最近参加 Nikhil Kamath 的访谈时，主持人问到 Amodei 对开源和闭源的看法时，Amodei 没有直接回答问题，而是直指中国模型蒸馏美国模型、为了 benchmark 做优化。“拉踩”一波后，他表示自己几乎全部精力都在做“最聪明、最适合任务的最佳模型”上。

  

  

  

  

  

首先，许多模型，尤其是来自中国的那些，往往针对基准测试做了强优化，而且不少是从美国头部实验室的“大模型”中蒸馏出来的。最近一项测试就揭示了这一点：一些模型在常见的软件工程基准上得分很高，但当有人设计了一个未公开过、此前从未见过的新基准时，它们的表现就明显下滑。这让我觉得，它们更多是为 benchmark 而优化，而非为了真实世界中的使用而优化。

但除了 benchmark 的局限之外，模型的经济学逻辑也和以往技术完全不同。我们逐渐发现，市场对“质量”存在一种极强的偏好。这有点像雇人：如果我对你说，你可以选择聘用全世界最好的程序员，也可以聘用排名第 10000 名的程序员。虽然他们可能都很强，但任何招过很多人的人都知道，能力分布是呈幂律分布的，头部与长尾的差距巨大。

模型也是同理。在一定范围内，价格其实没那么重要。只要一个模型是最强、认知能力最高的那个，无论是它的价格、还是它的交付形式，都不那么重要。因此，我几乎把所有精力都放在把模型打造成“最聪明、最适合任务的最佳模型”上。在我看来，这才是唯一重要的事。

值得注意的是，近日关于 DeepSeek V4 的消息频繁曝出。据路透社报道，DeepSeek 最快将于下周发布新一代 AI 模型，外界普遍推测该版本即为 DeepSeek V4。而据晚点报道，DeepSeek 在春节前后仅对现有模型进行了小幅升级，外界关注的 DeepSeek V4 则预计会在 3 月前后发布。而 CNBC 报道称，市场已严阵以待，部分投资机构担忧 DeepSeek 再次引发类似去年模型发布时的市场剧烈波动。当时，英伟达股价一度下跌近 17%，瞬间蒸发 6000 亿美元。

针对 Anthropic 的指控与叙事，T3 Chat 创始人 t3dotgg 公开进行了连夜测试并逐条反驳，认为 Anthropic 这次“自我打脸”，并没有他们试图营造的那种“铁证如山”，他们就是在胡扯。他甚至气愤地说，“你们真的让人火大。你们总在撒谎，总在挡路，总在搞一些奇怪的政策操作。”

逐条反驳，“蒸馏攻击”言论

t3dotgg 指出，“distillation attack”更像是 Anthropic 临

...(截断)
