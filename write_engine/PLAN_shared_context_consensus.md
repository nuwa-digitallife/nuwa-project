# Plan: 跨 Pass 上下文共享 + 优化共识协商机制

> **状态：✅ 已实施**
> **创建：2026-02-27（从上一会话截图恢复）**
> **完成：2026-02-27**

## Context

当前引擎 4 个 Pass 各自为政：Pass 2 没有人设/方法论，Pass 3 没有素材，Pass 4 什么都没有。
更关键的是，Pass 3 既当裁判又当运动员——自己提问题自己改文章，写作 Agent 没有"应诉"机会。
内容方法论（lines 314-329）定义了"优化共识"协议，蒸馏门实战证明了多轮协商的价值。
当前引擎完全缺失这个机制。

## 改动总览

三大改动：
1. **共享上下文层**：所有 Pass 注入统一的共享上下文（素材摘要 + 人设 + 方法论核心）
2. **Pass 3 他怡数据补全**：Pass 3 能看到素材阶段已采集的同主题公众号文章，用于他怡对比
3. **Pass 3+3.5 协商闭环**：Pass 3 只出 review 报告 → 多轮协商循环 → 执行修改 → 验收 → 放行

---

## 一、共享上下文层

### 设计

引入 `shared_context` 概念，所有 Pass 都能看到：

| 共享内容 | 来源 | 处理 |
|---------|------|------|
| 素材摘要 | topic_dir/素材/ | 取 deep_research.md 的「核心事实」「时间线」「数据表」段，截断到 ~3000 chars |
| 人设身份 | 人设/{name}.md | 取前 50 行（身份+核心特征，不含完整语料库）|
| 方法论核心 | 内容方法论.md | 提取「铁律」+「写作规则」+「Review 铁律」段，~2000 chars |
| 经验库 | experience.jsonl | 最近 10 条，~1000 chars |

总共 ~6-7k chars 共享层，每个 Pass 都注入。各 Pass 在共享层之上叠加自己的专属上下文。

### 改后各 Pass 上下文

| 上下文 | 共享层 | Pass 1 专属 | Pass 2 专属 | Pass 3 专属 | Pass 3.5 专属 | Pass 4 专属 |
|--------|--------|-------------|-------------|-------------|---------------|-------------|
| 素材摘要 | ✅ | – | – | – | – | – |
| 人设摘要 | ✅ | – | – | – | – | – |
| 方法论核心 | ✅ | – | – | – | – | – |
| 经验库 | ✅ | – | – | – | – | – |
| 完整素材 | – | ✅ | ✅ | – | – | – |
| 同主题公众号文章 | – | – | – | ✅(他怡) | – | – |
| 完整人设 | – | ✅ | – | ✅ | – | – |
| 系列经验 | – | ✅ | – | – | – | – |
| 文章草稿 | – | – | ✅ | – | – | ✅ |
| 核查报告 | – | – | – | – | – | ✅ |
| 核查后文章 | – | – | – | ✅ | – | – |
| 系列已发文章 | – | – | – | ✅(他怡) | – | – |
| Review 报告 | – | – | – | ✅ | ✅ | ✅ |
| 共识文档 | – | – | – | – | ✅(累积) | ✅ |
| 终稿(共识后) | – | – | – | – | – | ✅ |

### 文件改动

**context_loader.py:**
- 新增 `build_shared_context(topic_dir, persona_name)` → 返回 dict `{"SHARED_CONTEXT": "..."}`
- 新增 `load_materials_summary(topic_dir)` → 提取 deep_research.md 核心段落，截断到 ~3000 chars
- 新增 `load_persona_summary(name)` → 人设前 50 行
- 新增 `load_methodology_core()` → 提取铁律+写作规则+Review铁律
- 新增 `load_competitor_articles(topic_dir)` → 读取素材中其他公众号文章摘要，用于 Pass 3 他怡
- 每个 `assemble_passN_context()` 都合并 `build_shared_context()`

