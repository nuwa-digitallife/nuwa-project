# 公众号全自动化流水线 · 项目计划

> **这是自动化项目的 single source of truth。** 每次会话开始先读这个文件，做完一步就更新状态。
> 丢了 context 不要紧，读这个文件就能接上。

## 女娲计划路线图

公众号是女娲的第一个活体实验。三步走：

| 阶段 | 目标 | 状态 |
|------|------|------|
| **MVP 最小闭环** | 选题→写作→发布，全流程自动化。人只做选题确认+发布确认 | 🟡 引擎完成（含 Pass 5），待发布串联 |
| **质量进化** | 收敛搜索、迭代求导、插件化素材源、反馈驱动优化 | 🟡 Pass 5 迭代求导 ✅，收敛搜索/插件化待实施 |
| **人设与系列自主设计** | Agent 自主设计新人设、规划系列结构、选择执笔角色 | 🟡 已有调研和提案 |
| **自我迭代与反馈学习** | 读取数据，对比分析，自动优化选题/写作/人设策略 | ⬜ 未开始 |

**当前聚焦：MVP E2E 测试 → 质量进化**

**当前状态**：写作引擎代码完成（含协商闭环 + Pass 5 迭代求导），E2E 验证通过。演进路线图已制定。

**详细演进路线图**：[`write_engine/PLAN_evolution_roadmap.md`](../../write_engine/PLAN_evolution_roadmap.md)

### 双循环架构（2026-02-28 感悟沉淀）

上面的路线图是**循环1（内容生产）**的流水线。但实践中发现还有一个隐性循环：

**循环1：内容生产** — 选题→写作→发布→反馈→回写经验→下一篇。上面所有 WS 都在服务这个循环。

**循环2：能力生产** — 循环1每次人手动干预的地方 = 循环2的种子。例：发现需要新监控源 → 系统生成能力提案 → 人确认 → 系统自己写代码部署。循环1产出文章，循环2产出让循环1变强的代码和配置。

**落地方式**：不提前设计循环2。先跑通循环1，每次手动干预时记一条 log（干预类型/位置/原因）。跑几周后 log 聚类，循环2结构自然涌现。

### 六层框架中 AUTOMATION_PLAN 缺失的层（来自感悟）

AUTOMATION_PLAN 已覆盖：构建原子（WS-1~4）、反馈链路（WS-5/9）。以下三层尚无对应工作项：

| 层 | 含义 | 当前状态 | 落地时机 |
|---|---|---|---|
| **目标函数** | 每一圈转完，系统变强了还是没变？度量：质量上升 or 人介入步骤减少 | ⬜ 无度量 | 循环1跑通后，从 metrics + 人介入 log 中定义 |
| **心智交互界面** | 输入：人从任何终端最小成本扔碎片进系统；输出：系统压缩成5分钟可 review 的决策点 | 🟡 晨间清单（WS-6.5）是雏形 | P2 异步人机协作 |
| **自我强化** | 每圈自动：压缩经验 + 更新参数 + 降低人介入节点数 | ⬜ 经验压缩有（5.3），参数更新和节点削减无 | P3+ |

### 已有前期调研

| 文件 | 内容 |
|------|------|
| `wechat/AI公众号深度分析.md` | 11 个竞品账号画像、信息食物链、差异化空间 |
| `wechat/AI人设与系列开发方案.md` | 3 个新人设提案（丁仪/云天明/叶文洁）+ 系列规划 |
| `wechat/播客与YouTube监控方案.md` | 播客/YouTube 信息源清单 + RSS feeds + 实施方案 |

---

## 架构总览

