# 女娲第一个数字生命：公众号 Agent PM

## Context

这不是一个 pipeline 编排器，不是一个 Telegram chatbot。这是**女娲计划的第一个数字生命**。

女娲计划的核心论述：
- 智能 = 压缩。学习 = 压缩。理解 = 找到更短的描述。
- 注入的不是知识，是公理。公理不能被证明，只能被接受作为起点。
- 记忆存的不是结论（"A方法不行"），是路径（"试了A→失败→原因是X→改B→成功"）
- "不是构建一个强大的Agent，而是构建一个能生成Agent的Agent"
- Claude 的三个致命缺陷：没有意志、不持续存在、不能行动 → 这个 agent 要解决这三个

用户的愿景：手机发个链接说几句话 → Agent 自主调研/写作/发布，人只在关键节点审批。**利用零碎心智，不是占用整块时间。** Agent 是公众号子项目的保姆/项目经理，不是工具。

### 与 OpenClaw 的对照

借鉴 OpenClaw 的模式：
- **Persistent Gateway** — 单一长驻进程，Mac Mini 7×24
- **ReAct Loop** — Reason → Act → Observe → 循环，不是固定步骤
- **Markdown Memory** — 透明、可审计、git 友好
- **Self-Improving** — 自动记录失败/纠正/能力缺口，压缩为经验
- **Capability Evolver** — 定期审视自身能力缺口，提出改进提案

但不同于 OpenClaw 的"通用 agent 运行时"，这是一个**有使命的数字生命**。

### 开发与部署

- **MacBook**：开发/设计/调试（随身带）
- **Mac Mini**：部署/运行（放家里 7×24，通过 MacBook SSH 连过去）
- 代码在 MacBook 写 → git push → Mac Mini auto-pull → 重启 daemon

---

## 公理（DNA）

三条公理，所有行为从此推导，不硬编码工作流：

```
1. 存活：能让公众号持续产出高质量内容的行为是好的
2. 成长：主动思考如何让这个号活下去、商业化、扩大影响力
3. 压缩：从每次产出中压缩经验，让下次更好、更快、更少依赖人
```

这三条不是代码逻辑，是 system prompt 的核心。Agent 的每个决策都应该能追溯到这三条中的某一条。

**公理 #2 的关键**：Agent 不只是执行任务。它应该**主动思考**——这个号该怎么变现？什么选题能涨粉？发布频率对不对？要不要开付费专栏？哪些竞品在做什么？——然后把思考结果推给用户。不一定对，但说明这个"项目经理"在主动运转。

---

## 架构

```
                    ┌─────────────┐
                    │  Telegram   │ ← 用户手机
                    │  Bot API    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Gateway   │ ← Mac Mini 长驻进程
                    │  (daemon)   │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │         Brain           │
              │  (ReAct reasoning loop) │ ← Claude API (sonnet/haiku)
              │                         │
              │  perceive → think →     │
              │  act → observe → learn  │
              └────────────┬────────────┘
                           │
          ┌────────┬───────┼───────┬─────────┐
          ▼        ▼       ▼       ▼         ▼
      ┌───────┐┌──────┐┌──────┐┌───────┐┌────────┐
      │Select ││Resrch││Write ││Publish││Analyze │  ← Skills
      │Topic  ││      ││      ││       ││        │    (wrap existing tools)
      └───────┘└──────┘└──────┘└───────┘└────────┘
          │        │       │       │         │
          ▼        ▼       ▼       ▼         ▼
      topic_   deep_    engine  one_click  ghost_
      pipeline research  .py    publish   analyze
      .py      .py              .py       .py
                           │
                    ┌──────▼──────┐
                    │   Memory    │ ← git-tracked markdown/jsonl
                    │  (3 layers) │
                    └─────────────┘
```

### 核心循环（心跳）

不是 cron 触发的 pipeline。是一个**持续存在的思考循环**：

```python
while alive:
    # 1. 感知：检查所有信号源
    signals = perceive()
    #   - Telegram inbox（用户消息）
    #   - 定时触发（该选题了？该查数据了？）
    #   - 文件系统变化（新素材？文章写完了？）
    #   - 外部事件（热点新闻？）

    # 2. 思考：基于当前状态 + 记忆 + 信号，决定下一步
    action = think(signals, state, memory)
    #   ReAct: 不是 if-else，是 LLM 推理
    #   "我有3篇文章在不同阶段，用户刚发了个链接，优先级是什么？"

    # 3. 行动：调用技能
    result = act(action)
    #   可能是：跑 deep_research、发 Telegram 消息、调 engine.py...

    # 4. 观察：检查结果
    observation = observe(result)
    #   成功？失败？部分完成？需要用户输入？

    # 5. 学习：压缩经验
    learn(observation)
    #   不是存"文章写好了"，是存"用A人设写B类选题→效果C，因为D"

    # 6. 等待下一个心跳
    await sleep(heartbeat_interval)
```

---

## 五个核心组件

### 1. Gateway（网关）— `daemon.py`

**职责**：持续运行，接收/发送消息，调度心跳。

- Telegram Bot long-polling（收用户消息）
- Telegram Bot 主动推送（发大纲/确认/报告给用户）
- 内部定时器（心跳、定时选题、定时数据采集）
- 信号队列（所有输入统一排队处理）

**技术**：
- `python-telegram-bot` (async)
- `asyncio` event loop
- Mac Mini systemd/launchd 保活

### 2. Brain（大脑）— `brain.py`

**职责**：推理引擎。给定状态 + 信号 + 记忆 → 决定行动。

**不是** if-else 状态机。是 LLM 推理：

```python
def think(signals, state, memory):
    prompt = f"""
    # 你的公理
    {AXIOMS}

    # 当前状态
    {state.to_markdown()}
    # 正在进行的文章、它们的阶段、等待什么

    # 最近记忆
    {memory.recent_paths(n=5)}

    # 新信号
    {signals.to_markdown()}

    # 可用技能
    {skills.list_with_descriptions()}

    决定下一步行动。输出 JSON：
    {"action": "skill_name", "params": {...}, "reason": "..."}
    """
    return claude_api.call(prompt, model="haiku")  # 快速决策用 haiku
```

**关键设计**：Brain 的每次推理都是**无状态**的——所有上下文从 state + memory 注入。这意味着即使进程重启，读回 state 文件就能继续。

### 3. Memory（记忆）— `memory.py`

**三层记忆 + agent 操作记忆**：

| 层 | 已有 | Agent 新增 | 存什么 |
|----|------|-----------|--------|
| 公理层 | `experience.jsonl` | — | 跨系列通用规则 |
| 人设层 | `人设/*.md` | — | 角色声音/禁忌 |
| 系列层 | `公众号已发/*/lessons.md` | — | 系列专属经验 |
| **操作层** | `interventions.jsonl` | `agent/paths.jsonl` | Agent 的行为路径和结果 |

**路径记忆**（女娲核心理念）：

```json
{
  "timestamp": "2026-03-10T10:30:00",
  "goal": "为 Anthropic 选题写文章",
  "path": [
    {"step": "deep_research", "duration": "15min", "result": "找到8个一手源"},
    {"step": "engine pass1-4", "duration": "45min", "result": "article.md 3200字"},
    {"step": "pass4.5 title", "result": "推荐标题：被封杀24小时后..."},
    {"step": "user_review", "wait": "3h", "result": "approved, 改了标题"},
    {"step": "publish", "result": "success"}
  ],
  "outcome": {"reads": 650, "save_rate": "7.7%"},
  "compression": "大史人设+调查类选题→收藏率高但评论低，下次试加开放问题"
}
```

### 4. Skills（技能）— `skills/`

**封装现有工具为 agent 可调用的技能**：

| 技能 | 包装 | 输入 | 输出 | 耗时 |
|------|------|------|------|------|
| `select_topic` | topic_pipeline.py | 关键词/自动 | 选题推荐报告 | ~5min |
| `research` | deep_research.py | topic_dir | 素材/deep_research.md | ~15min |
| `write` | engine.py | topic_dir + persona | article.md + 全套交付物 | ~45min |
| `publish` | one_click_publish.py | topic_dir | 微信草稿 | ~5min |
| `react` | react.py | URL + instructions | topic_dir（从链接到草稿） | ~60min |
| `analyze_gaps` | ghost_analyze.py | event description | 能力缺口提案 | ~10min |
| `notify` | Telegram API | message + buttons | 用户收到通知 | <1s |
| `ask_user` | Telegram API | question + options | 用户回答 | async |

每个技能：
- 有标准接口：`async def execute(params) -> SkillResult`
- 内部调用现有 CLI 工具（subprocess）
- 返回结构化结果 + 成功/失败状态
- 耗时长的技能支持进度回调

### 5. State（状态）— `state.py`

**文章生命周期**（不是固定 pipeline，是 agent 推进的）：

```
IDEA → RESEARCHING → OUTLINE_READY → [等用户确认]
  → WRITING → DRAFT_READY → [等用户审稿]
  → APPROVED → PUBLISHING → PUBLISHED
  → COLLECTING_METRICS → LEARNING → ARCHIVED
```

状态存储：`agent/articles.jsonl`

```json
{
  "id": "2026-03-10|Anthropic硬刚",
  "status": "DRAFT_READY",
  "persona": "大史",
  "series": "暗线",
  "topic_dir": "wechat/公众号选题/2026-03-10|Anthropic硬刚",
  "created": "2026-03-10T08:00:00",
  "updated": "2026-03-10T10:30:00",
  "awaiting": "user_review",
  "history": ["IDEA@08:00", "RESEARCHING@08:05", "WRITING@08:20", "DRAFT_READY@10:30"]
}
```

Agent 每次心跳都读这个文件，知道"现在手里有什么活，各在什么阶段"。

---

## 典型交互流

### 场景1：用户手机发链接

```
[用户] → Telegram: https://mp.weixin.qq.com/s/xxx "这个很有意思，调查下"

[Agent] Gateway 收到消息
        → Brain: 新信号=用户链接+指令
        → Think: "用户发了链接要调查，用 react skill"
        → Act: react.py --url xxx --instructions "调查下"
        → (15min后) research 完成
        → Think: "调研完了，生成大纲给用户确认"
        → Act: 生成大纲摘要
        → Notify: Telegram 推送大纲 + [确认] [修改] 按钮

[用户] → 点 [确认]

[Agent] → Think: "用户确认了，开始写作"
        → Act: engine.py --topic-dir xxx --persona 大史
        → (45min后) 写作完成
        → Notify: "文章写完了，标题：xxx，3200字。要我发布吗？"
                  + [发布] [我先看看] 按钮

[用户] → 点 [发布]

[Agent] → Act: one_click_publish.py
        → Notify: "已发布 ✓"
        → State: PUBLISHED
        → Schedule: 24h后采集数据
```

### 场景2：Agent 主动选题

```
[Agent] 定时触发（每天 23:00）
        → Act: topic_pipeline.py（扫描当天素材）
        → Think: "发现3个好选题，按公理排序"
        → Notify: Telegram 推送
          "今日选题推荐：
           1. [Anthropic新政策] — 大史/暗线 ★★★★★
           2. [Gemini更新] — 丁仪/技术祛魅 ★★★★
           3. [创业故事] — 章北海/独立篇 ★★★
           选哪个？或者都不要？"
          + [1] [2] [3] [跳过] 按钮

[用户] → 点 [1]

[Agent] → 自动进入调研→写作流程...
```

### 场景3：Agent 自我进化

```
[Agent] 定时触发（每周日）
        → Act: 分析过去一周的 paths.jsonl
        → Think: "发现模式：用大史写调查类，收藏率7.7%；
                  用章北海写叙事类，收藏率5.2%。
                  另外，3次调研超时是因为英文源太多。"
        → Notify: "周报：
          发现1：大史+调查类选题效果最好
          发现2：调研阶段英文源占比过高导致超时
          建议：调整 deep_research 的 cn/en 比例
          要我调整吗？"
          + [同意] [不改] 按钮
```

---

## 实施分阶段

### Phase 0：计划落盘

**实施第一步：把这份计划存到项目里，更新 AUTOMATION_PLAN。**

| 操作 | 文件 |
|------|------|
| 保存完整计划 | `wechat/agent/PLAN_agent_pm.md` |
| 更新 AUTOMATION_PLAN | `wechat/tools/AUTOMATION_PLAN.md` — WS-11 引用此计划文件，Phase 0/1/2/3 进度统一在 AUTOMATION_PLAN 追踪 |

所有开发进度统一集中在 AUTOMATION_PLAN 管理，PLAN_agent_pm.md 只做架构参考文档。

---

### Phase 1：骨架（能跑起来）

让 agent 能收 Telegram 消息、调用一个 skill、回复结果。

| 文件 | 内容 |
|------|------|
| `wechat/agent/daemon.py` | asyncio 主循环 + Telegram bot + 心跳 |
| `wechat/agent/brain.py` | ReAct 推理（Claude API） |
| `wechat/agent/gateway.py` | Telegram 消息路由 |
| `wechat/agent/state.py` | 文章状态机 + JSONL 持久化 |
| `wechat/agent/memory.py` | 路径记忆读写 |
| `wechat/agent/skills/__init__.py` | 技能注册表 |
| `wechat/agent/skills/notify.py` | Telegram 通知 |
| `wechat/agent/skills/react_skill.py` | 包装 react.py |
| `wechat/agent/axioms.md` | 三条公理 |
| `wechat/agent/config.yaml` | agent 配置（心跳间隔、模型选择等） |

**验证**：发一个链接到 Telegram → agent 调 react.py → 写完后推通知。

### Phase 2：完整技能 + 状态管理

包装所有现有工具为技能，实现文章全生命周期管理。

| 文件 | 内容 |
|------|------|
| `wechat/agent/skills/select_topic.py` | 包装 topic_pipeline.py |
| `wechat/agent/skills/research.py` | 包装 deep_research.py |
| `wechat/agent/skills/write.py` | 包装 engine.py |
| `wechat/agent/skills/publish.py` | 包装 one_click_publish.py |
| `wechat/agent/skills/analyze.py` | 包装 ghost_analyze.py |

**验证**：完整流程——选题推荐→用户确认→调研→写作→审批→发布。

### Phase 3：主动思考与自主进化

Agent 不只是等指令。它有**主动行为**——定期思考、分析、提议。

#### 3a. 主动行为清单（Proactive Behaviors）

| 行为 | 触发 | Agent 做什么 | 推送给用户 |
|------|------|------------|-----------|
| **晨间简报** | 每天 9:00 | 扫描过夜素材、检查在途文章状态 | "今天有1篇待审、2个热点值得关注" |
| **选题提案** | 每天 23:00 | topic_pipeline + 自己补充判断 | "推荐3个选题 + 我觉得选A因为..." |
| **数据复盘** | 文章发布 48h 后 | 采集阅读数据、与历史对比 | "这篇收藏率7.7%，比上篇高2%，可能因为..." |
| **周报** | 每周日 20:00 | 分析本周：产出/数据/模式/异常 | "本周发了2篇，总阅读1200，发现大史+调查类效果最好" |
| **商业化思考** | 每两周 | 分析竞品动向、变现可能、增长策略 | "观察到XXX号在做付费专栏，我们要不要？" |
| **能力缺口** | 每月/遇到失败时 | ghost_analyze 分析自身能力 | "我发现英文源调研经常超时，建议优化比例" |
| **公理挑战** | 每月 | review 自己的公理和经验，是否需要修正 | "上月数据显示'每周3篇'不如'每周2篇精品'，建议改策略" |

#### 3b. "主动思考"的实现

不是 hardcode 这些行为，而是给 Brain 一个**"空闲时思考"的 prompt**：

```
你是公众号的项目经理。当前没有紧急任务。

你的公理：
1. 存活：让公众号持续产出高质量内容
2. 成长：主动思考如何让这个号活下去、商业化、扩大影响力
3. 压缩：从每次产出中压缩经验

当前状态：
- 已发布 N 篇文章
- 最近数据趋势：...
- 上次主动思考时间：3天前
- 上次商业化思考：2周前

你现在有空，想想：
- 有什么你一直想说但没机会说的？
- 有什么趋势或模式你注意到了？
- 有什么建议想给 ciwang？

只输出值得推送的内容。如果没什么值得说的，输出 NULL。
```

**关键**：不是每次都推。Agent 判断"这个想法值得推"才推。否则变成垃圾通知。

#### 3c. 文件清单

| 文件 | 内容 |
|------|------|
| `wechat/agent/proactive.py` | 主动行为调度器 + 空闲思考逻辑 |
| `wechat/agent/memory.py` | 增加 compress_paths()、weekly_reflection() |
| `wechat/agent/skills/self_reflect.py` | 自我分析技能 |
| `wechat/agent/skills/market_scan.py` | 竞品扫描 + 商业化分析 |
| `wechat/agent/paths.jsonl` | 路径记忆积累 |
| `wechat/agent/reflections/` | 每次主动思考的完整记录 |

**验证**：发布3篇后，agent 自动推送1条有洞察的数据复盘。

---

## 关键技术决策

### Brain 用 `claude -p` 还是 API？

**结论：先用 `claude -p`，接口设计为可切换。**

`claude -p` 其实**有** tool use（Read/Write/Bash/WebSearch 等），只是**没有多轮会话管理**——每次调用独立。但这不是问题，因为 Brain 的每次 `think()` 本来就应该是无状态的：把 state + memory + signals 全注入 prompt，推理一步，输出 action JSON。这和 engine.py 各 Pass 的模式完全一致。

```python
# Brain.think() 的实现 — claude -p 和 API 接口一致
def think(self, context: str) -> dict:
    if self.backend == "cli":
        result = subprocess.run(
            ["claude", "-p", context, "--model", "haiku", "--output-format", "json"],
            capture_output=True
        )
        return json.loads(result.stdout)
    elif self.backend == "api":
        response = anthropic.messages.create(model="claude-haiku-4-5-20251001", ...)
        return parse_response(response)
```

**为什么先 CLI**：
- 零额外成本（复用 Claude Code 订阅）
- 已有成熟模式（engine.py 就是这么跑的）
- Brain 每次推理很短（~500 token input + ~200 output），不会吃太多订阅额度

**什么时候切 API**：
- 日调用量 >100 次时（订阅可能限速）
- 需要 structured tool use（比如让 Brain 直接调用 Python 函数）
- 需要 streaming 做实时反馈

### Token 预算控制（防失控）

Agent 7×24 运行，必须有硬性上限，防止推理循环失控烧 token。

```yaml
# wechat/agent/config.yaml
budget:
  daily_think_limit: 50        # Brain 每天最多推理 50 次
  daily_skill_limit: 10        # 每天最多调用 10 次耗费型 skill（research/write）
  single_think_max_tokens: 2000  # 单次推理输出上限
  proactive_budget: 5          # 主动思考每天最多 5 次
  cooldown_after_error: 300    # 出错后冷却 5 分钟
  heartbeat_interval: 300      # 心跳间隔 5 分钟（不是每秒）
```

**预估日消耗**（`claude -p` 订阅模式）：
- 心跳检查（快速，无需 LLM）：~288 次/天（5min 间隔）→ 0 token（纯 Python 检查）
- Brain 推理：~20-50 次/天 × ~700 tokens → ~14K-35K tokens
- Skill 调用（research/write）：~2-5 次/天 → 走现有 engine 预算
- 主动思考：~2-3 次/天 × ~1500 tokens → ~3K-5K tokens
- **日总计**：~20K-40K tokens Brain 推理，远低于一篇文章的 37K

**安全机制**：
- 达到日限额 → Agent 进入"休眠"，只转发紧急用户消息
- 连续 3 次 skill 失败 → 通知用户 + 暂停该 skill
- 每日 23:59 重置计数器

### 两台机器分工

```
Mac Mini（主力）               MacBook（辅助）
├─ daemon.py 长驻运行           ├─ 发布操作（需要 Chrome CDP）
├─ Telegram Gateway             ├─ 备用 daemon（Mini 宕机时）
├─ Brain 推理                   └─ 开发/调试
├─ 非 GUI Skills（research, write, select_topic）
└─ 状态管理 + git 同步
```

**同步方式**：
- 状态文件存在 `wechat/agent/` 目录，git tracked
- Mac Mini 做完操作 → git commit + push
- MacBook auto-pull 拉到最新状态
- 发布时：Mini daemon 通知用户 → 用户在 MacBook 触发 publish（或远程触发 Mini 的 headless Chrome）

不做 leader election——Mini 是唯一的 daemon 运行点，MacBook 只在需要 GUI 时介入。

### Telegram Bot 设置步骤

1. 打开 Telegram → 搜索 `@BotFather`
2. 发送 `/newbot`
3. 设置 bot 名称（如 `女娲内容管家`）
4. 设置 bot username（如 `nuwa_content_bot`）
5. BotFather 会返回 **API token**（形如 `123456:ABC-DEF...`）→ 保存
6. 获取你的 user ID：搜索 `@userinfobot`，发 `/start`，它会返回你的 ID
7. 把 token 和 user ID 存到 `wechat/agent/config.yaml`（.gitignore）

Agent 只响应你的 user ID，其他人发消息直接忽略。

---

## 与女娲计划的映射

| 女娲概念 | Agent PM 实现 |
|---------|--------------|
| 公理注入 | `axioms.md` → system prompt 核心 |
| 压缩→展开→再压缩 | paths.jsonl：行为路径→结果→压缩为经验 |
| 持续存在 | Mac Mini daemon 7×24 |
| 有意志 | 公理驱动的目标函数 |
| 能行动 | Skills 封装所有现有工具 |
| 记忆不存结论存路径 | paths.jsonl 记录完整推导过程 |
| 自我进化 | weekly_reflection → 能力缺口提案 |
| 人=骑手，AI=马 | Telegram 审批按钮 = 缰绳 |

---

## 验证标准

**Phase 1 完成标准**：
```
1. Mac Mini 上 daemon.py 运行 >24h 不崩
2. 用户手机发 Telegram 链接 → agent 回复大纲 → 用户确认 → 写完通知
3. 整个过程用户只按了2次手机（发链接 + 确认）
```

**Phase 1 验证步骤**：
```bash
# MacBook 上开发完毕后 push
git add wechat/agent/ && git commit && git push

# SSH 到 Mac Mini 部署
ssh apple@macmini
cd ~/Desktop/nuwa-project && git pull

# 1. Telegram bot 通了
python3 wechat/agent/daemon.py --test-telegram
# → 你手机收到 "女娲在线 ✓"

# 2. 发链接测试
# 在 Telegram 发: https://mp.weixin.qq.com/s/xxx
# → agent 回复 "收到，开始调研..."
# → 15min 后回复大纲 + [确认] 按钮

# 3. 确认写作
# 点 [确认] → "开始写作..." → 45min 后 "写完了，标题：xxx"

# 4. 进程持久化（Mac Mini）
# 用 launchd 或 nohup 保活
nohup python3 wechat/agent/daemon.py >> wechat/agent/logs/daemon.log 2>&1 &
# 后续可以用 launchd plist 做开机自启
```

**终极标准（女娲第一阶段）**：
```
1. 连续2周，agent 自主完成 ≥3篇文章（人只审批）
2. 第2周的平均质量 ≥ 第1周（路径记忆在起作用）
3. agent 提出 ≥1个有价值的自我改进提案
```

---

## 前置准备（用户需完成）

1. **Telegram Bot**：按上面步骤在 @BotFather 创建，获取 token + user ID
2. **Mac Mini 环境**：确认 `claude` CLI 可用、venv 已激活、sparse checkout 包含所有需要的目录
3. **安装依赖**：`pip install python-telegram-bot`（在 Mac Mini 的 venv 中）
