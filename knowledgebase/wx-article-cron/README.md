# wx-article-cron — AI 日报简报

每天自动从关注的公众号拉取文章，筛选 AI 相关，**合并同类项**，生成简报供人工精选。

## 工作流

```
Chrome Cookie → auth-key → exporter API → 拉取12个公众号
                                              ↓
                              AI 过滤 → 去已入库 → 合并同题报道
                                              ↓
                                   digests/YYYY-MM-DD.md
                                              ↓
                                   你挑好的 → 丢链接给 Claude → 入库
```

## 使用

```bash
source ~/venv/automation/bin/activate

# 生成今日简报（最近 24h）
python auto_import.py

# 扫描最近 48h
python auto_import.py --hours 48
```

简报输出到 `knowledgebase/digests/YYYY-MM-DD.md`。

## 关注的公众号

机器之心、量子位、新智元、晚点LatePost、甲子光年、硅星人、36氪、极客公园、PaperWeekly、夕小瑶科技说、牛顿顿顿、虎嗅APP

编辑 `auto_import.py` 中的 `FOLLOWED_ACCOUNTS` 列表可增减。

## 入库

看完简报后，把想入库的文章链接发给 Claude：
```
帮忙加下 https://mp.weixin.qq.com/s/xxxxx
```

## 定时执行（launchd）

已配置每天 10:00 自动生成：

```bash
# 查看状态
launchctl list | grep nuwa

# 手动触发
launchctl start com.nuwa.kb-auto-import

# 重新加载
launchctl unload ~/Library/LaunchAgents/com.nuwa.kb-auto-import.plist
launchctl load ~/Library/LaunchAgents/com.nuwa.kb-auto-import.plist
```

## 技术方案

1. **认证**：从 Chrome Cookies SQLite DB 解密 `auth-key`（macOS Keychain + PBKDF2 + AES-CBC）
2. **拉取**：通过 exporter API 搜索公众号 → 分页拉取文章列表
3. **过滤**：标题/摘要关键词匹配（AI 高频词 + classification_rules.json）
4. **去重**：对比 articles_index.json 已入库文章的标题和 URL
5. **合并**：SequenceMatcher + Jaccard 相似度，阈值 0.45

## 前置条件

- exporter 服务运行中 (`localhost:3000`)
- Chrome 中已登录过 exporter（需要有效的 `auth-key` cookie）
- Python: `~/venv/automation/`（需 requests、cryptography）
