# 公众号全自动化流水线 · 项目计划

> **这是自动化项目的 single source of truth。** 每次会话开始先读这个文件，做完一步就更新状态。
> 丢了 context 不要紧，读这个文件就能接上。

## 女娲计划路线图

公众号是女娲的第一个活体实验。三步走：

| 阶段 | 目标 | 状态 |
|------|------|------|
| **MVP 最小闭环** | 选题→写作→发布，全流程自动化。人只做选题确认+发布确认 | 🟡 引擎完成（含 Pass 4.5+5），双机同步已配，发布待实测 |
| **质量进化** | 收敛搜索、迭代求导、插件化素材源、反馈驱动优化 | 🟡 Pass 5 迭代求导 ✅，收敛搜索/插件化待实施 |
| **人设与系列自主设计** | Agent 自主设计新人设、规划系列结构、选择执笔角色 | 🟡 3个新人设已建档(丁仪/智子/叶哲泰)，自动化流程已设计，待试写验证 |
| **Agent PM（项目经理）** | Agent 作为子项目经理，主动选题/调研/写作，人只在关键节点审批 | ⬜ 愿景已定义，见 WS-11 |
| **自我迭代与反馈学习** | 读取数据，对比分析，自动优化选题/写作/人设策略 | ⬜ 未开始 |

**当前聚焦：成本优化 + 下周文章 + Agent PM 架构设计**

**当前状态**：写作引擎完成，**发布管线 M2 端到端达成**（2026-03-14）。全自动 pipeline 8/8 步骤通过。已发布 8 篇，待发布 2 篇（Agent创业壁垒、Anthropic-Skill转向）。

### 场景愿景（2026-02-28 定义）

| 层级 | 场景 | 人的参与 | 状态 |
|------|------|---------|------|
| **T0** | 一键发布（30min→2min） | 确认发布 | 🟡 代码完成，待实测 |
| **T1** | 批量备稿（7篇存量） | 审稿+标记 ✅/❌ | 🟡 --batch 模式完成 |
| **T2** | 新闻反应（链接→草稿） | 发链接+指令 | 🟡 react.py 完成 |
| **T3** | 幽灵（能力自我增长） | 确认提案 | 🟡 ghost_analyze.py demo |

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

### 已有前期调研（已归档到 `wechat/归档/`）

| 文件 | 内容 | 状态 |
|------|------|------|
| `wechat/归档/AI公众号深度分析.md` | 11 个竞品账号画像、信息食物链、差异化空间 | ✅ 结论已吸收 |
| `wechat/归档/AI人设与系列开发方案.md` | 初版提案（丁仪/云天明/叶文洁），已被用户迭代替换 | ✅ 已替换 |
| `wechat/归档/robotics-research-verified.md` | Apptronik + 1X Technologies 调研数据 | ✅ 已用于机器人系列 |
| `wechat/播客与YouTube监控方案.md` | 播客/YouTube 信息源清单 + RSS feeds + 实施方案 | 待实施 |

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
  ├─ Pass 4.5 标题优化   → title_options.md + publish_guide 更新（✅ 完成）
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
| 1.6 | 调研覆盖审计（B+C） | 🟡 prompt已加，待验证 | `write_engine/deep_research.py` | **根因修复**：agent搜到"够用"叙事就停，漏掉李飞飞等关键玩家。修复方案：B=权威基准对照（搜现有综述/报告，对比自己覆盖范围）+ C=对抗性自查（"专家会说我漏了什么？"）。已加"关键玩家覆盖检查"到prompt，需泛化为通用覆盖审计（适用所有人设/系列） |

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
| 2.10 | Token 优化（-62%） | ✅ 完成 | `engine.py` + `context_loader.py` + `topic_config.yaml` | max_rounds 2→1, pass3b effort→medium, skip_fact, SHARED_CONTEXT按Pass分级, CONSENSUS_DOC压缩。98K→37K tokens/篇, 15→7次调用。`--consensus-rounds 2` 可覆盖 |
| 2.11 | Pass 4.5 标题优化 | ✅ 完成 | `engine.py` + `prompts/pass4b_title_meta.md` + `topic_config.yaml` | sonnet, 5种钩子标题+简介评分，自动注入 publish_guide。`--skip-title` / `--title "xxx"` CLI。6篇已优化 |

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
| 4.1 | mdnice 浏览器自动排版 | ✅ 完成 | `one_click_publish.py` → `mdnice_render()` | Playwright 打开 mdnice.com → 粘贴 md → 选橙心主题 → 复制富文本 |
| 4.2 | 正文注入微信编辑器 | ✅ 完成 | `publish/inject_js.py` + `publish/wechat_automator.py` | Playwright CDP + JS evaluate |
| 4.3 | 图片上传 | ✅ 完成 | `publish/https_server.py` + `js/upload_image.js` | HTTPS本地服务器 + inject_images URL dedup |
| 4.4 | 标题/简介/封面设置 | ✅ 完成 | `wechat_automator.py` _cdp_type() | 全部 JS evaluate，CDP Input 事件 |
| 4.5 | 原创声明+赞赏 | ✅ 完成 | `wechat_automator.py` enable_original/reward | 作者"降临派" + checkbox + 确认，全 JS evaluate |
| 4.6 | 投票创建 | ✅ 完成 | `wechat_automator.py` add_poll() | _cdp_type JS focus + CDP 键盘事件 |
| 4.7 | 端到端发布脚本 | ✅ 完成 | `publish/one_click_publish.py` | 全流程通过，含 --resume-from + checkpoint + 预览验证 |
| 4.8 | 草稿预览验证 | ✅ 完成 | `wechat_automator.py` open_draft_preview() | 新 tab 打开预览 + 截图 + tab 保留给用户 |