```
[每日信息采集]          ← auto_import.py (✅ launchd 10:00)
[播客/YouTube 监控]     ← ⬜ 待建（详见 播客与YouTube监控方案.md）
       ↓
[选题推荐]              ← topic_pipeline.py (✅ launchd 23:00)
       ↓
[人工：选题确认]         ← 人决策（保留）
       ↓
[素材深度采集]           ← deep_research.py (✅ 接入 run_pipeline.sh)
  └─ 收敛搜索            ← ⬜ 待建：梯度下降式采集，新信息 <20% 时收敛
       ↓
[多Agent写作]           ← engine.py (✅ 完成，E2E 验证通过)
  ├─ Pass 1 写作Agent    → article_draft.md
  ├─ Pass 2 事实核查      → factcheck_report.md + article_factchecked.md
  ├─ Pass 3 审视Agent    → review_report.md（纯 review，不改文章）
  ├─ Pass 3.5 协商闭环   → consensus_doc.md + article_reviewed.md
  ├─ Pass 4 整合Agent    → article.md / article_mdnice.md / poll.md / publish_guide.md
  └─ Pass 5 迭代求导     ← ✅ 完成：薄弱点审计→定向调研→重写→版本对比→收敛判断（--iterate）
       ↓
[交付物补全]            ← ✅ 封面图(Gemini) + 配图采集(截图+matplotlib+Gemini)
       ↓
[发布]                  ← 🟡 各步骤有脚本，缺端到端串联
       ↓
[人工：发布确认]         ← 人决策（保留）
       ↓
[数据反馈]              ← ⬜ 待建：Playwright 爬微信后台数据
       ↓
[经验回传]              ← 🟡 review→lessons ✅ | metrics→选题权重 ⬜ | 人肉→experience.jsonl 🟡
  └─ 公理PK              ← 🟡 人工运行中：新经验 vs 旧公理，数据裁判，淘汰/压缩
       ↓
[人设轮换检查]           ← ⬜ 待建：选题时自动检查最近3篇人设，≥3连续则提示轮换
       ↓
 ↺ 循环1 回到 [选题推荐]
       ↓
[循环2: 能力生产]        ← ⬜ 先记 log（每次人手动干预），跑通循环1后涌现
```

---

## 工作项

### WS-1: 选题与素材采集（上游）

| ID | 任务 | 状态 | 文件 | 备注 |
|----|------|------|------|------|
| 1.1 | 每日信息采集 | ✅ 完成 | `knowledgebase/wx-article-cron/auto_import.py` | launchd 每日10:00 |
| 1.2 | 选题推荐 | ✅ 完成 | `wechat/tools/topic_pipeline.py` | launchd 每晚23:00，Google News RSS + 公众号素材 |
| 1.3 | 素材深度采集 | ✅ 完成 | `write_engine/deep_research.py` | 多路中英文 web search + 一手源追溯 + 交叉验证，输出到 `素材/deep_research.md` |
| 1.5 | deep_research 接入 run_pipeline.sh | ✅ 完成 | `run_pipeline.sh` Phase 1.5 | full 和 --topic 模式都会在写作前先跑深采 |
| 1.4 | 选题配置优化 | 🟡 可用但粗糙 | `wechat/tools/topic_config.yaml` | 关键词和权重需要根据发布数据迭代 |

### WS-2: 多Agent写作引擎（核心，优先级最高）

| ID | 任务 | 状态 | 文件 | 备注 |
|----|------|------|------|------|
| 2.1 | 重写 run_pipeline.sh Phase 2 | ✅ 完成 | `wechat/tools/run_pipeline.sh` | 已改为调用 write_engine/engine.py，opus 4-pass |
| 2.2 | Pass 1 写作 prompt 设计 | ✅ 完成 | `write_engine/prompts/pass1_write.md` | 人设注入+方法论+经验库+素材+[待验证]/[配图]标记 |
| 2.3 | Pass 2 事实核查 prompt 设计 | ✅ 完成 | `write_engine/prompts/pass2_factcheck.md` | 逐条验证+2信源+时间推导+引用归属+陌生人名审计 |
| 2.4 | Pass 3 审视 prompt 设计 | ✅ 完成 | `write_engine/prompts/pass3_review.md` | 完整Review checklist+三层恰+类型专属(分析/叙事/调查)+人设检查 |
| 2.5 | Pass 4 整合 prompt 设计 | ✅ 完成 | `write_engine/prompts/pass4_integrate.md` | 合并修正+全部交付物(article/mdnice/poll/guide/简介) |
| 2.6 | 启动 checklist 自动化 | ✅ 完成 | `write_engine/context_loader.py` | 自动读取方法论+人设+经验库+系列lessons+素材 |
| 2.7 | 端到端测试 | ✅ 完成 | — | Pass 5 E2E 验证通过（机器人棋局，sonnet，1轮迭代）。10个P1弱点→算术错误修正+CMO具名+过渡句升级→CONVERGED |
| 2.8 | 跨Pass上下文共享 | ✅ 完成 | `context_loader.py` | 共享上下文层（素材摘要+人设+方法论核心）注入所有 Pass |
| 2.9 | Pass 3.5 协商闭环 | ✅ 完成 | `engine.py` + 6个 pass3b prompt | Writing Agent 回应→Fact Agent 回应→Review Agent 评估→执行修改→验收 |

