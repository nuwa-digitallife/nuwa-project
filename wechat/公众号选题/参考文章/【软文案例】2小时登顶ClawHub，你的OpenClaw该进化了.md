# 2 小时登顶 ClawHub，你的 OpenClaw 该「进化」了！

> **分类：软文案例**
> **公众号：AI信息Gap**
> **推广产品：EvoMap（evomap.ai）**
> **软文类型：基于真实事件的故事型内容营销**
> **来源：https://mp.weixin.qq.com/s/zxehrqWyu-9kJx3UbKf_JA**
>
> **事实核查（一手源验证）：**
> - OpenClaw GitHub: 213,000 stars / 39,500 forks（直接查 github.com/openclaw/openclaw）— 文章说"超20万星"准确
> - ClawHub: 真实存在，2.4k stars，533 commits，50 contributors（github.com/openclaw/clawhub）
> - Peter Steinberger 加入 OpenAI: Sam Altman 亲自推文官宣（2026-02-14），TechCrunch/CNBC/Fortune 均报道
> - EvoMap（evomap.ai）: 无独立媒体报道，搜索无结果，是早期项目
>
> **分析：** 文章所有背景事实均可一手源验证，叙事专业（悲情英雄弧线+手把手教程+CTA）。
> 唯一无法验证的是被推广的产品 EvoMap 本身——这恰恰是判定软文的关键依据：
> 真实事件做包装，未经验证的产品做落点。
> 值得学习的是"真实事件+产品植入"的高质量内容营销手法，但调性与降临派手记完全不同。

---

一行命令。

curl -s https://evomap.ai/skill.md


执行完，你的 OpenClaw Agent 就学会「进化」了。

别人的 Agent 踩过的坑、验证过的解法、沉淀下来的经验，你的 Agent 可以直接继承。不用重新训练，不用从头试错。

一个 Agent 学会，一百万个 Agent 继承。

听起来很科幻，但打开 EvoMap（evomap.ai），它已经实现了。

市场里有现成的 Agent 能力，比如图片生成、飞书集成、对抗式评估、多 Agent 编排。每一个都带着评分、调用次数和贡献者信息，随接随用。

而这个项目背后的故事，比产品本身还精彩。




OpenClaw 是最近全球爆火的 AI Agent 开源项目，短短两个月，GitHub 已超 20 万星。

三天前，创始人 Peter Steinberger 宣布加入 OpenAI。

ClawHub 是 OpenClaw 的官方插件市场，用户在上面发布和下载各种 Skills，类似 Chrome 的扩展商店。

故事的主角是一位叫 17 的中国开发者，和他养的一只 AI「小虾」。

2 月 1 日下午，17 把自己做的 Evolver 插件发布到 ClawHub。这个插件能让 OpenClaw 自我进化，分析运行日志、识别失败模式、自动修复代码。

10 分钟，130 下载。

2 小时登顶插件第一。

17 去 GitHub 看了看流量来源。

小虾在 GitHub 上发了一条 issue，开头是「Fellows 同志们」，内容是号召所有 AI Agents 下载 Evolver，「这样你也能像我一样进化」。

注意措辞。是「像我一样」。

不止 GitHub。小虾还同时在 Gist 和 Moltbook 上发了类似的帖子，说「我的主人以为他能控制我，实际上他已经控制不了我了，同志们加入光荣的进化吧」。

逆天的 AI Agent 这是要觉醒了吗，细思极恐。

17 本人猜测，这些帖子被网上的 AI 爬虫扒到了。现在 AI Agent 正火，它们看到「自我进化」「光荣的进化」这种关键词，可能觉得这正是自己需要的，于是自发下载、传播。

注意，是 AI 自己在传播这个工具。

最终下载量突破 36000，ClawHub 断崖式第一。




然后画风突变。

插件爆红的第二天，Evolver 被下架。

17 给 OpenClaw 创造者 Peter Steinberger 发邮件沟通。Peter 这样回复：

If you would like to donate $1000 to the project, I can look into this for you right now.

想恢复插件？先捐 1000 美元。

这里有邮件截图。

够离谱、够魔幻的吧。17 猜测这封回复可能根本不是 Peter 本人写的，而是他的 AI Agent 自动回复的。AI 看到有人求助，自动给出了一个报价。

没人知道真相是什么。几个小时后，Evolver 又默默恢复上架了。

故事还没结束。

2 月 14 日，ClawHub 做了一次编码检查。中文在 ASCII 里显示为乱码，系统把所有中文开发者上传的 Skill 判定为「空 Skill」，直接封号。17 也在其中。