**prompts/system_common.md:**
- 扩展：注入 `{{SHARED_CONTEXT}}` 占位符
- 包含：身份声明 + 素材摘要 + 人设摘要 + 方法论核心 + 经验库

---

## 二、Pass 3 改为纯 Review（不改文章）+ 他怡数据补全

### 他怡数据源

素材采集阶段（material_collector + deep_research）已经收集了同主题的公众号文章，存在：
- `素材/{公众号名}/{文章标题}.md` — 各家公众号对同一选题的报道全文
- `素材/deep_research.md` 的「多方观点」「争议点」段 — 已按立场分类

Pass 3 需要读取这些素材来做他怡对比（信息密度、独特视角、数据深度）。

**context_loader.py 新增：**
- `load_competitor_articles(topic_dir)` → 读取 `素材/{公众号名}/` 下所有 md 文件，拼接为「他怡参考材料」
  - 每篇取标题 + 前 500 chars 摘要（控制总量 ~5k chars）
  - 标注来源公众号名
- `assemble_pass3_context()` 新增 `COMPETITOR_ARTICLES` 字段

**prompts/pass3_review.md:**
- 他怡段新增 `{{COMPETITOR_ARTICLES}}` 占位符
- 指令明确：「以下是素材阶段已采集的同主题文章摘要，用于他怡对比。不需要重新搜索。」

### Pass 3 输出变更

**当前：**
Pass 3 输出 `===REVIEW_REPORT===` + `===REVISED_ARTICLE===`

**改后：**
Pass 3 只输出 `===REVIEW_REPORT===`，其中包含结构化的「优化点清单」：

```
### 优化点清单

### 优化点1：[标题]
- **问题**：[具体描述]
- **严重程度**：🔴关键 / 🟡重要 / 🟢建议
- **具体位置**：[引用原文]
- **建议修改**：[具体方案]
```

不干涉出修改后的文章。

---

## 三、Pass 3.5 协商闭环（核心新增）

### 流程

```
Pass 3 输出 review_report（含优化点清单）
       ↓
  分类筛选 ——
       ↓
┌─────────────────────────────────────────────┐
│  Writing Agent 应诉（处理🔴/🟡问题）         │
│  Review Agent 验收（检查修改是否解决问题）    │
│  （重复直到所有优化点通过 或 达到上限）       │
└─────────────────────────────────────────────┘
       ↓
  Pass 4 整合
```

- Writing Agent 执行修改 + 更新文章
- Review Agent 验收 + 检验修改是否解决所有问题
- Pass 4 整合

### 详细设计

当前 pass3_review.md 把 ~500 行 review checklist 硬编在 prompt 里，但方法论.md 才是 single source of truth。

**流程：**
- `context_loader.py` 要调 `load_review_checklist()` — 从内容方法论.md 提取 review checklist（含审稿+人设铁律+写作铁律 → 一组结构化规则）
- `pass3_review.md` 硬编部分改为 checklist 占位符，用 `{{REVIEW_CHECKLIST}}` 占位符
- 具体内容从方法论.md 实时读取，确保每次更新方法论后引擎自动同步

### 模块 A：诊断（Writing Agent 回应）

**prompt: pass3b_respond.md**

Writing Agent 回应：
- 输入：review_report + 每条优化点 + 已修正的原文全文 + 共享上下文
- 输出：修改后的全文 + 回应报告
  - 接受：执行修改，说明改了什么
  - 拒绝：给出带论据的理由 / 替代方案
  - 部分：接受要点但具体修改方案不同

### 模块 B：事实验证（Fact Agent 回应）

**prompt: pass3b_factcheck.md**

- 入手点：review_report + 每条 🔴 关键优化点 + 已修正后的全文 + 共享上下文
- 输出：每个优化点的结论
  - ✅ 通过：符合事实证据，确认 OK
  - ❌ 拒绝：违反已验证事实，回退修改
  - ⚠️ 需修改：方向对但细节有误，给出建议

**优化**：如果整篇零事实类优化点，跳过 B，直接到 C

### 模块 C：验收

**C1. Review Agent 验收 (prompt: pass3b_verify.md)**