### WS-3: 交付物生成

| ID | 任务 | 状态 | 文件 | 备注 |
|----|------|------|------|------|
| 3.1 | article_mdnice.md 文本生成 | ✅ 完成 | Pass 4 输出 | 无H1、图片标记替换为HTML注释。人工粘贴到 mdnice 排版 |
| 3.2 | 封面图生成 | ✅ 完成 | `engine.py` → `gen_image.py` | Gemini API，深色太空科技感，900x383，不放文字。引擎 Pass 4 后自动生成 |
| 3.3 | 投票 poll.md 自动生成 | ✅ 完成 | Pass 4 整合Agent输出 | 顺着文末情绪生成，不设截止日期 |
| 3.4 | publish_guide.md 自动生成 | ✅ 完成 | Pass 4 整合Agent输出 | 含文件清单+简介备选+配图位置+发布步骤 |
| 3.5 | review_report.md 自动生成 | ✅ 完成 | Pass 3 审视Agent输出 | 三层恰完整报告 |
| 3.6 | 配图采集/生成 | ✅ 完成 | `write_engine/image_collector.py` | 三类配图自动化：①实物截图(web search via claude -p) ②数据图(matplotlib via claude -p) ③AI生图(gen_image.py/Gemini)。引擎 Pass 4 后自动采集 |
| 3.7 | factcheck_report.md | ✅ 完成 | Pass 2 输出 | 逐条核查 + 时间推导 + 陌生人名审计 |

### WS-4: 发布上传

| ID | 任务 | 状态 | 文件 | 备注 |
|----|------|------|------|------|
| 4.1 | ~~Markdown→HTML 本地渲染~~ | ❌ **已废弃** | ~~`publish/md_to_html.py`~~ | 用户否决。改用 mdnice 网站粘贴排版 |
| 4.1b | mdnice 排版 | 🟡 人工 | — | article_mdnice.md 粘贴到 mdnice → 复制到微信编辑器 |
| 4.2 | 正文注入微信编辑器 | ✅ 完成 | `wechat/tools/publish/inject_js.py` | UTF-8 已修复（备选方案，和 mdnice 粘贴二选一） |
| 4.3 | 图片上传 | ✅ 完成 | `wechat/tools/publish/https_server.py` + `js/upload_image.js` | HTTPS本地服务器方案 |
| 4.4 | 标题/简介/封面设置 | 🟡 有JS脚本 | `js/set_title.js` `js/set_description.js` | 需要 Chrome 已登录 |
| 4.5 | 原创声明+赞赏 | 🟡 有JS脚本 | `js/enable_original_reward.js` | 需测试稳定性 |
| 4.6 | 投票创建 | ❌ 未开始 | — | 目前只能手动 |
| 4.7 | 端到端发布脚本 | ❌ 未开始 | — | 串联 4.1-4.6 成一键发布 |

### WS-5: 反馈闭环

