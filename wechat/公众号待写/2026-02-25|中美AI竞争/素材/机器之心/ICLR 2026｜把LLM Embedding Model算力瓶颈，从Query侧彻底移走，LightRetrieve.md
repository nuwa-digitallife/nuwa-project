# ICLR 2026｜把LLM Embedding Model算力瓶颈，从Query侧彻底移走，LightRetriever来了

- 来源: 机器之心
- 时间: 2026-02-22 18:50
- 链接: https://mp.weixin.qq.com/s/RMUE-ZQ0_SH9Ln3Tm1_7GQ

## 摘要

高质量的 LLM Embedding Model 并不必然意味着高昂的在线推理成本。

## 全文

     #js\_row\_immersive\_stream\_wrap { max-width: 667px; margin: 0 auto; } #js\_row\_immersive\_stream\_wrap .wx\_follow\_avatar\_pic { display: block; margin: 0 auto; } #page-content, #js\_article\_bottom\_bar, .\_\_page\_content\_\_ { max-width: 667px; margin: 0 auto; } img { max-width: 100%; } .sns\_opr\_btn::before { width: 16px; height: 16px; margin-right: 3px; }

![cover_image](https://mmbiz.qpic.cn/sz_mmbiz_jpg/5L8bhP5dIqHt96xQZkc1XyaqtmibNONddU1vt9ojic6bMJcN8yibB71kNClVc0snYyZLfGMHVILQLpZ0j2KTsVvpL2t2UzoFaUmQF3MiatDVUL8/0?wx_fmt=jpeg)

ICLR 2026｜把LLM Embedding Model算力瓶颈，从Query侧彻底移走，LightRetriever来了
===============================================================

[机器之心](javascript:void\(0\);)

在小说阅读器中沉浸阅读

![](https://mmbiz.qpic.cn/sz_mmbiz_png/KmXPKA19gWic1GuW68DykycvknmG9tyBv6ax8e99N0eyLy4Qo7OzKR5sgwWkpGv1vxoygrqI14ssGoXb90ibG6Jw/640?wx_fmt=png&from=appmsg)

  

近年来，大模型文本检索（LLM-based Text Retrieval）技术发展迅猛，SOTA 的 LLM Embedding Model 参数量普遍在 7B 以上，相关性搜索性能提升的同时，部署成本也大幅增长。

  

众所周知，LLM Embedding Model 是一种对称式双塔结构，Query 和 Doc 侧常共享同一个完整的 LLM。但一个长期被忽视的问题是：线上推理中，查询端（Query）真的需要和文档端（Document）一样 “重” 的大模型吗？在我们最新的研究论文 LightRetriever 中，文章给出了一个明确、激进、但被大量实验证实可行的答案：不需要。

  

LightRetriever 设计了一种极致非对称式结构的 LLM Embedding Model —— Doc 侧使用完整 LLM 建模，但 Query 侧最多仅用一层 Embedding Lookup。极致化降低了 Query 侧推理负担，也能做好大模型文本搜索。对比 Query-Doc 均用完整 LLM 的标准设计，LightRetriever 让 Query 侧的推理速度提升了千倍以上、端到端 QPS 提升 10 倍，同时 BeIR、CMTEB Retreival 等测试集上的中英文检索性能也能维持 95% 左右。

  

文章由中科院信工所 & 澜舟科技共同完成，已接收于国际计算机顶级会议 ICLR 2026。ICLR（International Conference on Learning Representations）是机器学习与表示学习领域的国际顶级会议之一，与 NeurIPS、ICML 并列为人工智能方向最具影响力的学术会议。本次 ICLR 2026 共有接近 19000 篇有效投稿，接收率约为 28%。 

  

![](https://mmbiz.qpic.cn/sz_mmbiz_png/5L8bhP5dIqF7Bf7gsURRd7HMwWYJt7er2uzkOEgialH9P2bXibloPxv3aSjhjIZ13xIOECISG00nLCAkpCac7jn85CJUIs2wgmy06tBFaibYcM/640?wx_fmt=png&from=appmsg)

  

*   论文标题：LightRetriever: A LLM-based Text Retrieval Architecture with Extremely Faster Query Inference
    
*   论文链接：https://arxiv.org/abs/2505.12260
    

  

LightRetriever：极致非对称的 LLM Embedding Model

  

LightRetriever 的核心思想非常明确：将深度建模的主要计算负担彻底转移到 Doc 侧，Query 侧只保留必要、可缓存的表征能力。LightRetriever 为稠密和稀疏检索两大检索范式，分别设计了极致非对称的建模方法。

  

![](https://mmbiz.qpic.cn/mmbiz_png/5L8bhP5dIqFNMotpfia6Z0y3NPzXcANqsGLVTeypKZm48IQwG2bwlrvAcCsu95b4Tx4WMWZViabElehtBgp06PWEf6meZ1r1MdpvvicuFk6Eoo/640?wx_fmt=png&from=appmsg)

图。在稠密 / 稀疏检索中，对称式 LLM Embedding Model 使用了 1) 标准的 Full-sized Query Inference，查询侧推理负担很重；2) LightRetriever 大幅降低了查询推理成本，查询侧负载降低至不超过一层 Embedding Layer Lookup。 

  

稠密检索（Dense Retreival）训练中，Doc 侧保持建模方式不变，LightRetriever 词袋化了 Query 侧建模：完整的 LLM 接收 “指令 + 单个 Query Token” 作为输入，先建模 Token Embedding，再求平均获取 Query 句向量，并通过对比学习获得 Prompted Token Embedding。

  

![](https://mmbiz.qpic.cn/sz_mmbiz_png/5L8bhP5dIqHVtPYnvLaZdHib60dEIEedQO82A35OcuaKWIjxkJiaQMPuf9r2pfXmKDia4Bp3O3FlGPdc4WGsJWJxSA9WqPxreWSkdu0Rq3XLfs/640?wx_fmt=png&from=appmsg)

  

不同之处在于，这些 Token Embedding 在训练完成后，可以被整体缓存为一个词表级 Embedding 矩阵。在线推理时，Query 句向量的推理仅需一次简单的 Token Embedding 查表 + 求均值，不再涉及任何 L

...(截断)
