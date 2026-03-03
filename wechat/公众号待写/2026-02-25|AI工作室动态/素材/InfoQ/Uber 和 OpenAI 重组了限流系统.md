# Uber 和 OpenAI 重组了限流系统

- 来源: InfoQ
- 时间: 2026-02-25 15:42
- 链接: https://mp.weixin.qq.com/s/YEHCTNG0e8Hiab8PgqaQyw

## 摘要

优步和OpenAI讨论了他们对限流方法的转变。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/hLLZnAbUwNhyibxPwGPSyiaANXN6Vvj3QiaFMPKODoE1wFbSZ4zqdaNnAu59ujXIqtIkZmV8f8dXVwkcxvNLiaKn7qZR4EibKljHmfo8cQoVH6qE/0?wx_fmt=jpeg)

Uber 和 OpenAI 重组了限流系统
=====================

Patrick Farry Patrick Farry [InfoQ](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/mmbiz_gif/YriaiaJPb26VPQqHC66RJFpttVIMWG83T3lWHahUD4bvhxlKSayjeV2ibvC5ydqklP9QHDPD3qHJM07TV3IfHstjA/640?wx_fmt=gif)

作者 | Patrick Farry

译者 | 刘雅梦

在最近的博客文章中，优步（Uber 的限流系统）和 OpenAI（超越限流：扩展对 Codex 和 Sora 的访问）都讨论了他们对限流方法的转变：从基于计数器的、每个服务的限流转向适应性、基于策略的系统。两家公司都开发了专有的限流平台，并在基础设施层实施。这些系统具有软控制功能，通过向客户端施加压力而不是使用硬停止来管理流量——无论是通过概率性丢弃还是基于信用的瀑布流——确保系统弹性而不牺牲用户动力。

以前，优步工程师为每个服务实施限流，通常使用由 Redis 支持的 令牌桶。这导致了操作效率低下，例如额外的延迟，以及部署时需要调整阈值。不一致的配置增加了维护风险，并导致保护不均衡，一些较小的服务没有任何限制。此外，可观测性是分散的，使得很难准确指出由限流引起的问题。

优步用新的全球限流器（GRL）替换了这些遗留限流器。GRL 架构由一个三层反馈循环组成：优步服务网格数据平面中的限流客户端在本地执行决策，区域聚合器收集指标，区域控制器计算全局限制并将其推送回客户端。

GRL 还用一个降低可配置流量百分比（例如 10%）的系统取代了硬停止桶。这个策略作为一个软限制，对调用者服务施加压力，允许它们继续运行，而不会因配额耗尽而关闭。

OpenAI 以类似的架构实施了其新的限流器；然而，主要驱动力是 Codex 和 Sora 应用程序的用户体验，而不是运维弹性。随着越来越多的采用，OpenAI 看到了一个一致的模式：用户发现这些工具具有很大的价值，但被限流中断。虽然这些界限确保了公平的访问和系统的稳定性，但它们经常让参与的用户感到沮丧。OpenAI 寻求一种方法，通过即时基于使用量的计费，在不阻碍探索的情况下保持动力。

工程团队设计了一种综合方法，允许用户在一定限额内访问系统，超过限额后系统将从信用余额中扣除。团队将这个决策过程描述为“瀑布式”：

> 这个模型反映了用户对产品的实际体验。限流、免费层、信用、促销和企业权益都只是同一个决策堆栈中的层。从用户的角度来看，他们不会“切换系统”——他们只是继续使用 Codex 和 Sora。这就是为什么信用感觉不可见：它们只是瀑布中的另一个元素。

为确保这种过渡是无缝的，OpenAI 构建了一个专用的实时访问引擎，将使用跟踪、限流窗口和信用余额整合到单一评估路径中。与传统的异步计费系统不同，这些系统因延迟而受到影响，这个引擎同步地做出可证明正确的决策：每个请求在立即检查信用余额之前，都会识别出限流层的可用容量。

为保持低延迟，系统通过一个流处理器异步结算信用借记，使用稳定的 幂等键 防止双重收费。这种架构依赖于三个紧密耦合的数据流——产品使用事件、货币化事件和余额更新——确保每笔交易都是可审计和可对账的，而不会中断用户的创作流程。

优步和 OpenAI 都报告说，这些架构转变成功地实现了他们各自的操作和产品目标。在优步，全球限流器的实施已经扩展到每秒处理超过 8000 万个请求，覆盖 1100 个服务，显著降低了尾部延迟，消除了外部 Redis 依赖。该系统在生产中证明了其有效性，吸收了 15 倍的流量激增而没有退化，并在 DDoS 攻击到达内部系统之前减轻了它们。

同样，OpenAI 已经将信用系统集成到 Codex 和 Sora 的访问路径中，用连续的瀑布模型替换了硬停止。平台提供实时、准确的计费，同时保持交互式 AI 应用程序所需的低延迟性能。对于这两家公司来说，转向内部、基础设施级别的平台已经用自动化、适应性控制取代了手动配置，允许他们各自的集群在最小的人为干预下处理大规模问题。

**原文链接：**

https://www.infoq.com/news/2026/02/uber-openai-rate-limiting/

声明：本文为 InfoQ 翻译，未经许可禁止转载。

**点击底部********阅读原文**********访问 InfoQ 官网，获取更多精彩内容！****

今日好文推荐

[全行业盯了两年的编程能力榜，今天退役！OpenAI 停用 SWE-bench Verified：未来标准将看 AI 能顶替多少程序员？](https://mp.weixin.qq.com/s?__biz=MjM5MDE0Mjc4MA==&mid=2651276190&idx=1&sn=f450b5a373cc8e23e8dedbdf4229e0dc&scene=21#wechat_redirect)

[收购不成便带头封杀？！Meta 痛下狠手，OpenClaw 彻底失控：被拒后竟“人肉”网暴人类，实锤无人操控](https://mp.weixin.qq.com/s?__biz=MjM5MDE0Mjc4MA==&mid=2651275997&idx=1&sn=4d39f74a4c67edec31477e85cfb122c0&scene=21#wechat_redirect)

[“软件工程师”头衔要没了？Claude Code之父YC访谈：一个月后不再用plan mode，多Agent开始自己组队干活](https://mp.weixin.qq.com/s?__biz

...(截断)
