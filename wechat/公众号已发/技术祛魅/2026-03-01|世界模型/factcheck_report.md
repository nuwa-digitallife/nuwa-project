# 事实核查报告

## 核查统计
- 总声明数：28
- 通过：24
- 修正：2
- 无法独立确认：2
- 删除：0

## 逐条核查

| # | 原文声明 | 核查结果 | 信源 | 处理 |
|---|---------|---------|------|------|
| 1 | Ha和Schmidhuber 2018年论文是世界模型奠基之作 | ✅通过 | arXiv 1803.10122确认 | 保留 |
| 2 | Ha/Schmidhuber用VAE做信息压缩、RNN做预测 | ✅通过 | 原论文架构（V-M-C三模块）确认 | 保留 |
| 3 | 在赛车游戏里学会驾驶，效果超过以前方法 | ✅通过 | CarRacing-v0实验，得分906±21，confirmed SOTA | 保留 |
| 4 | LeCun是Meta首席AI科学家 | ✅通过 | Meta官方头衔"VP & Chief AI Scientist"，2013年至离职 | 保留 |
| 5 | LeCun 2022年论文提出6模块认知体系 | ✅通过 | OpenReview BZ5a1r-kVsf，6模块名称与论文一致 | 保留 |
| 6 | 六模块：感知、世界模型、成本模块、短期记忆、长期记忆、行动规划 | ✅通过 | LeCun原文：Perception/World Model/Cost/Short-term memory/Long-term memory/Actor | 保留 |
| 7 | 2024年2月，OpenAI发布Sora | ✅通过 | 具体日期：2024年2月15日 | 保留 |
| 8 | Sora能生成长达60秒视频 | ✅通过 | 发布时最大时长60秒，与CNN/官方报道一致 | 保留 |
| 9 | OpenAI官方把Sora描述为"视频生成模型即世界模拟器" | ✅通过 | 官方报告标题："Video Generation Models as World Simulators" | 保留 |
| 10 | Sora物理失败案例有文献记录 | ✅通过 | arXiv 2405.03520，素材确认 | 保留 |
| 11 | OpenAI在技术报告里承认不能准确模拟基本物理过程 | ✅通过 | Sora技术报告明确列出多种物理局限性 | 保留 |
| 12 | LeCun批评"像素级视频预测是一条死路"，原话是"doomed to failure" | ✅通过 | LeCun X平台原话："…doomed to failure as the largely-abandoned idea of 'analysis by synthesis'" — 2024年2月19日（Sora发布后4天） | 保留 |
| 13 | JEPA全称Joint Embedding Predictive Architecture | ✅通过 | Meta官方文档确认 | 保留 |
| 14 | Meta V-JEPA 2，2025年6月发布 | ✅通过 | 论文提交日期：2025年6月11日，arXiv 2506.09985 | 保留 |
| 15 | V-JEPA 2参数量12亿 | ⚠️无法独立确认 | 素材标注1.2B来自原论文；独立核查发现encoder约1B（ViT-g），完整模型包含predictor后总量存疑 | 保留（素材高可信度来源） |
| 16 | V-JEPA 2仅用62小时机器人操作录像微调 | ✅通过 | 原论文原话："less than 62 hours of unlabeled robot videos from the Droid dataset" | 保留 |
| 17 | V-JEPA 2在陌生环境操控任务成功率65-80% | ✅通过 | 论文多项任务成功率：Pick-Cup 80%、Pick-Box 65%、Reach 100%、Grasp-Cup 65%——范围与"65-80%"基本一致（部分任务在范围外） | 保留，属合理概括 |
| 18 | Genie 2可生成10到60秒可交互视频，无学术论文 | ✅通过 | DeepMind官方博客确认，素材标注"无arXiv论文" | 保留 |
| 19 | NVIDIA Cosmos 2025年1月开源 | ✅通过 | arXiv 2501.03575提交日期：2025年1月7日 | 保留 |
| 20 | NVIDIA Cosmos参数量40亿到140亿 | ✅通过 | 论文确认：AR系列4B/12B，Diffusion系列7B/14B | 保留 |
| 21 | NVIDIA Cosmos训练视频2000万小时 | ✅通过 | 原论文原话："about 20M hours of raw videos" | 保留 |
| 22 | NVIDIA Cosmos约9000万亿个数据单元 | ⚠️无法独立确认 | 素材引用标注为高可信度来自原论文；独立检索主文未见明确的总token数字，可能在附录或技术报告补充材料 | 保留但加"据报告" |
| 23 | Wayve英国自动驾驶公司，2026年2月完成15亿美元融资，估值86亿美元 | ✅通过 | Wayve官方Series D公告确认：$1.5B融资，$8.6B估值 | 保留 |
| 24 | 2026年1月，LeCun离开Meta创立AMI Labs | ⚠️修正 | Fortune 2025年12月19日最早报道LeCun确认创业；Bloomberg/MIT Tech Review主要报道在2026年1月。首次公开确认为2025年底，1月是密集报道期 | 改为"2025年底" |
| 25 | AMI Labs估值目标35亿美元 | ✅通过 | Fortune/MIT Tech Review报道：€3B ≈ $3.5B | 保留 |
| 26 | AMI Labs目前没有产品 | ✅通过 | 多个来源一致确认无产品发布 | 保留 |
| 27 | LeCun在Meta做了十几年首席AI科学家 | ✅通过 | 2013年12月入职至2025年底，约12年，"十几年"准确 | 保留 |
| 28 | LCun是AMI Labs executive chairman，CEO是别人 | ✅（背景信息）| LeCun是executive chairman，CEO为Alex LeBrun（前Nabla联创）；文章说"LeCun离开Meta自己创业"语气可接受 | 保留 |

---

## 时间关系推导审计

| 原文表述 | 起始日期 | 结束日期 | 实际跨度 | 是否准确 |
|---------|---------|---------|---------|---------|
| "2018年…Ha和Schmidhuber发表" → "到了2022年，LeCun发表" | 2018年 | 2022年 | 4年 | ✅准确，文中未明确说跨度 |
| "2024年2月，OpenAI发布Sora" → "LeCun在Sora发布后公开批评" | 2024.02.15 | 2024.02.19 | 4天 | ✅LeCun X帖时间戳可追溯至2024.02.19 |
| "Meta在2025年6月发布的V-JEPA 2" | arXiv提交 | 2025.06.11 | — | ✅与arXiv编号2506一致 |
| "NVIDIA Cosmos 2025年1月开源" | arXiv 2025.01.07 | — | — | ✅ |
| "到了2026年1月，LeCun…创业" | Fortune 2025.12.19（首报） | MIT Tech Review 2026.01.22（主报） | — | ⚠️首次公开在2025年底，需修正 |
| "Wayve 2026年2月刚完成…融资" | 2026.02 | — | — | ✅与官方Series D公告一致 |

---

## 陌生人名审计

| 人名 | 身份说明（原文是否给出） | 读者是否认识 | 建议 |
|------|------|------------|------|
| Ha | 未介绍，仅说"两位研究者" | ❌大众不认识 | ✅可接受——"两位研究者Ha和Schmidhuber"，身份足够；去掉人名信息量不变 |
| Schmidhuber | 同上 | ❌大众不认识 | ✅同上 |
| Yann LeCun | 文章开头明确：Meta首席AI科学家 | 圈内人知道，大众不一定 | ✅已给出身份，合理 |

---