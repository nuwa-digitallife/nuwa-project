# 发布指南：所有人都在造 Agent，Anthropic 突然说：你的方法错了

## 文件清单

- [ ] article.md — 终稿
- [ ] article_mdnice.md — mdnice 排版版
- [ ] poll.md — 投票
- [ ] images/cover.png — 封面图（900x383，不含标题文字）
- [ ] images/01_agent_architecture.png — 专用 Agent 架构图
- [ ] images/02_skill_directory.png — SKILL.md 目录结构截图（GitHub anthropics/skills）
- [ ] images/03_timeline.png — MCP vs Skills 路径时间线对比图
- [ ] images/04_arxiv_chart.png — arXiv 2602.12430 漏洞分类图表
- [ ] images/05_agentskills_io.png — agentskills.io 官网截图

## 简介（3个备选，每个≤70字）

1. Anthropic 高管说 2025 年 Agent 热潮"方法错了"。那什么是对的？他们用"开放标准"回答——两天内 OpenAI 跟进，同一剧本正在 Skills 上重演。但 42,447 个 Skills 扫描结果：26.1% 存在漏洞。技术洞见还是标准卡位？两件事可以同时为真。

2. 所有人都在造 Agent，Anthropic 突然说你造错了——应该造 Skill。能力即文件，业务人员直接写操作手册替代工程师搭架构。OpenAI 两天内跟进。但社区 Skills 漏洞率 26.1%，开放标准不等于跨模型兼容。几个判断供你参考。

3. Anthropic 告诉你 Agent 的方法错了，然后卖给你一套"正确方法"，再把这套方法变成行业标准。MCP 这么走过，Skills 正在重演。这是真洞见，也是真卡位。arXiv 论文扫了 4 万多个 Skills，26.1% 有漏洞——这个数字主流报道基本没提。

## 配图位置

| 图片 | 对应正文位置 |
|------|------------|
| images/01_agent_architecture.png | "先说清楚'专用 Agent'到底是什么"段末，"Anthropic 的判断是……"大字之前 |
| images/02_skill_directory.png | 代码块（my-skill/ 目录结构）之后，"Anthropic 的设计意图是……"之前 |
| images/03_timeline.png | "如果你觉得这个模式有点眼熟"段前，Simon Willison 引用之后 |
| images/04_arxiv_chart.png | "更细的数字……2.12 倍"之后，Tom MacWright 段之前 |
| images/05_agentskills_io.png | 全文最后一段"OpenAI 两天内跟进"之后，署名之前 |

## 封面图建议

主视觉：一个通用 AI 核心（光球或节点），周围有多个能力模块（标签卡片形态）插拔式连接。感觉是"可插拔的能力"而非"碎片化的专用机器"。不放文字，不放人物，偏冷色调（Anthropic 品牌感）。

## 发布步骤

1. 将 article_mdnice.md 粘贴到 mdnice.com 排版（选择适合的主题）
2. 从 mdnice 复制排版后内容到微信公众号编辑器
3. 在编辑器标题栏填写：所有人都在造 Agent，Anthropic 突然说：你的方法错了
4. 按配图位置逐一上传图片到对应段落
5. 设置封面图（900x383，不含文字）
6. 填写简介（从上面3个备选中选一个）
7. 创建投票（从 poll.md 复制问题和选项，不设截止日期）
8. 将投票插入文章结尾（署名之后）
9. 勾选原创声明（文字原创）
10. 开启赞赏功能
11. 预览确认排版、图片、投票均正常 → 保存草稿
12. 扫码发布

## 注意事项

- 封面图不放文字（微信会自动在封面叠加文章标题）
- 投票必须在发布前创建并插入，发布后无法补加
- 数据来源声明保留在文末，不删除
- 丁仪系列首篇，发布后观察评论区反应，记录读者对"技术祛魅"人设的接受度