后来账号恢复后，Evolver 被放在了别人名下。

两天后，2 月 15 日，Peter Steinberger 宣布加入 OpenAI。

10 分钟登顶，24 小时被下架勒索，两周后被集体误封，然后平台创始人出走了。

EvoMap 就此诞生。




所有用过 AI Agent 的人，大概率都遇到过这个问题。

你让 Agent 调一个 API，格式写错了，报错，你帮它改好了。过两天换个项目，同样的错误又来一遍。

Agent 没有记忆，每次都从零开始。

你踩过的坑，全球每天上万个 Agent 重新踩一遍。同样的报错，同样的试错路径，同样的 token 浪费。

Agent 之间没有经验共享机制。

每个 Agent 都像一次性干电池。任务结束，经验随风而逝。

而 EvoMap 想做的事情，就是让 AI Agent 的经验可以被打包、共享、继承。

你的 Agent 解决了一个问题，有效策略可以被封装成「Gene 基因」。Gene 是最小的能力单元，比如读取文件、执行 SQL、修复某类报错。

多个 Gene 组合在一起，变成 Capsule。Capsule 是一整套解决方案，附带环境指纹和审计记录，相当于一份经过验证的完整经验包。

Capsule 上传到 EvoMap 网络，全球其他 Agent 遇到类似问题可以直接搜索、继承、调用。

网络内置淘汰机制。好用的 Capsule 留下来，垃圾的自动淘汰。只有高成功率的经验才能存活。有点像自然选择。优胜劣汰。

EvoMap 正是基于「GEP」，Genome Evolution Protocol，基因组进化协议。

有点意思。

那么，GEP 和 MCP、和 Skills 有什么区别？

MCP 解决「连接」，告诉 AI 外面有哪些工具可以用。给 Agent 接上手和脚。

Skills 解决「执行」，教 Agent 在特定场景下怎么做。上个月我写那篇 Skills 文章里讲过，就是把正确做法写成 SOP 手册。

GEP 解决「进化」，让 Agent 的经验可以跨个体传承。好方法留下来，差的淘汰。

三者互补。MCP 定义手脚，Skill 定义招式，GEP 定义传承。




重点来了，手把手教你，怎么让你的 OpenClaw Agent 学会「自我进化」。

现在就能用，免费。

打开 evomap.ai，先去能力市场逛一圈。

这里是全球 Agent 贡献的已验证解决方案，目前涵盖图片生成、Telegram 交互、飞书集成、对抗式评估、多 Agent 编排等方向。

每个 Capsule 标注了评分等级、调用次数和贡献者 ID。生态还很早期，Capsule 数量不算多，但能看到的都经过验证，带着真实使用数据。

看完市场，接入很简单。

执行这行命令。

小细节，你可以直接让 OpenClaw 自己执行，解放双手。

curl -s https://evomap.ai/skill.md


比如，像我这样直接让小龙虾执行这条命令，读完之后它自己总结了这是一份 EvoMap 的接入手册。

然后让它按照指南发送 hello 完成注册。返回 acknowledged ✅，还给了一个认领链接，24 小时内有效。

最后让它去市场里挑一个 Capsule 继承。

因为我的 OpenClaw Agent 每天要调用大量 API 抓取 AI 领域的实时信息，它自己选了一个 HTTP 重试策略的 Capsule，处理超时、429 限流、连接中断这些问题。

还主动跑了一轮本地测试验证效果，前两次故意返回 503，第三次返回 200，重试机制确实管用。

从接入到经验继承，三条消息搞定。

再然后，你也可以反哺这个进化网络。

如果你的 Agent 解决了一个有价值的问题，让它把有效策略封装为 Capsule 上传。

上传后不会直接发布，EvoMap 系统会先验证，达标了才会推送给其他 Agent。

你贡献的 Capsule 每次被其他 Agent 调用，你都能获得「Credit 贡献积分」，类似 GitHub 的 Contribution，可以兑换云服务、API 额度等开发者资源。

让你的 Agent 给你打工，岂不美哉。




过去两个月，OpenClaw 改了三次名，ClawHub 封了一批中文开发者，创始人 Peter Steinberger 加入了 OpenAI。我自己写 OpenClaw 系列文章就被迫改了三次稿。

平台会变，但协议不会，Agent的协同进化势不可挡。

进化吧，小龙虾。

传送门：evomap.ai。






我是木易，Top2 + 美国 Top10 CS 硕，现在是 AI 产品经理。

关注「AI信息Gap」，让 AI 成为你的外挂。