**WS-4 发布管线 M2 达成（2026-03-14）**：

全部步骤通过，已发布 OpenClaw算力涟漪 + AI就业冲击 两篇：
- ✅ Chrome CDP 连接（幂等，不杀进程）
- ✅ mdnice 排版（橙心主题）→ 正文粘贴（JS focus + Cmd+V）→ 图片注入（URL dedup，不追加到文末）
- ✅ 封面图/标题/简介/原创声明/赞赏/投票 — 全部 JS evaluate
- ✅ 保存 + 草稿预览验证（新 tab 打开预览 + 截图 + tab 保留给用户）
- ✅ `--resume-from <step>` 断点续跑 + per-article checkpoint
- ✅ `test_steps.py` 逐步测试（connect/title/desc/cover/original/reward/poll/save）

关键修复记录：
- inject_images: cdn_map 双键 URL 重复 → dedup + 删除 appendChild fallback
- verify_with_claude(): 删除（外部 AI 截图验证不稳定）→ open_draft_preview() 固化为代码
- 每篇文章独立 tab（new_post → context.new_page()），预览 tab 保留，草稿列表新开 tab

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
| 8.1 | 浏览器池（Chrome CDP） | 🟡 代码完成 | `publish/wechat_automator.py` | Playwright CDP 连接 Chrome --remote-debugging-port=9222 |
| 8.2 | 端到端发布脚本 | 🟡 代码完成 | `publish/one_click_publish.py` | 串联 render→clipboard→paste→全部元数据→保存 |
| 8.3 | Mac Mini 部署 | 🟡 SSH+auto-pull完成 | `scripts/setup_mac_mini.sh` + `scripts/git-auto-pull.sh` + `scripts/com.nuwa.git-auto-pull.plist` | SSH key 已配, launchd 5min auto-pull, sparse checkout(wechat+scripts+logs) |
| 8.4 | 批量发布 | 🟡 代码完成 | `run_pipeline.sh --publish-all` | 对所有已完成文章串行调用 one_click_publish |
| 8.5 | 新闻反应管道 | 🟡 代码完成 | `react.py` | URL→获取→选题→调研→写作→通知 |
| 8.6 | Ghost 能力缺口分析 | 🟡 demo完成 | `ghost_analyze.py` | 事件溯源→能力对照→缺口提案 |

