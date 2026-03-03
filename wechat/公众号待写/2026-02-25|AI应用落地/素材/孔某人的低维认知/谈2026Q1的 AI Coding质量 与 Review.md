# 谈2026Q1的 AI Coding质量 与 Review

- 来源: 孔某人的低维认知
- 时间: 2026-02-25 14:00
- 链接: https://mp.weixin.qq.com/s/s4EhjJh1ebP8qUq-vFUjSQ

## 摘要

AI Coding确实需要正经的Review，否则会更快的导致代码腐败。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/XQa98jWSCyoxWtkhFxPyxgzDKY8VxlcFJOee3doZVRUwZYHHqrqONhSVyy4AwZDJPQrGRibavQDmmn4lfCIBO7w9xc6GQ2ffUicSuhc2D1OCI/0?wx_fmt=jpeg)

谈2026Q1的 AI Coding质量 与 Review
=============================

原创 孔某人 孔某人 [孔某人的低维认知](javascript:void\(0\);)

在小说阅读器中沉浸阅读

春节假期中，大量使用了AI Coding工具做一些新的事情，但体感实际上跟很多人以及我过去的预期并不匹配。特别是最近几天开始把高强度的AI review进入到开发流程中，发现了一些之前完全没有注意到的事情。

感觉似乎更进一步的理解了为什么现在开发者对于AI Coding代码质量的不同观点流派。

所以本文就来谈一谈我的发现，以及我目前在AI Review上的一些实践经验。

1、这几天的实践
========

在过去10天之内，主要做了两件事：

*   数据库上的数据治理，并且有可供对照的原始材料，主要使用Claude Code完成。
    
*   一个自用的数据CRUD类软件的3批新功能开发，也是主要使用Claude Code完成。
    

10天中花费了1550刀的Claude Code等效额度（使用ccusage统计），此外还花费了不少Codex CLI的额度，和大约80刀的Cursor额度。这些都以原价LLM API调用计算。我使用的都是原厂服务。

**1.1、数据治理**
------------

从实践来说，使用AI Agent来做数据治理是不错的，大概算得上是最佳实践。我使用Claude Code + Opus 4.6，应该算得上最强一档。

但实际使用并不能放心，虽然说Opus 4.6不至于随便删库，但不能完全遵守指令，过短的Context 能力（200k）都导致过程体验较差。由于我很在乎这个数据的最终质量，所以我不得不高强度盯着它，每轮修改都要review修改计划再实施，并在过程中对它进行纠偏以及同步我对于一些情况的处理意见。**这个高强度盯着的方式已经好久没有了，感觉跟我2025年5-8月的时候类似了。**

在我最近的高强度Claude Code使用下，又重新让我开始怀疑Claude Code是否会有一些间歇性降智的问题，例如在北京时间晚上21点之后。**有些情况犯的错误就很离谱**，感觉就像是一些智力较低的模型。而且感觉跟 context 压缩过程有较大相关性，不过现在不仅是context压缩了，Claude Code也增加了Memory功能。

数据治理工作做了几天，**感觉这个过程让我下调了我对目前前沿AI Coding Agent能力的判断**。

**1.2、功能开发**
------------

这个过程中在一个项目上做了三波较大的开发。项目整体规模是4w行Python+3w行Next.js。每波新功能的设计都是跟AI讨论2-4小时，然后再交付开发。

前两波没有什么特别的，Cursor自带有一个Review Agent。**从第三波开始在完成之后使用额外的Claude Code和Codex进行Review。与预想偏离的地方就从这第三波开发的Review开始了。**

在这之前已经有了一些心理准备：

*   一个是Claude Code在数据治理中的不算很好的表现
    
*   另外是中间做了一些当前项目的AI review，虽然发现了一些冗余和死代码，但总体感觉还算正常。
    

第三波修改中，第一个是一次大重构，并新增了一些功能。**我最近给AI的目标都是不要做最小化重构，而要做干净且合理的设计**，所以这次修改牵扯面较多。最终是5k行新增+5k行删除的量级。

但进入Review环节之后就发现陷入了泥潭。每轮review使用Cursor Review Agent、Claude Code、Codex三方独立review，然后交由Claude Code在接续开发的context中进行修复。整个过程进行了十几轮，累计耗时9h，**而且每轮都能发现一些明显的问题**。

在这个过程中：

*   Codex发现问题的能力令人深刻，但速度也较慢。
    
*   Claude Code的review能力也不错，速度适中。
    
*   Cursor Review Agent的结果大概算是比聊胜于无强一点，但不多，而且误报率也偏高。
    

但不管怎么样，目前AI Review的过程都有一些明显的缺点：

*   **每轮review不能召回大部分问题，**即使Claude Code和Codex拆分了子Agent来去做分区调研了也是如此。这也是为什么最终整个Review过程长达9h的原因。**即使三家一起上，每轮review能发现一些问题，但有限。**
    
*   review过程较慢，一轮review没比开发短多少时间，尤其是对于Codex来说。
    
*   AI Review过程极耗token，Codex的额度之前似乎很难用完，但在这9h review中，我把ChatGPT Plus的Codex周额度使用了50%，这是我之前无法想象的。
    

还没有完的是，在我通过AI review消除掉了所有可见问题之后，发现该次功能的设计上还有bug，又不得不进行了功能调整。

在这之后又进行了2个小一点需求的修改，大约每次diff量1k行水平，**但看起来每次开发仍然需要配合3轮左右的review才算完善。**

2、我的评论
======

首先目前的AI Coding Agent做不到很细心，在代码开发中其实是有表现的，只是即使你比较多的与Agent交互也不一定能发现。**但是当你在一个稍大的项目中开发，并认真地找其他Agent来做review时候，你会发现这些不够完善的地方**。体感是，即使是目前最强的Coding Agent，第一轮直出的代码大概我也只能评分为60-70分。

这个不细心

...(截断)
