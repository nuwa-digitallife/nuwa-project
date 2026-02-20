# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IndividualRL - A Python-based project with two core focuses:

### 🎯 PRIMARY TASK: Personal Knowledge Base System
**This is the CORE mission** - Building an automated personal knowledge management system:
- **Article Collection**: Crawl WeChat articles and other content
- **Auto Classification**: 7 categories (人工智能, 商业, 金融, 个人成长, 历史, 哲学, 文学)
- **Interactive Q&A**: Answer user questions based on article content, record conversations
- **Notion Integration**: Future sync to user's Notion database

📋 **See KNOWLEDGE_BASE_PLAN.md for complete roadmap and implementation details**

### Secondary: Reinforcement Learning
Future RL experiments and implementations

## 微信文章抓取

当用户发来微信文章链接（`mp.weixin.qq.com`）时，使用 `fetch_article.py` 抓取：

```bash
source ~/venv/automation/bin/activate

# 抓取文章保存为 Markdown（指定输出目录）
python knowledgebase/wx-article-cron/fetch_article.py <url> -o <输出目录>

# 抓取多篇
python knowledgebase/wx-article-cron/fetch_article.py <url1> <url2> <url3> -o <输出目录>

# 入库到知识库（自动分类到 knowledge_base/{分类}/{公众号}/{标题}/）
python knowledgebase/wx-article-cron/fetch_article.py <url> --kb
```

**前置条件**: exporter 服务需运行在 localhost:3000（通常已在后台跑）。

**常见场景**:
- 用户说「帮忙加下 <url>」→ 用 `--kb` 入库
- 用户说「抓下这篇」→ 存到指定目录或当前目录
- 用户给多个链接 → 批量抓取

## User Preferences

**Model Selection Reminder**:
- Current model: Claude Sonnet 4.5 (suitable for most development tasks)
- **IMPORTANT**: If you encounter tasks that are beyond your capability or require exceptional reasoning/complexity, proactively remind the user: "This task might benefit from using Opus for better results"
- Examples: Complex architecture design, innovative solutions to novel problems, large-scale refactoring, advanced algorithm optimization

## Development Environment

### Python Environment
- Virtual environment located in `.venv/`
- Python version: 3.9 (based on .venv structure)

### Activating the Environment
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

## Project Structure

### Web Crawler (Current)
- `connect_chrome.py` - Main crawler using Chrome CDP
- `start_chrome_debug.sh` - Chrome debug mode launcher
- `get_chrome_cookies.py` - Cookie extraction utility
- `fetch_with_cookies.py` - Cookie-based crawler (backup)
- `WEBCRAWLER_NOTES.md` - Comprehensive crawler documentation

### RL Components (Future)
- Training scripts
- Environment definitions
- Agent/model implementations
- Configuration files

## Common Commands

### Web Crawler
```bash
# 1. Start Chrome in debug mode
./start_chrome_debug.sh

# 2. Open article in Chrome, then run crawler
source .venv/bin/activate
python connect_chrome.py
```

### Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

## Important Notes

### Knowledge Base System
- **Read KNOWLEDGE_BASE_PLAN.md first** - Contains complete system design and roadmap
- Current phase: Building local knowledge base (Phase 1)
- Future phase: Notion integration (Phase 2)
- User expects: Article crawling → Auto classification → Q&A recording → Notion sync

### Web Crawler
- See `WEBCRAWLER_NOTES.md` for detailed web crawling workflow and troubleshooting
- Chrome must run on port 9222 for CDP connection
- Crawler automatically detects verification pages (60s timeout)