### WS-9: 反馈数据采集（演进路线图 §五）

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 9.1 | 微信后台数据爬取 | ⬜ TODO | 浏览器自动化 | Playwright 爬 mp.weixin.qq.com 数据页 |
| 9.2 | metrics 文件自动写入 | ⬜ TODO | 9.1 | launchd 发布后 24h/48h/7d 自动采集 |
| 9.3 | 数据驱动选题权重 | ⬜ TODO | 9.2 + 攒数据 | 高转发→提升 priority，低互动→降低 |
| 9.4 | 归因分析自动生成 | ⬜ TODO | 9.2 | 每篇数据分析→写作策略反馈 |

### WS-10: 新人设与系列开发（演进路线图 §六）

**2026-03-01 更新**：用户 review 初版提案后，基于选题偏好重新定义了3个新人设。初版提案已归档。

**人设全景（6个）**：

| 人设 | 定位 | 系列 | 状态 | 档案 |
|------|------|------|------|------|
| 章北海 | 冷静温情叙事 | 独立篇 | ✅ 已验证 | `人设/章北海.md` |
| 罗辑 | 分析框架型 | 机器人系列 | ✅ 已验证（节制用） | `人设/罗辑.md` |
| 大史 | 调查记者型 | 暗线 | ✅ 已验证 | `人设/大史.md` |
| **丁仪** | 技术祛魅 | **技术祛魅** | 🟡 已建档待试写 | `候选人设和系列/丁仪.md` |
| **智子** | 涟漪观察者 | **涟漪** | 🟡 已建档待试写 | `候选人设和系列/智子.md` |
| **叶哲泰** | 先驱者讲述者 | **先驱者** | 🟡 已建档待试写 | `候选人设和系列/叶哲泰.md` |

**暂缓**：云天明（应用叙事，当前选题无刚需）、叶文洁（文明观察，需验证接受度）

| ID | 任务 | 状态 | 依赖 | 备注 |
|----|------|------|------|------|
| 10.1 | 丁仪人设建档 | ✅ 完成 | — | 技术祛魅者，系列「技术祛魅」 |
| 10.2 | 智子人设建档 | ✅ 完成 | — | 涟漪观察者，系列「涟漪」 |
| 10.3 | 叶哲泰人设建档 | ✅ 完成 | — | 先驱者讲述者，系列「先驱者」 |
| 10.4 | 「技术祛魅」系列试写 | ✅ 已发布1篇 | — | 世界模型 ✅ 已发布。Anthropic-Skill转向 待发布（差图+mdnice） |
| 10.5 | 「涟漪」系列试写 | ✅ 已发布1篇 | — | OpenClaw算力涟漪 ✅ 已发布。中国AI-Token超美 待发布 |
| 10.6 | 「先驱者」系列试写 | ✅ 已发布1篇 | — | 三局棋 ✅ 已发布 |
| 10.7 | 试写后人设迭代 | ⬜ TODO | 10.4-10.6 | 根据试写反馈调整声音/禁忌 |
| 10.8 | 确认后移入正式 `人设/` | ⬜ TODO | 10.7 | 候选 → 正式 |
| 10.9 | 人设开发自动化流程 | ⬜ TODO | — | 详见下方 |

#### 10.9 人设开发自动化流程（待实施）

**触发条件**：topic_pipeline.py 推荐选题时，自动匹配现有人设。匹配度低于阈值时触发新人设开发流程。

**自动化流程**：

```
[选题推荐] → 人设匹配评估（现有6人设）
    │
    ├── 匹配度高 → 分配人设，正常写作
    │
    └── 匹配度低 → 触发人设缺口分析
         │
         ├── Step 1: 分析缺口类型
         │   - 内容类型空白？（技术/叙事/调查/...）
         │   - 声音空白？（现有声音都不合适？）
         │   - 视角空白？（需要新的看问题方式？）
         │
         ├── Step 2: 候选人设生成
         │   - 从三体角色库中匹配（维德/程心/云天明/...）
         │   - 生成人设草案（定位/声音/禁忌/与现有区别）
         │   - 输出到 候选人设和系列/ 目录
         │
         ├── Step 3: 用户确认
         │   - 人审核候选人设（修改/通过/否决）
         │
         ├── Step 4: 试写验证
         │   - 用候选人设写一篇文章
         │   - 根据反馈迭代人设文档
         │
         └── Step 5: 归档
             - 通过 → 移入 人设/ 正式目录
             - 否决 → 归档到 归档/
```

