# 170 万围观！继「Vibe Coding」后，Karpathy 又造了个新词：Claw

- 来源: AI信息Gap
- 时间: 2026-02-23 06:33
- 链接: https://mp.weixin.qq.com/s/-Is77gkIr8BASNoHKE1yUg

## 摘要

Karpathy：AI 技术栈又多了一层。Chat -> Code -> Claw 🦞。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/VpHtkRLWJljcqu9hiaULmMtlibSbN35oJZkc4SicAvJc0mptpdfpKa4qK0yZoS3Lrju1h9qyibVm1RlBTIJibxcIWA2Yb9O8ISjZ67gvGno373Hk/0?wx_fmt=jpeg)

170 万围观！继「Vibe Coding」后，Karpathy 又造了个新词：Claw
============================================

原创 木易的AI频道 木易的AI频道 [AI信息Gap](javascript:void\(0\);)

在小说阅读器中沉浸阅读

Andrej Karpathy 跑去苹果店买了台 Mac mini。

店员跟他说，这东西最近卖疯了，搞不懂为什么。

Karpathy 懂。他去给自己的「数字龙虾」找个窝。

然后他在 X 上发了一条长推文。24 小时，170 万阅读。

![](https://mmbiz.qpic.cn/mmbiz_png/VpHtkRLWJlia46oSd6mFiblnQYn60EXB6w0m5proWkb4KI56BRx4uibRVgy4weKRvr3E96HbRE9GQVw4p0drJ1ZrTqtEE64nn1JloEjWjw3MJE/640?wx_fmt=png&from=appmsg)

核心观点很有意思。

> LLM 之上有 LLM Agent，LLM Agent 之上，现在又多了一层，「**Claw**」。

Andrej Karpathy（安德烈·卡帕西）是 OpenAI 联合创始人、前特斯拉 AI 总监、斯坦福博士。AI 圈最顶级的技术网红，没有之一。

这是一位造词能力极强的大神。

2025 年 2 月他随口说了个「Vibe Coding」，几周后全行业都在用，年底直接成了柯林斯词典的年度词汇。

他说的另一个词「Agentic Engineering」，现在也成了新岗位名称。

Django 框架联合创始人 Simon Willison 评论道，「Karpathy 对技术术语的嗅觉一直很准，这次 Claw 很可能也会成为下一个行业黑话。」

连 emoji 都有了。🦞

![](https://mmbiz.qpic.cn/mmbiz_png/VpHtkRLWJliavhqHCG6icu8ClGcoDYpVqMvibe1jUdaiasicV7o3GW3PJZqNU2ibe3ptiaMNPrh5sSCG9gI08Ps5WMO0FiaZwFAknl0jLDicLR6ZkZgU/640?wx_fmt=png&from=appmsg)

  

* * *

### Claw 到底是什么？

Karpathy 这次在给一整类东西命名。

过去两年，AI 技术栈可以分为两层。

第一层是大模型本身。你问问题，它回答你。ChatGPT 聊天，就是这样。

第二层是 Agent。你给它一个任务，它自己调用工具、写代码、查资料，帮你完成。Claude Code、Cowork、Cursor，都算这一层。

现在第三层来了，「Claw」。

那么，Claw 和 Agent 的区别在哪？

四个关键词，「**编排、调度、上下文、持久性**」。

Agent 是你叫它干活它才开始干。Claw 是你不叫它，它也在干。

它在你的电脑上常驻，24 小时在线。它有长期记忆，记得你上周说了什么。它有定时任务，可以每天早上给你发一份日报。它能同时连着你的聊天软件、邮箱、日历、代码库，哪里有事去哪里。

Karpathy 说这就像家里有一台被「附身」的设备，里面住着一个 personal digital house elf「数字家养小精灵」。

  

* * *

### 40 万行代码的安全噩梦

但 Karpathy 紧接着说，他不敢用 OpenClaw。

> 「把我的私人数据和密钥交给一个 40 万行 vibe coded 的怪物，这件事一点都不好玩。」

暴露的实例、远程代码执行漏洞、供应链投毒、恶意 Skills。他用了一个词来形容整个 OpenClaw 生态的现状。

Wild west。荒野西部，法外之地。

这跟我之前在 OpenClaw 安全篇里写的几乎完全吻合。

Shodan 数百个裸奔的实例，5 分钟拿到 SSH 私钥的提示词注入攻击，4000 次下载的恶意供应链包。谷歌云安全副总裁 Heather Adkins 当时直接就说，别用。

Peter Steinberger 已经在 2 月 15 日加入了 OpenAI，OpenClaw 转为基金会运营。

所以 Karpathy 全力看好 Claw 这个方向，但 OpenClaw 他不碰。

  

* * *

### 4000 行代码，有点上头

Karpathy 看上了另一只龙虾。

NanoClaw。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/VpHtkRLWJljS08zlD00aMibB7Pjpg26oK3AggzypfOUPZdanmBSkibf77wZrRt6qmVg9k0ClOU4DWVe111PicRS3QsKzeSJlcea38k11t0m8Pg/640?wx_fmt=png&from=appmsg)

4000 行代码。只有 OpenClaw 的百分之一。所有 Agent 都跑在 Linux 容器里，文件系统隔离。

但真正让 Karpathy 有点上头的，是 NanoClaw 的 Skills 系统。

传统应用，功能越多代码越臃肿。OpenClaw 就是这么变成 40 万行的。

NanoClaw 完全不同。想加 Telegram？运行 `/add-telegram`，`Claude Code` 读取一份 Skill 文件（本质就是一个 Markdown 教程），按指示直接改你本地的代码，生成一个干净的定制版本。

百分百 AI 驱动的功能迭代。

Karpathy 联想到了深度学习里的「元学习」。2017 年的 MAML 论文，核心思路是训练一个「最容易学会新东西」的模型。

Na

...(截断)
