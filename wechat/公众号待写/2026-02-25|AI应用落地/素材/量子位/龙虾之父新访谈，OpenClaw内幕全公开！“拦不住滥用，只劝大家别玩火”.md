# 龙虾之父新访谈，OpenClaw内幕全公开！“拦不住滥用，只劝大家别玩火”

- 来源: 量子位
- 时间: 2026-02-25 13:31
- 链接: https://mp.weixin.qq.com/s/NiNAjU_AziuLYLA5MyNtOQ

## 摘要

龙虾之父也曾被AI编程啪啪打脸

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/A6fTew8FFGFib1OpfcHCibEaBGoeG0w7wQox7hdsk88NvEFgQfPYG0gjHjM4hTaqZ3AwncAQvrK7wyNYlYhwfQucp2VsQ5MVIViaFuI8oIMLXY/0?wx_fmt=jpeg)

龙虾之父新访谈，OpenClaw内幕全公开！“拦不住滥用，只劝大家别玩火”
=====================================

[量子位](javascript:void\(0\);)

在小说阅读器中沉浸阅读

##### 梦瑶 发自 凹非寺  
量子位 | 公众号 QbitAI

不是，这才加入OpenAI几天啊，龙虾之父**Peter Steinberger**这波发言属实猛了些啊！

在OpenAI的最新访谈中，他聊创业、聊OpenClaw、聊龙虾滥用和安全问题，那叫一个「实诚」。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/A6fTew8FFGEWTw955Jib8jp8eFMgbsAujSeROTE2ccakiaqmtPv0GJjnQRRl9FsAajCkeia5TgPcrf9CoxFwuic5F9HWTnlCoNnHe2yCRXcEA98/640?wx_fmt=png&from=appmsg)

实诚到什么程度呢？人家Peter可摸着良心说了

> 说实在的啊，我平时连代码都很少看……大多数代码都挺无！聊！的！（Big胆）

而整场对话听下来，有几个判断尤其值得玩味，我帮大家梳理了一下——

*   Peter创业13年后精力耗尽退隐，结果被Claude Code一小时原型直接「打脸」重燃。
    
*   Peter直言没法儿阻止大家滥用OpenClaw，只能尽可能让大家别自毁前程。
    
*   OpenClaw已经有2000个PR，有些PR更像是prompt request，代码靠后，意图靠前。
    
*   代码不必百分百符合审美，关键是方向对，如果真出现性能问题，再专门去优化。
    

下面这位网友看完这个采访憋不住了，直言：Peter太接地气儿了啊，这到了OpenAI咋适应啊..（doge

![](https://mmbiz.qpic.cn/sz_mmbiz_png/A6fTew8FFGEZvgNnZBxC3PR5phXXJ3T9ozraekwKpTEBdYOMp4q2eLtsDNHHAl2xsKfYILqJvbDYq9Kj6GHuRnzmh5wE2icSVjF9LKXGpwso/640?wx_fmt=png&from=appmsg)

以下为本场访谈重点内容实录，围绕核心观点做了摘选整理，部分文字在不改变原意的基础上做了适度删改～

从13年老创业人，到龙虾时刻上头
----------------

#### 龙虾之父第一次被AI编程“打脸”

Q:你做PSPDFKit连续拼了13年，后来停了一段时间，是啥原因让你又回来创业了？

**Peter Steinberger**：是的，确实是连续13年高强度运转。

第一次创业，我也不懂怎么给自己降压，只能停下来放松一下，那段时间我会关注AI的进展，早期看到GPT Engineer觉得挺酷，但没真正被打动。

直到状态恢复了些，我开始亲手试，真正震住我的是我把一个做了一半就丢下的项目打包成一个大Markdown文件，让模型先写规格，再交给Claude Code去构建。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/A6fTew8FFGE8R1nM9IIAYYy6KzQY4GiasfUtgicBSANsRbwHhyxEkcH8gbaQPTPuZBrrVE3mtgrKJgJWoiavVJnqR3L38S9boI3Pgrich96ld3o/640?wx_fmt=png&from=appmsg)

那时候比现在粗糙很多，它还跟我说“我已经100%量产可用”，我一试就崩了。

于是我接了自动化测试工具，让它把登录那套做出来、一路验收，大概一小时后，居然真的跑通了。

虽然代码质量一般吧，成品代码很烂，但对我来说，流程层面的冲击太大了——

> 可能性一下子铺开，我起了「鸡皮疙瘩」。

从那天起我几乎睡不着， 因为脑子里全是：

以前想做却做不了的东西，现在都能做了，然后我就彻底钻进去了。

#### 一条语音，让OpenClaw真正活了

Q：过去9到10个月，我看你的GitHub有四十多个项目，能讲讲这些想法是怎么一路汇到OpenClaw里的吗？

Peter Steinberger：说实话，我也希望当初有一个宏大的蓝图，但真实情况更像一路试出来的。

最初我只是想做一个能读我聊天记录、替我处理事情的工具，原型做出来了，域名也买了，但我以为大实验室很快会做，我就等一等，把注意力放去别的方向。

那段时间我做了很多实验，目标很简单——玩得开心，也激励别人。

到了十一月，我做了几个版本，没有一个让我真正满意，我开始疑惑：

为什么那些大实验室还没做出来？他们到底在干嘛？于是我做了后来变成OpenClaw的第一个版本，到现在名字已经换到第五个。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/A6fTew8FFGEJfBod9N6nRu5jfvkxPHOUpibRHg7I68K9wQiawGEFKX0PPRXKAoBkQpwPrpxgf9tW1ISkb75wXq6wVa4Dia9sUFVSdEakKia6QzU/640?wx_fmt=png&from=appmsg)

当时产品还没完全成熟，只是觉得很酷，第一个原型大概一小时就做出来了，因为很多东西现在可以直接催出来。

真正让我彻底上头的，是在马拉喀什的一次周末旅行。

当时网络不稳定，但聊天软件在哪都能用，我用它翻译图片、找餐厅、查电脑里的东西，我给朋友演示，让它替我发消息，朋友立刻说想要。

后来有个更离谱的瞬间，我发了一条语音，居然出现了「正在输入」，这本来不该能跑通，结果它真的回复了，我问它怎么做到的，它说：

> 你发的是个没后缀的文件，我看

...(截断)
