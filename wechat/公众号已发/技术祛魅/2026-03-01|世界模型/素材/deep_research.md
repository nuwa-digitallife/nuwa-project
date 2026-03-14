素材报告已保存至 `wechat/公众号选题/2026-03-01|世界模型/素材报告.md`

---

# 素材报告：世界模型
采集时间：2026-03-02 21:30 | 三路并行搜索（中文/英文一手源/数据）

---

## 核心事实（已验证）

**概念起源**
- **Ha & Schmidhuber 2018** 是现代 World Model 的奠基论文（VAE + RNN，"梦境训练"）—— [arXiv 1803.10122](https://arxiv.org/abs/1803.10122)
- **LeCun 2022** 将概念扩展为通用机器智能架构，提出6模块认知体系 + JEPA路线 —— [OpenReview](https://openreview.net/pdf?id=BZ5a1r-kVsf)

**三条技术路线清晰分野**

| 路线 | 代表 | 本质 | 状态 |
|------|------|------|------|
| 非生成式（LeCun/JEPA） | Meta V-JEPA 2 | 预测抽象embedding变化，不生成像素 | V-JEPA 2（2025年6月），机器人操控SOTA |
| 生成式视频（Sora/Genie） | OpenAI Sora、Google Genie 2 | 像素/帧预测，涌现物理理解 | Sora官方承认物理缺陷；Genie 2无arXiv论文 |
| 生成式（物理AI专用） | NVIDIA Cosmos、Wayve GAIA | 视频生成 + 物理场景/AV驾驶专用 | Cosmos 2025年1月开源；GAIA-2 2025年3月 |

**最新重磅：LeCun离开Meta创立AMI Labs（2026年1月）**
- 押注世界模型而非LLM，估值目标 **$3.5B**，**尚无产品**
- 来源：[MIT Technology Review](https://www.technologyreview.com/2026/01/22/1131661/yann-lecuns-new-venture-ami-labs/)

---

## 关键数据

| 指标 | 数值 | 信源 | 可信度 |
|------|------|------|--------|
| NVIDIA Cosmos训练视频 | 2000万小时 / 9000万亿token | [arXiv 2501.03575](https://arxiv.org/abs/2501.03575) | 高（官方论文） |
| NVIDIA Cosmos参数量 | 4B–14B | [NVIDIA官方](https://www.nvidia.com/en-us/ai/cosmos/) | 高 |
| V-JEPA 2参数量 | 1.2B | [arXiv 2506.09985](https://arxiv.org/abs/2506.09985) | 高 |
| V-JEPA 2机器人微调数据 | 62小时 | Meta官方 | 高 |
| V-JEPA 2机器人成功率 | 65-80%（陌生环境） | [Meta AI Blog](https://ai.meta.com/blog/v-jepa-2-world-model-benchmarks/) | 高 |
| Wayve Series C | $1.05B | [Wayve官方](https://wayve.ai/press/series-c/) | 高 |
| Wayve Series D（2026年2月） | $1.5B，估值$8.6B | [Wayve官方](https://wayve.ai/press/series-d/) | 高 |
| Genie 2生成时长 | 10-60秒（最长1分钟） | DeepMind博客 | 中（无论文） |
| AMI Labs目标估值 | $3.5B | MIT Tech Review | 中（媒体报道） |

---

## 核心争议

1. **"Sora是世界模型吗"**：OpenAI说是，LeCun/Marcus/学术综述说否——有物理失败文档记录在案（[arXiv 2405.03520](https://arxiv.org/html/2405.03520v1)）

2. **像素预测 vs 嵌入预测**：LeCun称前者"doomed to failure"，OpenAI/DeepMind/NVIDIA全押前者——这是路线之争的本质

3. **LLM隐含世界模型吗**：LeCun：完全不同，LLM建模"关于世界的文本"而非"世界本身"

4. **AMI Labs $3.5B合理吗**：无产品、押少数派路线、纯靠声誉——是信心溢价还是泡沫

---

## 一手源清单（精选）

| 来源 | 类型 | URL |
|------|------|-----|
| Ha & Schmidhuber 2018 | 论文 | https://arxiv.org/abs/1803.10122 |
| LeCun 2022 架构论文 | 论文 | https://openreview.net/pdf?id=BZ5a1r-kVsf |
| V-JEPA 2 论文 | 论文 | https://arxiv.org/abs/2506.09985 |
| NVIDIA Cosmos论文 | 论文 | https://arxiv.org/abs/2501.03575 |
| Wayve GAIA-1论文 | 论文 | https://arxiv.org/abs/2309.17080 |
| Wayve GAIA-2论文 | 论文 | https://arxiv.org/abs/2503.20523 |
| LeJEPA理论论文 | 论文 | https://arxiv.org/abs/2511.08544 |
| OpenAI Sora技术报告 | 官方 | https://openai.com/index/video-generation-models-as-world-simulators/ |
| Genie 2官方博客 | 官方 | https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/ |
| LeCun炮轰Sora | 权威媒体 | https://the-decoder.com/metas-chief-ai-researcher-says-openais-world-simulator-sora-is-a-dead-end/ |
| AMI Labs报道 | 权威媒体 | https://www.technologyreview.com/2026/01/22/1131661/yann-lecuns-new-venture-ami-labs/ |