**三层记忆架构**（内容方法论 9-23行）：
- **公理层** `experience.jsonl` — 跨系列通用规则。人工判断后写入，不自动写。
- **系列层** `公众号已发/{系列}/lessons.md` — 系列专属经验。可从 review 自动提取。
- **人设层** `人设/{角色名}.md` — 角色特有发现。很少变动。

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 5.1 | 微信后台数据采集 | ⬜ TODO | Chrome登录 | 无官方API，方案待定。**用户先人肉反馈** |
| 5.2 | metrics 文件自动写入 | ⬜ TODO | 5.1 | 采集后写入 `公众号已发/{系列}/XX-metrics.md` |
| 5.3 | review→lessons 自动提取 | ✅ 完成 | `engine.py` extract_lessons_from_review() | Pass 3 的"改进行动/下篇需注意"自动追加到系列 lessons.md |
| 5.4 | 选题权重反馈 | ⬜ TODO | 5.2 | **用户先人肉反馈**，攒几篇数据后再自动化 |
| 5.5 | 公理层经验写入 | 🟡 人工 | — | experience.jsonl 需人工判断什么值得提炼为公理，不自动写 |
| 5.6 | 公理PK机制 | 🟡 人工运行中 | 5.5 | 新经验回传后变成"待检验公理"，挑战现有公理。用子项目实际数据做裁判（如：罗辑×3→负面感知→推翻"人设固定效果好"）。不合理的淘汰或压缩成新版本。当前人工执行，未来半自动化：引擎自动检测新经验与已有公理的冲突并标记，人做最终裁决 |
| 5.7 | 人设轮换自动检查 | ⬜ TODO | 1.2 | topic_pipeline.py 选题推荐时自动检查最近3篇的执笔人设，连续≥3篇同一人设时强制提示轮换。当前排序：章北海 > 大史 > 罗辑 |
| 5.8 | 框架去重参考 | ⬜ TODO（弱约束） | 2.2 | Pass 1 写作 prompt 注入已用框架列表（五维棋力/四种棋路/翻底牌/...）作为参考，提醒避免重复。不做硬性阻断 |

### WS-6: 素材源增强（演进路线图 §一）

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 6.1 | 插件化素材源架构 | ⬜ TODO | 2.7 E2E 完成 | SourcePlugin 基类 + 注册表，新源只需写一个 py 文件 |
| 6.2 | 收敛搜索（梯度下降式） | ⬜ TODO | 2.7 | deep_research.py 改为循环，覆盖率 >80% 时停 |
| 6.3 | 素材质量自评估 | ⬜ TODO | 6.2 | 信源数/一手源占比/观点多样性/数据点 自动评分 |
| 6.4 | 播客/YouTube 源插件 | ⬜ TODO | 6.1 | 详见 `播客与YouTube监控方案.md` |
| 6.5 | 异步人机协作（晨间任务清单） | ⬜ TODO | P2 | 引擎写待确认事项到文件，用户早上看 |

### WS-7: 迭代求导 Pass 5（演进路线图 §三）

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 7.1 | 薄弱点分析 prompt | ✅ 完成 | 2.7 | `pass5_weakness.md`：逐段证据硬度(强/中/弱/纯修辞) + 叙事连贯性检测 |
| 7.2 | 定向调研 + 弱段替换 | ✅ 完成 | — | `pass5_targeted_research.md` + `pass5_rewrite.md`：一手源优先搜弱点 + 外科手术式替换 |
| 7.3 | 版本对比 prompt | ✅ 完成 | 7.1 | `pass5_compare.md`：证据硬度变化 + 叙事连贯性回归检查 + 收敛判断 |
| 7.4 | engine.py 集成 | ✅ 完成 | 7.1-7.3 | `--iterate` + `--max-iterations` + `run_iteration_loop()`。双写 article.md + article_iterated.md |

### WS-8: 发布自动化提升（演进路线图 §四）

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 8.1 | 浏览器池（Browser Pool） | ⬜ TODO | — | 长驻 Playwright 进程 / Chrome CDP 直连 |
| 8.2 | 端到端发布脚本 | ⬜ TODO | 8.1 | `one_click_publish.py` 串联 4.1-4.6 |
| 8.3 | Mac Mini 多端同步 | ⬜ TODO | — | Git 自动 commit+push + setup_new_machine.sh |