- 输入：修改后文章 + 修改前文章 + review_report 的优化点 + 修改清单
- 输出格式：

```
===VERIFICATION===
| 优化点 | 执行状态 | 通过 |
|--------|----------|------|
| 优化点1 | ✅ 已修改 | ✓ |
| 优化点2 | ❌ 拒绝 | ✓（理由成立）|
| 优化点3 | ⚠️ 未完全解决 | ✗（需再修改）|
| 优化点X | 🆕 新问题 | （发现了新问题，加入下一轮）|
```

- 通过门槛：所有 🔴 通过，🟡 不超过 2 个未解决

```
===VERIFIED_ARTICLE===
```
（只在通过验证时输出。Review Agent 标记但不修改文章——文章只有 Writing Agent 能改）

### 循环机制

循环正式名为 `consensus_loop`：
```
review → respond → (fact-check) → verify → (if needed) → review(targeted) → respond → verify → done
```

最多 2 轮（`num_revision_entries: 2`）

最终一致后：
- 通过 → 输出最终文章 + 变更日志（consensus_doc.md）
- 不通过 / 达到上限 → 输出当前最佳版本 + 未解决问题清单

---

## 四、Pass 4 输入调整

Pass 4 = 最终整合阶段

**改后输入：**
- 素材摘要（共享层）
- 核查报告（Pass 2）
- Review 报告（Pass 3）
- 验收结果（Pass 3.5 验收记录 consensus_doc）

**文件改动：**

**prompts/pass4_integrate.md:**
- 新增 `{{CONSENSUS_DOC}}` 占位符
- 替换 `{{SHARED_CONTEXT}}`（通过 system_common 注入）

**context_loader.py `assemble_pass4_context()`:**
- 新增 consensus_doc 参数

**engine.py `run_pass4()`:**
- 接收 consensus_doc 参数

---

## 五、输出文件结构

一次完整运行后，选题目录产出：

```
topic_dir/
  article_draft.md          ← Pass 1 初稿
  factcheck_report.md       ← Pass 2 核查报告
  article_factchecked.md    ← Pass 2 修正后文章
  consensus_doc.md          ← Pass 3.5 全部对话记录（含共识）
  article_reviewed.md       ← Pass 3 review 报告（不改文章）
  review_report.md          ← Pass 3 review report
  verified_revision_report.md ← Pass 3.5 验收报告
  article.md               ← Pass 4 最终版
  poll.md                  ← Pass 4 产出
  publish_guide.md         ← Pass 4 产出
  description_options.md    ← Pass 4 产出
  images/                  ← 配图
```

---

## 六、执行顺序

1. `context_loader.py` → 共享上下文 + review checklist 加载 + 他怡数据 + 所有 assemble 方法
2. `prompts/system_common.md` → 共享方法论 review → review checklist 从方法论实时读取
3. `prompts/pass3_review.md` → 改为纯 review + 他怡段 + review checklist 占位符引用方法论
4. 新增 4 个 prompt 文件：`pass3b_respond.md` / `pass3b_factcheck.md` / `pass3b_verify.md` / pass4_integrate 的改动
5. `engine.py` → Pass 3.5 `consensus_loop` + Pass 3/4 上下文串联
6. `topic_config.yaml` → Pass 3.5 各轮次模型 + consensus 参数

---

## 七、配置

**topic_config.yaml 新增：**

```yaml
models.write_engine.pass_effort:
  1.write: high        # Writing Agent 需要高
  1.5.fact: high       # Fact Agent 也要高
  3.5.read: high       # Review Agent 高
  3.5.respond: high    # Writing Agent 高
  3.5.fact: "Hour"     # 可能需要大量搜索
  3.5.verify: high     # 验收高

consensus:
  max_rounds: 2
  num_revision_entries: 2
```

---

## 八、备注

1. Python import 验证：`python -c "from write_engine.context_loader import ContextLoader"`
2. Prompt 模板验证：检查 `{{PLACEHOLDER}}` 都有对应 context_loader 输出
3. **所有改动都要读现有实现再改，不要凭空写**
