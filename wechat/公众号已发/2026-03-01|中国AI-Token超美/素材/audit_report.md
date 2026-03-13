两个审计 agent 都已完成。以下是合并后的审计报告：

---

# 审计报告：中国AI-Token超美

## 关键实体清单

**公司/组织**: OpenRouter, MiniMax, DeepSeek, 阿里云(Qwen), 智谱(GLM), Anthropic, OpenAI, 华为, 寒武纪, 长江存储, Kilo Code, GitHub, Anysphere(Cursor), 字节跳动, 腾讯, 月之暗面, 摩根大通, 百度, 科大讯飞, 欧盟EuroHPC, Silicon Box

**模型/产品**: M2.5, DeepSeek V3.2/V4, Qwen3.5, GLM-5, Claude Opus/Sonnet/Haiku, Kimi K2.5, 豆包, GitHub Copilot, Claude Code

**芯片**: 昇腾910B/C/950PR/950DT, 寒武纪590/690, 昆仑芯, 沐曦, 天数智芯, 摩尔线程, 壁仞科技, 燧原科技

**政策**: 美国出口管制实体清单, 中国50%芯片自给率目标

---

## 覆盖检查结果

### ✅ 已覆盖
- OpenRouter 61%份额 + 12.1T周token
- MiniMax M2.5 定价/性能/IPO
- DeepSeek V3.2/V4 状态
- Qwen3.5/GLM-5 定价与性能
- Anthropic 效率优势与定价
- 华为昇腾全线芯片路线图
- 寒武纪590/690
- 编程工具三足鼎立格局
- Agent Token倍增效应
- 美国出口管制 + 中国反制
- 欧盟/日本/新加坡芯片计划

### ⚠️ 需要补充

| 优先级 | 缺失实体 | 理由 |
|--------|---------|------|
| **HIGH** | **月之暗面 Kimi K2.5** | OpenRouter排名第2，周1.21T token，100-agent并行分发，直接支撑"token超美"叙事，完全未提 |
| **HIGH** | **字节跳动 豆包 (Doubao)** | DAU过亿，定价低于行业均价99.3%，价格战最激进推动者，完全未提 |
| **HIGH** | **国产芯片出货排名（IDC数据）** | 华为64万 > 昆仑芯6.9万 > 天数智芯3.8万 > 寒武纪2.6万 > 沐曦2.4万 > 燧原1.3万。素材只提华为+寒武纪，缺完整生态 |
| **MEDIUM** | **摩根大通 330% CAGR预测** | 权威第三方机构对token增长的量化验证，增强论据说服力 |
| **MEDIUM** | **Anysphere (Cursor) $1B ARR** | 强化"编程工具驱动token消耗"论点 |
| **MEDIUM** | **腾讯 AI战略** | BAT三巨头独缺腾讯，明显遗漏 |
| **LOW** | **GLM-Image（首个纯国产芯片训练SOTA模型）** | 昇腾生态成熟度佐证，但与token主线偏远 |

---

## 时效性检查结果

### ✅ 最新
| 实体 | 确认信息 |
|------|---------|
| DeepSeek V4 | 仍未正式发布，素材描述准确 |
| OpenRouter 中国模型份额 | 61%确认（2026年2月24日数据） |
| Qwen3.5 定价 | ¥0.8/¥4.8 确认 |
| GLM-5 SWE-Bench | 77.8% 确认 |
| 华为昇腾950 | 950PR Q1 2026时间表未变 |

### ⚠️ 需要更新

| 实体 | 旧值 | 新值 | 信源 |
|------|------|------|------|
| **Claude Opus 定价（严重）** | 素材第3轮写 "$15/$75" → 实际 Opus output 价格 | Opus 4.6: **$5 input / $25 output**（不是$15 output，$15是Sonnet output价格）| [Claude官方定价](https://platform.claude.com/docs/en/about-claude/pricing) |
| **MiniMax 市值** | 900亿港元（IPO首日冲高） | 截至2026年3月约**3000亿+港元**，已超越百度（3322亿） | [CTOL Digital](https://www.ctol.digital/news/minimax-stock-surges-past-baidu-market-cap-china-ai-valuation-investors/) |
| **美国实体清单数量** | 82个实体 | 多数信源报道为**80个实体**，且2026年3月有传闻将全面禁止对华AI芯片出口（H20/B20） | [BIS官方](https://www.bis.gov/press-release/commerce-further-restricts-chinas-artificial-intelligence-advanced-computing-capabilities) |
| **长江存储 HBM角色** | "长江存储HBM Q2量产" | 长江存储是**封装合作方**（混合键合技术），HBM晶圆主体是**长鑫存储(CXMT)**，目标月产1万片。需明确区分。 | [DRAM.com.cn](http://www.dram.com.cn/wap/views.asp?menuid=37&sortid=0&id=83043) |

### ❓ 待确认
| 实体 | 问题 |
|------|------|
| 寒武纪590/690 | 性能数据（690达H100的80%）来源不透明，寒武纪2025年12月曾发声明否认多项市场传闻 |

---

## 审计结论

**FAIL**

### 关键问题（3项严重）

1. **Claude Opus 定价错误** — 素材混淆了 Opus output ($25) 和 Sonnet output ($15) 的价格。文章用此计算价差倍数（"约21倍"），若基准价错，倍数也错。**需立即修正**。
2. **Kimi K2.5 完全缺失** — OpenRouter排名第2的中国模型、token超美叙事的核心驱动力之一，零覆盖。
3. **字节跳动豆包完全缺失** — DAU过亿、价格战最激进玩家，文章讨论价格战却不提豆包，说服力严重不足。

### 次要问题（3项中等）
4. MiniMax市值已从900亿涨至3000亿+，需更新
5. 缺少摩根大通 330% CAGR第三方验证
6. 长江存储vs长鑫存储角色需澄清