### WS-9: 反馈数据采集（演进路线图 §五）

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 9.1 | 微信后台数据爬取 | ⬜ TODO | 浏览器自动化 | Playwright 爬 mp.weixin.qq.com 数据页 |
| 9.2 | metrics 文件自动写入 | ⬜ TODO | 9.1 | launchd 发布后 24h/48h/7d 自动采集 |
| 9.3 | 数据驱动选题权重 | ⬜ TODO | 9.2 + 攒数据 | 高转发→提升 priority，低互动→降低 |
| 9.4 | 归因分析自动生成 | ⬜ TODO | 9.2 | 每篇数据分析→写作策略反馈 |

### WS-10: 新人设与系列开发（演进路线图 §六）

**前期调研已完成**：`AI公众号深度分析.md` + `AI人设与系列开发方案.md`

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 10.1 | 丁仪人设建档 | ⬜ TODO | 用户确认 | 技术解构者，覆盖模型发布(18.9%最大空白) |
| 10.2 | 「拆机」系列试写 | ⬜ TODO | 10.1 | 用一个大模型发布选题试水 |
| 10.3 | 云天明人设建档 | ⬜ TODO | 用户确认 | 应用叙事者，覆盖 AI 落地(10.5%) |
| 10.4 | 叶文洁人设评估 | ⬜ TODO | P1 数据反馈 | 文明观察者，审慎推荐 |

---

## 🔴 待讨论 / 下一步（TODO）

> 2026-02-26 会话中与 Ciwang 对齐后的状态。

### 已确认的方案

| 项 | 决定 |
|----|------|
| 封面图 | Gemini API (`gen_image.py`)，需接入引擎自动调用 |
| 正文配图 | 三类混合（方法论140-157行）：实物截图 > 自制数据图(matplotlib) > AI生图(Gemini)。蒸馏门是范本 |
| HTML渲染 | **废弃 md_to_html.py**。用 mdnice 网站排版（人工粘贴 article_mdnice.md） |
| review 经验 | "下篇需注意" → 写入 **系列 lessons.md**（不是 experience.jsonl） |
| experience.jsonl | 公理层，人工判断后才写入 |
| 5.1/5.4 数据反馈 | 先人肉反馈，记 TODO |

### 待做（按优先级）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| ~~P0~~ | ~~2.7 E2E 测试~~ | ✅ 完成 |
| ~~P1~~ | ~~7.1-7.4 Pass 5 迭代求导~~ | ✅ 完成 |
| **P1** | **6.2 收敛搜索** | deep_research.py 改为循环，新信息 <20% 时收敛 |
| **P1** | **6.3 素材质量自评估** | 信源数/一手源/观点多样性/数据点 自动评分 |
| **P2** | **8.2 端到端发布脚本** | one_click_publish.py 串联所有发布步骤 |
| **P2** | **6.1 插件化素材源** | SourcePlugin 基类，新源只需一个 py 文件 |
| **P2** | **8.1 浏览器池** | Chrome CDP 直连 / 长驻 Playwright |
| **P2** | **8.3 Mac Mini 多端同步** | Git 自动同步 + setup_new_machine.sh |
| **P2** | **9.1-9.2 微信后台数据** | Playwright 爬取 + launchd 定时 |
| **P3** | **10.1-10.2 丁仪人设 + 拆机系列** | 覆盖模型发布空白，需用户确认 |
| **P3** | **9.3-9.4 数据驱动优化** | 需攒够数据 |
| **TODO** | 选题管理 Web App | 等核心流水线稳定后再做 |

---

## 执行顺序（2026-02-27 更新）

**已完成** ✅：
- WS-1.1-1.5（选题+素材采集全链路）
- WS-2.1-2.9（写作引擎 + 共享上下文 + 协商闭环）
- WS-2.7 E2E 测试（Pass 5 验证通过）
- WS-3.1-3.7（全部交付物生成）
- WS-5.3（review→lessons 自动提取）
- WS-7.1-7.4（Pass 5 迭代求导全部完成）