**实施依赖**：
- topic_pipeline.py 需要新增人设匹配评分模块
- context_loader.py 需要支持读取候选人设目录
- engine.py Pass 1 需要支持候选人设注入

### WS-12: 主编 Agent（编辑审稿）— 2026-03-10 用户需求

**用户原话**："要不是能有个和我想法差不多的 AI 编辑帮忙审稿优化该多好呀"

**定位**：把用户的编辑直觉固化为 prompt，审稿标准不是通用"写得好不好"，而是**"Ciwang 会不会打回来"**。

**数据来源**（用户编辑偏好的积累）：
- `wechat/logs/interventions.jsonl` — 每次用户纠正的记录
- `wechat/内容方法论.md` — 写作规则
- `wechat/experience.jsonl` — 跨系列经验公理
- 会话中的反馈模式（配图质量/覆盖完整性/数据来源格式/根因修复...）

**实施思路**：
- 可作为 Pass 3 review 的增强版，或独立的 Pass 3.1 "主编审稿"
- prompt 注入用户偏好清单（从 interventions.jsonl 提取高频模式）
- 审查维度：素材覆盖完整性 / 配图比例与质量 / 格式规范 / 叙事节奏 / 数据来源格式
- 输出：打回清单（具体到行号+修改建议），模拟用户审稿

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| 12.1 | 从 interventions.jsonl 提取用户偏好模式 | ⬜ TODO | 聚类分析，提炼为审稿规则 |
| 12.2 | 主编 prompt 设计 | ⬜ TODO | 注入偏好规则 + 打回标准 |
| 12.3 | 集成到 engine.py | ⬜ TODO | Pass 3.1 或增强 Pass 3 |
| 12.4 | 用已发文章做回测 | ⬜ TODO | 主编能否发现用户实际打回的问题 |

### WS-11: Agent PM（项目经理）— 2026-03-08 用户愿景

**这是女娲计划的第一个数字生命**，不是 pipeline 编排器。

**完整架构设计**：[`wechat/agent/PLAN_agent_pm.md`](../../agent/PLAN_agent_pm.md)

**已确定方案**：
- **消息通道**：Telegram Bot（稳定、API 成熟、支持语音/文件/按钮）
- **Brain**：先用 `claude -p` CLI（零额外成本），接口设计为可切 API
- **运行环境**：Mac Mini daemon 7×24 + MacBook 辅助（开发 + GUI 发布）
- **记忆系统**：路径记忆（存 HOW，不存 WHAT）+ 现有三层记忆架构

**公理（DNA）**：
```
1. 存活：能让公众号持续产出高质量内容的行为是好的
2. 成长：主动思考如何让这个号活下去、商业化、扩大影响力
3. 压缩：从每次产出中压缩经验，让下次更好、更快、更少依赖人
```

**五大组件**：Gateway（Telegram daemon）+ Brain（ReAct 推理）+ Memory（路径记忆）+ Skills（封装现有工具）+ State（文章生命周期）

**主动行为**（不只是等指令）：晨间简报、选题提案、数据复盘、周报、商业化思考、能力缺口分析、公理自我挑战

**Token 预算控制**：daily_think_limit=50, daily_skill_limit=10, proactive_budget=5, heartbeat=5min

