# 关键文件地图

## 每次会话必读（CLAUDE.md 规定）

| 文件 | 内容 |
|------|------|
| `wechat/tools/AUTOMATION_PLAN.md` | 公众号自动化流水线计划 + 进度追踪 |
| `wechat/内容方法论.md` | 写作规则/Review checklist/三层记忆/配图规则 |
| `docs/claude-collaboration-protocol.md` | Claude 协作协议（沟通风格/行为检测/Notion 规则）|
| `docs/zh/nuwa-plan.md` | 女娲计划完整愿景 |
| `logs/devlog.jsonl` | 开发日志（每次会话自动追加）|

## Claude 记忆系统

| 文件 | 内容 |
|------|------|
| `~/.claude/projects/.../memory/MEMORY.md` | Claude 自动记忆（前 200 行每次加载）|
| `~/.claude/projects/.../memory/startup-guide.md` | 启动 checklist 详细版 |
| `CLAUDE.md` | 项目级指令（Claude 每次自动读）|
| `~/.claude/CLAUDE.md` | 全局指令（所有项目生效）|

## 全局 Skills（`~/.claude/skills/`）

| Skill | 触发 | 功能 |
|-------|------|------|
| `/start` | 新会话说"继续" | 自动读完所有必读文件再开工 |
| `/fetch-wechat` | 给微信链接 | 通过本地 exporter 抓微信文章 |
| `/analyze` | "帮我分析下" | 4-Pass 内容分析与事实核查 |

## 公众号·降临派手记

### 核心

| 文件 | 内容 |
|------|------|
| `wechat/内容方法论.md` | 选题标准/生产流程/质量 checklist/调性标杆 |
| `wechat/experience.jsonl` | 跨系列通用经验库 |
| `wechat/人设/章北海.md` | 分析型人设（冷静温情叙事）|
| `wechat/人设/大史.md` | 调查型人设（调查记者扒皮）|
| `wechat/人设/罗辑.md` | 数据分析框架（暂停）|

### 选题与成品

| 目录 | 内容 |
|------|------|
| `wechat/公众号选题/` | 进行中的选题（每个子目录 = 一篇文章）|
| `wechat/公众号已发/` | 已发布文章归档（按系列分，含 lessons.md）|
| `wechat/公众号选题/参考文章/` | 参考素材 |

### 前期调研

| 文件 | 内容 |
|------|------|
| `wechat/AI公众号深度分析.md` | 11 个竞品账号画像 + 差异化空间 |
| `wechat/AI人设与系列开发方案.md` | 3 个新人设提案 + 覆盖矩阵 |
| `wechat/播客与YouTube监控方案.md` | 信息源清单 + RSS feeds |

## 写作引擎（`wechat/tools/write_engine/`）

| 文件 | 内容 |
|------|------|
| `engine.py` | 核心引擎（Pass 1→2→3→3.5→4 编排）|
| `context_loader.py` | 上下文组装（共享层 + 各 Pass 专属）|
| `deep_research.py` | 深度调研模块 |
| `prompts/` | 所有 Pass 的 prompt 模板 |
| `topic_config.yaml` | 配置中心（模型/搜索参数/共识参数）|
| `PLAN_evolution_roadmap.md` | 演进路线图（6 大方向）|
| `PLAN_shared_context_consensus.md` | 共享上下文 + 协商闭环计划（已实施）|

## 素材采集

| 文件 | 内容 |
|------|------|
| `wechat/tools/material_collector.py` | 素材采集（WeChat exporter + Google News）|
| `knowledgebase/wx-article-cron/auto_import.py` | 每日自动导入（launchd 10:00）|
| `knowledgebase/knowledge_base/` | 知识库存储 |
| `knowledgebase/digests/` | 每日摘要 |

## 发布工具（`wechat/tools/`）

| 文件 | 内容 |
|------|------|
| `inject_js.py` | JS 注入微信后台（图片上传等）|
| `md_to_html.py` | Markdown → HTML（本地橙心主题）|
| `mdnice_render.py` | mdnice 排版（主题选择有 bug）|

## 女娲计划

| 文件 | 内容 |
|------|------|
| `docs/zh/nuwa-plan.md` | 核心理论（压缩/公理注入/自复制）|
| `docs/zh/motivation-training.md` | 方法论（压缩-预测-校准循环）|
| `docs/claude-collaboration-protocol.md` | 协作协议 |
| `docs/zh/retrospective-2026-02-deepseek.md` | DeepSeek 复盘 |

## Notion 常用页面 ID

| 页面 | ID |
|------|-----|
| To-Do 任务管理 | `303994d02404813894b6c92e0616a5c9` |
| 主控台 | `305994d0-2404-81ce-b838-cca0a4a28e3a` |
| 公众号项目页 | `308994d024048154b3b8c9d48686cc34` |
| 女娲项目页 | `305994d02404819fa11ef6d394c719e8` |
| 内容方法论 | `30b994d0-2404-81c4-97e3-c9a9a547714b` |
| 每日 Log | `305994d0240481be8158d305a4c0782a` |
| 认知热缓存 | `303994d024048138bef8c542e4a63ce8` |
| 协作协议 | `305994d024048194bb96cd8c77ad26fc` |