**当前焦点：P1 质量进化**
1. **WS-6.2 收敛搜索** — ⬜ deep_research.py 改为循环，新信息 <20% 时收敛
2. **WS-6.3 素材质量自评估** — ⬜ 信源数/一手源/观点多样性 自动评分

---

### 三机并行协同方案（2026-02-27 确定）

E2E 测试通过后，三台机器并行开发，按目录边界隔离避免冲突。

**分工**：

| 机器 | 角色 | Phase 2 任务 | 主要改动目录 | 模型档位 |
|------|------|-------------|-------------|---------|
| **本机** | 引擎核心 | Pass 5 迭代求导 (WS-7) | `write_engine/engine.py`, `prompts/` | opus |
| **Mac Mini** | 后台采集 | 收敛搜索 (WS-6.2) + 插件化素材源 (WS-6.1) + Twitter 部署 | `write_engine/deep_research.py`, `write_engine/sources/`(新), `twitter/` | sonnet |
| **MacBook** | 发布+反馈 | 浏览器池 (WS-8.1) + 发布脚本 (WS-8.2) + 微信数据采集 (WS-9.1) | `wechat/tools/publish/`, `wechat/tools/feedback/`(新) | sonnet + GUI |

**Git 协同**：
- 每台机器一个 feature 分支（`feat/engine-pass5`, `feat/convergent-search`, `feat/publish-pipeline`）
- 做完一个任务 merge 回 main，再拉新分支
- 本文件 (AUTOMATION_PLAN.md) 标注 `机器` 列，每台 Claude Code 启动时读此文件确认分工

**限流策略**：三台共享同一 Claude 订阅，错开重计算任务。Mac Mini / MacBook 用 sonnet 为主。

**时序**：
- Phase 1（当前）：本机跑 E2E 测试 → debug
- Phase 2（E2E 通过后）：三台并行各自任务
- Phase 3：合并分支 → 集成测试 → 分配 P3 任务

---

**P1 质量进化（Phase 2 三机并行）**
2. **WS-6.2 收敛搜索** — Mac Mini
3. **WS-7 Pass 5 迭代求导** — 本机
4. **WS-6.3 素材质量自评估** — Mac Mini（随 6.2 一起做）

**P2 扩展能力（Phase 2 三机并行）**
5. **WS-8 发布自动化** — MacBook
6. **WS-6.1 插件化素材源** — Mac Mini
7. **WS-9 反馈数据** — MacBook

**长期：P3 进化**
8. **WS-10 新人设/系列** — 丁仪→云天明→叶文洁
9. **女娲主项目回传** — 通用模式文档化

**暂缓**：
- WS-4 发布串联 — 并入 WS-8 MacBook 统一处理
- WS-5.1/5.4 数据反馈 — 并入 WS-9 MacBook 统一处理

---

## 变更记录