| ID | 任务 | 状态 | Phase | 备注 |
|----|------|------|-------|------|
| 11.0 | 计划落盘 + Telegram Bot 创建 | ✅ 计划已存 | 0 | PLAN_agent_pm.md 已存, 待用户创建 Telegram bot |
| 11.1 | daemon.py + gateway.py + brain.py | ⬜ TODO | 1 | asyncio 主循环 + Telegram bot + ReAct 推理 |
| 11.2 | state.py + memory.py | ⬜ TODO | 1 | 文章状态机 + 路径记忆 JSONL 持久化 |
| 11.3 | skills/react_skill.py + notify.py | ⬜ TODO | 1 | 包装 react.py + Telegram 通知 |
| 11.4 | axioms.md + config.yaml | ⬜ TODO | 1 | 公理注入 + 预算/心跳配置 |
| 11.5 | skills/select_topic + research + write + publish | ⬜ TODO | 2 | 包装全部现有工具为标准技能接口 |
| 11.6 | 完整生命周期管理 | ⬜ TODO | 2 | IDEA→RESEARCHING→...→PUBLISHED→LEARNING |
| 11.7 | proactive.py + 主动思考 | ⬜ TODO | 3 | 晨间简报/选题提案/周报/商业化思考 |
| 11.8 | self_reflect.py + 路径压缩 | ⬜ TODO | 3 | 经验压缩 + 公理挑战 + 能力缺口提案 |
| 11.9 | market_scan.py | ⬜ TODO | 3 | 竞品扫描 + 变现策略分析 |

**Phase 完成标准**：
- **Phase 1**：Telegram 发链接 → agent 调研 → 回大纲 → 确认 → 写完通知（用户只按2次手机）
- **Phase 2**：完整流程——选题推荐→确认→调研→写作→审批→发布
- **Phase 3**：连续2周自主完成 ≥3篇，第2周质量 ≥ 第1周，提出 ≥1个自我改进提案

---

## 🔴 待讨论 / 下一步（TODO）

> 2026-03-08 更新。

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
| ~~P1~~ | ~~2.11 Pass 4.5 标题优化~~ | ✅ 完成 |
| **P0** | **11.1 Agent PM 消息通道选型** | 评估微信/Telegram/飞书/文件系统方案，决定交互层 |
| **P0** | **4.7/8.2 发布实测** | one_click_publish.py 首篇实测（Mac Mini） |
| **P1** | **11.2-11.5 Agent PM 核心实现** | 消息路由+状态机+工具调度，串联现有 pipeline |
| **P1** | **6.2 收敛搜索** | deep_research.py 改为循环，新信息 <20% 时收敛 |
| **P1** | **6.3 素材质量自评估** | 信源数/一手源/观点多样性/数据点 自动评分 |
| **P2** | **6.1 插件化素材源** | SourcePlugin 基类，新源只需一个 py 文件 |
| **P2** | **9.1-9.2 微信后台数据** | Playwright 爬取 + launchd 定时 |
| **P2** | **10.4-10.6 三个新人设试写** | 丁仪(技术祛魅)、智子(涟漪)、叶哲泰(先驱者)各试写一篇 |
| **P3** | **9.3-9.4 数据驱动优化** | 需攒够数据 |
| **P3** | **11.6 Agent PM 自我迭代** | 发布数据→策略调整 |

---

## 执行顺序（2026-03-08 更新）

**已完成** ✅：
- WS-1.1-1.5（选题+素材采集全链路）
- WS-2.1-2.11（写作引擎 + 协商闭环 + Token优化-62% + Pass 4.5标题优化）
- WS-2.7 E2E 测试（Pass 5 验证通过）
- WS-3.1-3.7（全部交付物生成）
- WS-5.3（review→lessons 自动提取）
- WS-7.1-7.4（Pass 5 迭代求导全部完成）
- WS-8.3 Mac Mini 双机同步（SSH + launchd auto-pull 5min）
- 7篇文章引擎生成完毕 + 6篇标题优化完毕
- Anthropic硬刚文章更新（3/4-3/6 后记）
- 日志拆分为子项目维度（wechat/logs/ + knowledgebase/logs/ + logs/）

