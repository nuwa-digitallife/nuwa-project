---
name: sparse-clone
description: 在其他电脑上轻量 clone 本 repo 的指定子目录（sparse checkout），避免下载整个 1.3G 仓库。
user-invocable: true
allowed-tools: Bash, AskUserQuestion
---

# /sparse-clone — 轻量 clone 指定目录

## 触发场景

用户说"我想在另一台电脑上只拉公众号的内容"、"sparse clone"、"轻量 clone"等。

## 预置模板

根据用户需求选择或组合以下模板：

### 公众号（~30M）
```
wechat/ logs/ docs/ write_engine/ CLAUDE.md
```

### 女娲核心（~5M）
```
docs/ logs/ CLAUDE.md
```

### 知识库（~6M）
```
knowledgebase/ logs/ CLAUDE.md
```

### 全部轻量（不含 exporter/videocut/TradingAgents，~35M）
```
wechat/ docs/ logs/ knowledgebase/ scripts/ write_engine/ qqinvest/ twitter/ CLAUDE.md
```

## 执行流程

1. **问用户要什么**：用 AskUserQuestion 展示上面的模板，让用户选。如果用户在 `/sparse-clone` 后面直接指定了目录或模板名，跳过此步。

2. **判断当前环境**：
   - 如果**已在 nuwa-project repo 内**：说明用户想在当前机器添加目录，用 `git sparse-checkout add`
   - 如果**不在 repo 内**：生成完整的 clone 命令

3. **生成命令**：

   **新 clone（在其他电脑上执行）：**
   ```bash
   git clone --filter=blob:none --sparse git@github.com:nuwa-digitallife/nuwa-project.git
   cd nuwa-project
   git sparse-checkout set <目录列表>
   ```

   **已有 sparse checkout，添加目录：**
   ```bash
   git sparse-checkout add <新目录>
   ```

   **查看当前 sparse 状态：**
   ```bash
   git sparse-checkout list
   ```

4. **执行或输出**：
   - 如果在当前 repo 内需要调整 sparse-checkout：直接执行
   - 如果是为其他电脑生成命令：输出命令让用户复制，格式为一行可粘贴的命令

## 一行命令格式

为方便用户在其他电脑粘贴，输出如下格式：

```bash
git clone --filter=blob:none --sparse git@github.com:nuwa-digitallife/nuwa-project.git && cd nuwa-project && git sparse-checkout set wechat/ logs/ docs/ write_engine/ CLAUDE.md
```

## 注意事项

- `--filter=blob:none` 确保只下载需要的文件内容（按需获取）
- sparse-checkout 后 `git pull` 只更新已选目录
- 完整 repo 约 1.3G，其中 `wechat-article-exporter/` 911M、`videocut/` 133M、`.git/` 179M 是大头
- CLAUDE.md 始终包含（项目指令）