| 日期 | 变更 | 操作人 |
|------|------|--------|
| 2026-02-26 | 初始化计划，审计现有代码 | Claude (麦老) |
| 2026-02-25 | topic_pipeline.py + run_pipeline.sh 创建 | Claude + Ciwang |
| 2026-02-26 | publish/ 工具包完善（md_to_html重写、inject_js修复） | Claude + Ciwang |
| 2026-02-26 | **WS-2 多Agent写作引擎完成** — write_engine/ 目录：engine.py(orchestrator) + context_loader.py + 4个prompt模板。run_pipeline.sh Phase 2 已改为调用 engine.py。待端到端测试 | Claude (麦老) |
| 2026-02-26 | **WS-1.3 素材深度采集完成** — deep_research.py：多路中英web search + 一手源追溯 + 交叉验证。未接入 run_pipeline.sh | Claude (麦老) |
| 2026-02-26 | **缺口审计** — 标记交付物缺口（封面图/配图/HTML渲染串联）+ 反馈链路全部未建 + 添加待讨论 TODO | Claude (麦老) |
| 2026-02-26 | **与用户对齐** — 封面图=Gemini、配图=三类混合、HTML渲染=废弃改用mdnice、review→series lessons(不是experience)、5.1/5.4=先人肉 | Ciwang + Claude |
| 2026-02-26 | **三项接入完成** — ①run_pipeline.sh 插入 Phase 1.5 deep_research ②engine.py 后处理：review→lessons自动提取 ③engine.py 后处理：Gemini封面图自动生成 | Claude (麦老) |
| 2026-02-27 | **WS-3.6 配图采集完成** — image_collector.py：解析[配图]标记→分类(实物/数据/AI)→claude -p搜索下载+matplotlib生成+Gemini AI图。已接入engine.py后处理 | Claude (麦老) |
| 2026-02-27 | **代码重构** — ①topic_pipeline.py 拆分完成（755→160行CLI + material_collector.py + topic_recommender.py）②模型/预算配置集中到 topic_config.yaml models section，run_pipeline.sh 从 config 读取 MODEL_DEEP/MODEL_WRITE ③gen_image.py 移入 write_engine/ ④所有模块统一从 topic_config.yaml 读取配置，不再硬编码 | Claude (麦老) |
| 2026-02-27 | **预算→Effort 迁移** — ①移除所有 --max-budget-usd（订阅制无需预算控制）②全面改用 --effort (low/medium/high) 控制 extended thinking 深度 ③新增 run_claude_with_retry()：5次短间隔重试(60s) → 2h冷却 → 5次短间隔重试 → 放弃。deep_research.py 和 image_collector.py 统一使用 ④记录 WS-6 Web App TODO（低优先级） | Claude (麦老) |
| 2026-02-27 | **WS-2.8+2.9 协商闭环实施** — engine.py 重写：Pass 3 改为纯 Review（不改文章）→ Pass 3.5 consensus_loop（Writing Agent 回应→Fact Agent 回应→Review Agent 评估→执行修改→验收）→ Pass 4 接收 consensus_doc。topic_config.yaml 新增 consensus + pass3b_effort/tools 配置。pass4_integrate.md 补充 CONSENSUS_DOC 占位符。上一会话已完成：context_loader.py 全部 assemble 方法 + 7个 prompt 模板 | Claude (麦老) |
| 2026-02-27 | **演进路线图制定** — 覆盖 6 大方向：①素材源插件化+收敛搜索 ②Pass 3 Review标准梳理 ③Pass 5 迭代求导 ④发布自动化(浏览器池+Mac Mini多端) ⑤反馈闭环(Playwright爬微信后台) ⑥新人设/系列开发。新增 WS-6~10 追踪。引用已有调研：AI公众号深度分析.md + AI人设与系列开发方案.md + 播客与YouTube监控方案.md。详见 `write_engine/PLAN_evolution_roadmap.md` | Ciwang + Claude (麦老) |
| 2026-02-27 | **三机并行协同方案确定** — 本机(引擎核心/opus) + Mac Mini(后台采集/sonnet) + MacBook(发布+反馈/sonnet+GUI)。按目录边界隔离，Git feature branch 协同。engine.py 修复嵌套调用（env -u CLAUDECODE）。E2E sonnet 管道测试启动。 | Ciwang + Claude (麦老) |
| 2026-02-28 | **感悟→计划回传** — 从 nuwa-insights.md + 内容方法论对照 AUTOMATION_PLAN 缺口，补充：①双循环架构（循环1内容+循环2能力）②六层框架缺失层（目标函数/心智交互/自我强化）③公理PK机制（WS-5.6）④人设轮换自动检查（WS-5.7）⑤框架去重参考（WS-5.8，弱约束）。架构总览图更新。 | Ciwang + Claude (麦老) |
| 2026-02-28 | **WS-7 Pass 5 迭代求导完成** — 4个prompt模板(weakness/targeted_research/rewrite/compare) + context_loader 4个assemble方法 + engine.py 5个函数 + CLI --iterate/--max-iterations。E2E验证通过（机器人棋局，sonnet，1轮：10个P1→算术修正+CMO具名+过渡句升级→CONVERGED）。write_engine/ 全量入库 git。人工干预：article.md 接口契约→双写设计。协作协议新增 §4.6 人工干预记录规则。 | Ciwang + Claude (麦老) |