**当前焦点：成本优化 + 待发文章 + Agent PM**
1. **成本优化** — 🔴 当前 pipeline token 消耗过高，需评估优化方案
2. **待发文章** — Agent创业壁垒（差mdnice）、Anthropic-Skill转向（差图+mdnice）
3. **搜索质量 review** — 马斯克太空数据库为什么没在 OpenClaw 检索中出现？
4. **WS-4.7 发布管线** — ✅ M2 端到端达成（2026-03-14，已发布 OpenClaw + AI就业）
5. **WS-11 Agent PM** — ⬜ 待用户创建 Telegram Bot 后启动 Phase 1

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
8. **WS-10 新人设试写+迭代** — 丁仪(技术祛魅)→智子(涟漪)→叶哲泰(先驱者)
9. **WS-10.9 人设开发自动化** — 选题时自动匹配人设+缺口检测+候选生成
10. **女娲主项目回传** — 通用模式文档化

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
| 2026-02-28 | **周末冲刺代码全部完成** — T0: publish/render_html.py(本地CSS渲染) + clipboard_html.py(AppKit剪贴板) + wechat_automator.py(Playwright CDP) + one_click_publish.py(端到端) + theme_orange.css + scripts/setup_mac_mini.sh。T1: run_pipeline.sh --batch N + --publish-all + --persona + topic_pipeline.py --num-topics。T2: react.py(新闻反应管道)。T3: ghost_analyze.py(能力缺口demo) + prompts/ghost_gap_analysis.md。场景愿景(T0-T3)写入AUTOMATION_PLAN。 | Claude (麦老) |
| 2026-03-01 | **WS-10 人设与系列重新定义** — 用户 review 初版提案后，基于7个选题偏好迭代：①丁仪(技术祛魅)确认 ②云天明→智子(涟漪观察者，追踪产业链二阶效应) ③叶文洁→叶哲泰(先驱者讲述者，老者讲述历史)。3个新人设已建档(`候选人设和系列/`)，4个新系列已规划(技术祛魅/涟漪/先驱者/暗线)。新增10.9人设开发自动化流程设计。初版调研文档归档到`wechat/归档/`。 | Ciwang + Claude (麦老) |
| 2026-03-01 | **7篇文章批量生成** — engine.py 批量跑完全部7个选题（三局棋/世界模型/Anthropic-Skill/中国AI-Token超美/Anthropic硬刚/OpenClaw涟漪/Agent创业壁垒），全套交付物就位 | Claude (麦老) |
| 2026-03-04 | **WS-2.10 Token优化 -62%** — max_rounds 2→1, pass3b effort→medium, skip_fact, SHARED_CONTEXT按Pass分级, CONSENSUS_DOC压缩。实测98K→37K tokens/篇。新增 `--consensus-rounds` CLI。AUTOMATION_PLAN 加入公众号必读 checklist | Claude (麦老) |
| 2026-03-04 | **轻量 clone 能力** — `scripts/clone_wechat.sh` + `.claude/skills/sparse-clone/` skill。其他电脑只拉公众号目录(~30M vs 1.3G) | Claude (麦老) |
| 2026-03-08 | **WS-2.11 Pass 4.5 标题优化完成** — prompts/pass4b_title_meta.md + engine.py run_pass4b() + _update_publish_guide()。sonnet, 5种钩子标题+简介评分。6篇未发布文章全部标题优化。sonnet vs opus 对比：质量接近，选 sonnet 省成本 | Claude (麦老) |
| 2026-03-08 | **Mac Mini 双机同步** — scripts/git-auto-pull.sh + com.nuwa.git-auto-pull.plist(launchd 5min)。Mac Mini SSH key 配置完成（ed25519→GitHub）。日志拆分为子项目维度（wechat/logs/ + knowledgebase/logs/ + logs/） | Ciwang + Claude (麦老) |
| 2026-03-08 | **Anthropic硬刚文章更新** — 新增3/4-3/6后记（泄露备忘录/"straight up lies"/重开谈判/Amodei道歉），更新时间线+数据源。重跑 Pass 4.5 标题优化 | Claude (麦老) |
| 2026-03-08 | **WS-11 Agent PM 愿景定义** — 用户提出：Agent 作为公众号项目经理，手机发链接+几句话→调研→大纲→写作→发布，人只在关键节点审批。利用零碎心智，Agent 自主管理全流程。技术方案候选：微信bot/Telegram/飞书/文件系统。新增 WS-11.1-11.6 | Ciwang + Claude (麦老) |
