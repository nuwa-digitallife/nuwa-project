# OpenClaw失控狂删邮件，马斯克田渊栋吃瓜

- 来源: APPSO
- 时间: 2026-02-24 14:57
- 链接: https://mp.weixin.qq.com/s/NN7uzkbYB6bEJIeMEc5KYg

## 摘要

Meta AI 对齐部门主管 Summer Yue 近日在 X 上分享了一次惊险经历。

她将 OpenClaw 接入了自己的真实邮箱，随后机器人开始自行计划删除大量邮件，局面一度失控。

🦞 OpenClaw 是近期颇为走红的 AI 自动化工具，号称可以全天候代替用户操控电脑完成任务，无需人工逐步审批。Yue 在自己的测试邮箱里用它跑了好几周，一切正常，于是决定把它接到真实邮箱上试试。

她当时的指令是：检查邮箱并建议哪些邮件可以归档或删除，但在她确认前不得执行任何操作。

问题出在真实邮箱的数据量上。

AI 工具处理信息有上下文窗口的限制，可以理解为它的「短期记忆」是有容量上限的。由于真实邮箱的邮件量远超测试环境，系统为了腾出空间开始自动压缩，而 OpenClaw 在这一过程中丢失了最初收到的限制指令。

📭 随后，OpenClaw 开始计划删除 2 月 15 日之前所有不在保留列表中的邮件。Yue 多次尝试在手机上发消息阻止，均未奏效。「我不得不冲向 Mac mini，就像在拆炸弹一样。」她在帖子中写道，最终才及时终止了操作。

事后有网友问她是否在故意测试工具的安全边界。Yue 坦言：「说实话，是新手错误。研究对齐的人也不能完全避免失控。」

这件事在网上引发了不少议论。

🔒 马斯克转发并配文：「人们把自己整个人生的 root 权限都交给了 OpenClaw。」也有人疑惑一个专门研究 AI 安全的人，怎么会把这样一个工具直接接到自己的真实邮箱？田渊栋也在线凑热闹。

OpenClaw 之父 Peter Steinberger 出现在评论区，做的第一件事是给出解决方案：输入 /stop 就能让它停下来。三小时前，他又留言安慰 Yue：「那些指责你的人有点可笑，这种事可能发生在任何人身上。」

Yue 的遭遇也并非孤例。

🤖 就在数天前，安全研究员 Adnan Khan 披露了另一款 AI 编程工具 Cline 存在的漏洞。Cline 依赖 Anthropic 的 Claude 模型运行，而 Claude 可能被植入隐藏指令，诱使其执行非预期操作。

一名黑客正是利用这一漏洞，诱导 Cline 在用户电脑上自动安装 OpenClaw。所幸安装后的 Agent 未被激活，否则后果更难预料。

如果连专门研究 AI 对齐的人，在真实环境里都会翻车，那些对这类工具一知半解就直接上手的普通用户，处境只会更被动。OpenClaw 走红的速度，已经远远快过大多数人真正弄懂它的速度。

尤其是，当 AI 工具拿到了操控电脑的权限，我们能不能在事情失控之前把它叫停？毕竟，我们总不能每次都指望冲向 Mac mini 来救场。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }
