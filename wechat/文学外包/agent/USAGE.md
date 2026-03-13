# 文学编辑 Agent 使用手册

## 快速开始

Telegram 搜索 **@nvwa_literature_bot**，发 `/start`，看到"文学编辑在线 ✓"即可开始。

## 启动 / 停止

```bash
# 启动
./wechat/文学外包/agent/run.sh

# 停止
kill $(cat wechat/文学外包/agent/daemon.pid) && rm wechat/文学外包/agent/daemon.pid

# 查看日志
tail -f wechat/文学外包/agent/logs/daemon.log
```

## 核心流程

一篇稿件从开始到结束会经过以下阶段，每个关键节点 Agent 会发 Telegram 按钮让你决策：

```
发现机会 → 提出选题 → [你确认] → 采集素材 → 金线压缩 → [你确认金线]
→ 展开写作 → [你审阅终稿] → 生成邮件 → [你发送] → 跟踪结果 → 压缩经验
```

### 你需要参与的 5 个节点

| 阶段 | Agent 做什么 | 你做什么 |
|------|-------------|---------|
| 选题确认 | 发送选题方案 + 目标刊物 | 点 [确认] / [换个角度] |
| 金线确认 | 发送意象 + 洞察 + 结构 | 点 [确认金线] / 发修改意见 |
| 终稿审阅 | 发送完成稿件摘要 + 方法论合规报告 | 点 [通过] / [需要修改] |
| 邮件发送 | 生成投稿邮件草稿到 Gmail | 去 Gmail 检查后发送，回来说"已发" |
| 结果反馈 | 等你告知结果 | 说"采用"或"拒稿"，Agent 自动分析压缩经验 |

## Telegram 对话指令

不需要特殊命令格式，直接说人话。

### 开始写作（推荐入口）

选题不是你定的，是期刊定的。直接让 Agent 扫描机会数据库，它会推荐匹配的，你选一个就行：

```
扫描
有什么可以投
下一篇
找机会
投什么
```

Agent 会扫描机会数据库 → 返回匹配列表 → 每个机会一个按钮 → 你点选 → 自动进入流程。

### 查询类

```
进度
状态
投稿状态
```

### 纠正类（造人过程）

以"纠正:"或"修改:"开头，Agent 会记录到 corrections.jsonl，后续写作自动学习：

```
纠正: 第三段太AI味了，"岁月的长河"是陈词滥调
修改: 不要用抒情概括开头，直接进场景
纠正: 金线断了，中段跟主题没关系
```

### 结果反馈

```
采用了
拒稿了
录用
退稿
```

## 预算限制

| 项目 | 每日上限 | 说明 |
|------|---------|------|
| Brain 推理 | 30 次 | 每条消息消耗 1 次推理 |
| 技能调用 | 8 次 | 写作/压缩/分析等重操作 |
| 心跳间隔 | 2 分钟 | 无消息时的轮询频率 |

达到上限后 Agent 会通知你，次日自动重置。

## 技能清单

| 技能 | 耗时 | 做什么 |
|------|------|--------|
| `scan_opportunities` | ~10min | 扫描投稿机会数据库，匹配合适征文 |
| `gather_materials` | ~15min | 搜索采集写作素材 |
| `compress_goldline` | ~5min | 金线压缩（意象 + 洞察 + 结构） |
| `write_manuscript` | ~30min | 4-Pass 展开写作，产出终稿 MD + DOCX |
| `check_methodology` | ~3min | 方法论合规检查（金线/6C/陈言/AI败相） |
| `draft_submission` | ~1min | 生成投稿邮件草稿 |
| `track_submissions` | <1s | 汇总投稿状态 |
| `analyze_result` | ~5min | 分析采用/拒稿结果，压缩经验 |

## 纠正系统（造人）

Agent 的进化路径：

- **学徒期**（前 5 篇）：严格 follow 方法论，你频繁纠正，它记录学习
- **助手期**（5-15 篇）：开始提出自己的判断，纠正频率降低
- **编辑期**（15-30 篇）：主动自检自修，偶尔纠正
- **自主期**（30+ 篇）：你只做金线确认 + 发送

每条纠正存入 `corrections.jsonl`，Brain 每次推理都会读取最近 10 条纠正作为短期记忆。

## 文件结构

```
wechat/文学外包/agent/
├── run.sh              # 启动脚本
├── daemon.py           # 主程序
├── config.yaml         # 配置（bot token, 预算, 路径）
├── axioms.md           # Agent 的 DNA（3 条公理）
├── methodology.md      # → 文学方法论.md（symlink）
├── manuscripts.jsonl   # 稿件状态持久化
├── paths.jsonl         # 行为路径记忆
├── corrections.jsonl   # 用户纠正记录
├── logs/
│   └── daemon.log      # 运行日志
└── skills/             # 8 个技能模块
```

## 故障排查

**Agent 无响应**：检查进程是否存活
```bash
cat wechat/文学外包/agent/daemon.pid && ps -p $(cat wechat/文学外包/agent/daemon.pid)
```

**Brain 推理报错**：通常是 `claude -p` 调用问题，查日志
```bash
grep "error\|ERROR\|failed" wechat/文学外包/agent/logs/daemon.log | tail -5
```

**重启**：
```bash
kill $(cat wechat/文学外包/agent/daemon.pid) 2>/dev/null; rm -f wechat/文学外包/agent/daemon.pid
./wechat/文学外包/agent/run.sh
```
