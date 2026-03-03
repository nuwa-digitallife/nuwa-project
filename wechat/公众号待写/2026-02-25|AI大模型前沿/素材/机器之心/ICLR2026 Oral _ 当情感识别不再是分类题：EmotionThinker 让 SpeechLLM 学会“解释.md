# ICLR2026 Oral | 当情感识别不再是分类题：EmotionThinker 让 SpeechLLM 学会“解释情绪”

- 来源: 机器之心
- 时间: 2026-02-25 11:38
- 链接: https://mp.weixin.qq.com/s/JTUBumkv3aF9vU3Sb6z2mQ

## 摘要

研究团队提出了首个面向可解释情感推理的强化学习框架，尝试将 SER 从 “分类任务” 提升为 “多模态证据驱动的推理任务”。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/5L8bhP5dIqGE2xQ1nDVCV7yS6zX0vC04biaiaNc83JfDm08LPPT8ZCp5Mv3Fia0CozGD05Vfx6tqaBNdqpCpdJ8aJm4icKWaYYdydRhJYEpJPCA/0?wx_fmt=jpeg)

ICLR2026 Oral | 当情感识别不再是分类题：EmotionThinker 让 SpeechLLM 学会“解释情绪”
===============================================================

[机器之心](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/sz_mmbiz_png/KmXPKA19gWic1GuW68DykycvknmG9tyBvLRsVGY4rRKCGuKKSkOqnGrvGwXxqqDxHlia88ZCbqyicswl2HC89BcZA/640?wx_fmt=png&from=appmsg)

  

语音情感识别（Speech Emotion Recognition, SER）在过去基本遵循同一种范式：输入语音，输出情绪标签。这种设定在工程上有效，但在认知层面却过于简化。

  

在人类交流中，情绪判断从来不是一个 “标签选择” 的过程，而是一种基于证据整合的推理行为。我们会综合语调变化、音高起伏、语速快慢、重音位置、语义内容，以及说话人的身份特征，去解释 “为什么” 这是愤怒、“为什么” 这是失落。

  

因此，一个更根本的问题浮现出来：

  

SpeechLLM 是否具备像人类一样解释 “为什么” 做出情绪判断的能力？

  

为此，研究团队提出了 EmotionThinker —— 首个面向可解释情感推理（Explainable Emotion Reasoning）的强化学习框架，尝试将 SER 从 “分类任务” 提升为 “多模态证据驱动的推理任务”。

  

![](https://mmbiz.qpic.cn/sz_mmbiz_png/5L8bhP5dIqEicvqPib6q5ADBcQiaKzUuAXWf9addEO6owRJ8giaVMvnwI3kpv5nqw6JHBdMWt8ECoHjibM9lg9ZoX7hNwuGjBD5opEokoukrpaw8/640?wx_fmt=png&from=appmsg)

  

*   论文标题：**EmotionThinker: Prosody-Aware Reinforcement Learning for Explainable Speech Emotion Reasoning**
    

  

一、从 “情绪分类” 到 “情感推理”

  

EmotionThinker 首先对语音情感识别任务本身进行了重定义，将其扩展为情感推理任务（Emotion Reasoning）。在新的设定下，模型不仅需要预测情绪标签，还需要生成一段解释，明确指出：

  

*   哪些声学线索支持这一判断
    
*   哪些语义线索起到关键作用
    
*   这些线索如何共同构成最终结论
    

  

这种范式转变意味着，模型输出从 “标签” 升级为 “标签 + 基于证据的推理”。

  

它的意义并非简单延长输出，而是对优化目标的重写。模型不再只需 “预测正确”，而必须学习如何整合韵律、语义与说话人属性等多模态信号，并在解释中体现证据对齐过程。情绪识别由此从判别问题转变为结构化推理问题。

  

![](https://mmbiz.qpic.cn/mmbiz_png/5L8bhP5dIqEtqmic0n4a4GMqjNNLBKFKMZhJnUm3ibbe0U1icQ1Fk63SEficiaEfsRBCvUu75hGAy1YFCQToN55msndM6cwoofav4RBZpwwzpYwA/640?wx_fmt=png&from=appmsg)

  

二、EmotionThinker：

面向可解释情感推理的框架

  

EmotionThinker 的目标并不局限于提升最终准确率，而是同时提升三方面能力：

  

（1）更高的情绪识别准确率

（2）更强的情绪线索整合与推理能力

（3）更细粒度的音频描述能力，覆盖说话人特征、韵律线索与语义信息

  

为了支撑这一目标，研究团队首先构建了 EmotionCoT-35K。这是一个包含 35,000+ 条样本的 Chain-of-Thought 风格数据集。与传统 SER 数据不同，它不仅提供情绪标签，还提供细粒度韵律描述与结构化推理解释。

  

这些样本明确标注了音高、能量、语速、重音、语调轮廓等线索如何支持情绪判断，使模型能够学习到 “证据 — 推理 — 结论” 之间的对应关系。

  

与此同时，研究团队观察到：若模型的韵律感知能力不足，其情感推理能力将受到系统性限制。因此，研究团队进一步构建了一个 EmotionThinker-Base。EmotionThinker-Base 通过监督微调增强模型对音高变化、能量波动、语速模式与重音等结构的感知能力，从而为后续的推理优化提供稳定基础。

  

![](https://mmbiz.qpic.cn/sz_mmbiz_png/5L8bhP5dIqEBic20GBXDMQxSOPAtF0IDWT5NKFGtUKwGg5FFf6c2Gic5tGVWicxYvQEmnDtknSbTEtSib4ryibZDuXCz8MSicGReB93LniaQoQU6Is/640?wx_fmt=png&from=appmsg)

  

三、GRPO-PTR：

让强化学习真正优化 “解释能力”

  

在将语音情感识别重定义为情感推理之后，一个新的优化难题随之出现：如何在开放式生成场景中，对 “推理质量” 进行稳定强化学习？直接将推理奖励与情绪预测奖励简单叠加，会带来明显的噪声问题。一方面，模型可能生成语言上看似合理但与最终情绪判断不一致的解释；另一方面，在训练初期，

...(截断)
