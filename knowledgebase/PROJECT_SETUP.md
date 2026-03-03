# 个人知识库项目 - 完整复原指南

> 本文档包含项目的所有关键信息，用于在新环境中完整复原整个系统

**创建日期**: 2025-01-19
**最后更新**: 2025-01-19

---

## 📋 目录

1. [项目概述](#项目概述)
2. [环境依赖](#环境依赖)
3. [目录结构](#目录结构)
4. [核心脚本](#核心脚本)
5. [配置文件](#配置文件)
6. [使用流程](#使用流程)
7. [重要说明](#重要说明)

---

## 项目概述

### 核心功能

**个人知识库管理系统** - 基于微信文章爬取、自动分类、问答交互的知识管理工具

**主要特性**：
- ✅ 自动爬取微信公众号文章（使用 Chrome CDP）
- ✅ 智能分类到 7 个主题（人工智能、商业、金融、个人成长、历史、哲学、文学）
- ✅ 问答记录（与 Claude 的交互式学习）
- ✅ 阅读笔记（个人随笔和感想）
- ⏳ 未来：Notion 集成

**相关文档**：
- `KNOWLEDGE_BASE_PLAN.md` - 完整的项目规划和设计文档
- `WEBCRAWLER_NOTES.md` - 网络爬虫技术细节
- `CLAUDE.md` - Claude Code 使用指南（会被自动加载）

---

## 环境依赖

### Python 版本
```
Python 3.9+
```

### 必需的 Python 包

**requirements.txt**:
```
playwright==1.40.0
```

**安装步骤**:
```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器
playwright install chromium
```

### 系统要求
- **操作系统**: macOS / Linux / Windows
- **Chrome 浏览器**: 用于网页爬取
- **终端**: 支持 bash 命令

---

## 目录结构

### 完整的知识库结构

```
IndividualRL/
├── knowledge_base/              # 知识库根目录
│   ├── 人工智能/
│   │   └── 文章标题/
│   │       ├── article.md      # 文章正文
│   │       ├── qa.md          # 问答记录
│   │       ├── notes.md       # 阅读笔记
│   │       ├── metadata.json  # 元数据
│   │       └── attachments/   # 附件
│   │           ├── screenshot.png
│   │           └── article.pdf
│   ├── 商业/
│   ├── 金融/
│   ├── 个人成长/
│   ├── 历史/
│   ├── 哲学/
│   ├── 文学/
│   ├── 未分类/
│   ├── _index/
│   │   ├── articles_index.json           # 全局文章索引
│   │   └── classification_rules.json     # 分类规则
│   └── README.md
│
├── add_article.py               # 添加文章脚本
├── add_note.py                  # 添加笔记脚本
├── connect_chrome.py            # Chrome CDP 爬虫
├── start_chrome_debug.sh        # Chrome 调试模式启动脚本
├── get_chrome_cookies.py        # Cookie 提取工具
├── fetch_with_cookies.py        # Cookie 爬虫（备用）
│
├── CLAUDE.md                    # Claude Code 配置
├── KNOWLEDGE_BASE_PLAN.md       # 项目规划文档
├── WEBCRAWLER_NOTES.md          # 爬虫技术文档
├── PROJECT_SETUP.md             # 本文件（复原指南）
│
├── requirements.txt             # Python 依赖
└── .venv/                       # 虚拟环境（不需要复制）
```

### 最小复原所需文件

**必需文件**（带走这些即可复原）:
```
✅ knowledge_base/              # 整个知识库目录
✅ add_article.py
✅ add_note.py
✅ connect_chrome.py
✅ start_chrome_debug.sh
✅ CLAUDE.md
✅ KNOWLEDGE_BASE_PLAN.md
✅ WEBCRAWLER_NOTES.md
✅ PROJECT_SETUP.md            # 本文件
✅ requirements.txt
```

**可选文件**:
```
⚪ get_chrome_cookies.py       # 备用爬虫
⚪ fetch_with_cookies.py       # 备用爬虫
```

**不需要的文件**:
```
❌ .venv/                      # 虚拟环境（重新创建即可）
❌ weixin_article.*            # 临时文件
❌ __pycache__/                # Python 缓存
```

---

## 核心脚本

### 1. start_chrome_debug.sh

**功能**: 启动 Chrome 调试模式

**完整代码**:
```bash
#!/bin/bash

# 启动 Chrome 浏览器并开启远程调试端口

echo "正在关闭所有 Chrome 进程..."
killall "Google Chrome" 2>/dev/null || true
sleep 2

echo "启动 Chrome（远程调试模式）..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
  > /dev/null 2>&1 &

echo "Chrome 已启动，远程调试端口: 9222"
echo "现在可以在 Chrome 中打开文章，然后运行: python connect_chrome.py"
```

**权限设置**:
```bash
chmod +x start_chrome_debug.sh
```

---

### 2. add_article.py

**功能**: 自动添加文章到知识库

**核心功能**:
1. 连接到 Chrome CDP（端口 9222）
2. 爬取文章（标题、作者、正文）
3. 自动分类（基于关键词匹配）
4. 生成截图和 PDF
5. 创建文章目录并保存所有文件
6. 更新全局索引

**使用方法**:
```bash
python add_article.py "https://mp.weixin.qq.com/s/xxxxx"
```

**文件长度**: ~515 行

**关键依赖**:
- `asyncio` - 异步操作
- `playwright` - 浏览器自动化
- `json` - 数据处理
- `pathlib` - 路径操作

---

### 3. add_note.py

**功能**: 快速添加阅读笔记

**使用方法**:
```bash
# 方式 1: 添加到最新文章
python add_note.py "我的笔记内容"

# 方式 2: 添加到指定文章
python add_note.py -a "关键词" "我的笔记内容"

# 方式 3: 交互式输入
python add_note.py
```

**文件长度**: ~165 行

---

### 4. connect_chrome.py

**功能**: 基础的 Chrome CDP 爬虫

**核心特性**:
- 连接到已打开的 Chrome（端口 9222）
- 自动检测验证页面（等待 60 秒）
- 提取文章内容并清理
- 生成截图和 PDF

**使用方法**:
```bash
# 1. 启动 Chrome 调试模式
./start_chrome_debug.sh

# 2. 在 Chrome 中打开文章

# 3. 运行脚本
python connect_chrome.py
```

**文件长度**: ~265 行

---

## 配置文件

### 1. classification_rules.json

**位置**: `knowledge_base/_index/classification_rules.json`

**作用**: 定义自动分类的关键词规则

**结构**:
```json
{
  "categories": {
    "人工智能": {
      "keywords": ["AI", "机器学习", "深度学习", ...],
      "weight": 1.0,
      "description": "人工智能、机器学习、深度学习相关技术"
    },
    "商业": { ... },
    "金融": { ... },
    ...
  },
  "rules": {
    "min_score_threshold": 2
  }
}
```

**分类逻辑**:
- 统计文章标题 + 正文前 500 字中关键词出现次数
- 得分最高的分类为主分类
- 得分低于阈值（2）归入"未分类"

---

### 2. articles_index.json

**位置**: `knowledge_base/_index/articles_index.json`

**作用**: 全局文章索引

**结构**:
```json
{
  "version": "1.0",
  "last_updated": "2025-01-19",
  "total_articles": 1,
  "articles": [
    {
      "id": "article_20250119_001",
      "title": "文章标题",
      "category": "人工智能",
      "author": "作者",
      "crawl_date": "2025-01-19",
      "word_count": 9259,
      "read_status": "unread",
      "path": "人工智能/文章标题",
      "tags": ["标签1", "标签2"]
    }
  ],
  "statistics": {
    "人工智能": 1,
    "商业": 0,
    ...
  }
}
```

---

### 3. CLAUDE.md

**位置**: 项目根目录

**作用**: Claude Code 的项目说明（自动加载）

**关键内容**:
```markdown
## 🎯 PRIMARY TASK: Personal Knowledge Base System
- Article Collection: 爬取微信文章
- Auto Classification: 7 个主题分类
- Interactive Q&A: 基于文章内容问答
- Notion Integration: 未来同步到 Notion

## User Preferences
**Model Selection Reminder**:
- 如果任务超出能力，提醒用户使用 Opus 模型
```

---

## 使用流程

### 完整工作流程

#### 1️⃣ **初始化项目**

```bash
# 在新环境中
cd /path/to/new/location

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 设置脚本权限
chmod +x start_chrome_debug.sh
chmod +x add_article.py
chmod +x add_note.py
```

#### 2️⃣ **添加新文章**

```bash
# Step 1: 启动 Chrome 调试模式
./start_chrome_debug.sh

# Step 2: 在 Chrome 中打开文章链接

# Step 3: 运行添加脚本
python add_article.py "https://mp.weixin.qq.com/s/xxxxx"

# 脚本会：
# - 自动爬取文章
# - 智能分类（可手动修改）
# - 保存到 knowledge_base/
# - 更新索引
```

#### 3️⃣ **添加阅读笔记**

```bash
# 快速添加到最新文章
python add_note.py "我的想法和感悟"

# 添加到指定文章
python add_note.py -a "OpenAI" "关于这篇文章的思考"
```

#### 4️⃣ **问答交互**

与 Claude Code 对话时：
- 直接问问题，Claude 会回答
- Claude 会自动把问答记录到对应文章的 `qa.md`

示例：
```
你: "请解释 MCTS"
Claude: [详细解释] + 记录到 qa.md
```

---

## 重要说明

### Chrome 调试模式

**端口**: 9222（固定）

**启动方式**:
```bash
./start_chrome_debug.sh
```

**注意事项**:
- 脚本会关闭现有的 Chrome 进程
- 使用你的正常 Chrome 配置（已登录状态）
- 不会影响你的书签、历史等数据

**验证启动成功**:
```bash
# 检查端口
lsof -i :9222

# 检查 CDP 接口
curl -s http://localhost:9222/json/version
```

---

### 文章 ID 生成规则

**格式**: `article_YYYYMMDD_序号`

**示例**:
- `article_20250119_001` - 2025年1月19日的第1篇
- `article_20250119_002` - 2025年1月19日的第2篇

**自动递增**: 脚本会自动查找当天已有文章数量并递增

---

### 文件命名规则

**文章目录名**:
- 使用文章标题
- 特殊字符替换为下划线
- 长度限制 100 字符

**示例**:
```
原标题: 万字长文推演OpenAI o1 self-play RL 技术路线
目录名: 万字长文推演OpenAI_o1_self-play_RL_技术路线
```

---

### 分类修改

**自动分类后可以手动修改**:

运行 `add_article.py` 时会提示：
```
是否修改分类？(直接回车使用'人工智能')
输入新分类 (人工智能/商业/金融/个人成长/历史/哲学/文学):
```

输入新分类即可修改。

---

### 知识库备份

**建议定期备份**:
```bash
# 备份整个知识库
cp -r knowledge_base knowledge_base_backup_$(date +%Y%m%d)

# 或使用 Git
git init
git add .
git commit -m "Backup knowledge base"
```

---

### Git 版本控制（推荐）

```bash
# 初始化 Git
git init

# 创建 .gitignore
cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.pyc
.DS_Store
weixin_article.*
EOF

# 提交
git add .
git commit -m "Initial commit: Knowledge base system"

# 以后每次修改
git add .
git commit -m "Add new article: 文章标题"
```

---

### 迁移到新环境

**带走的文件**（最小化）:
```
✅ knowledge_base/          # 整个目录
✅ *.py                     # 所有 Python 脚本
✅ *.sh                     # Shell 脚本
✅ *.md                     # 所有 Markdown 文档
✅ requirements.txt
```

**新环境重建**:
```bash
# 1. 复制文件到新位置
cp -r /path/to/old/project /path/to/new/project

# 2. 重新创建虚拟环境
cd /path/to/new/project
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 4. 设置权限
chmod +x *.sh *.py

# 5. 测试
./start_chrome_debug.sh
```

---

## 常见问题

### Q1: Chrome 连接失败

**错误**: `Error: connect ECONNREFUSED 127.0.0.1:9222`

**解决**:
```bash
# 检查 Chrome 是否在调试模式运行
lsof -i :9222

# 如果没有，重新启动
./start_chrome_debug.sh
```

---

### Q2: 文章爬取失败

**错误**: 遇到验证页面

**解决**:
- 脚本会自动等待 60 秒
- 在 Chrome 中手动完成验证
- 脚本会自动继续

---

### Q3: 分类不准确

**解决**:
1. 运行 `add_article.py` 时手动修改分类
2. 或编辑 `classification_rules.json` 添加更多关键词

---

### Q4: 笔记/问答文件找不到

**检查**:
```bash
# 查看文章目录结构
ls -la "knowledge_base/人工智能/文章名/"

# 应该有：
# - article.md
# - qa.md
# - notes.md
# - metadata.json
# - attachments/
```

---

## 技术细节

### Chrome DevTools Protocol (CDP)

**端口**: 9222
**协议**: HTTP WebSocket

**连接代码**:
```python
browser = await p.chromium.connect_over_cdp("http://localhost:9222")
```

**优势**:
- 使用已登录的浏览器
- 绕过反爬虫机制
- 保留 cookies 和 session

---

### 文章内容清理

**清理规则**（在 `connect_chrome.py` 和 `add_article.py` 中）:

```javascript
// 去掉附录部分
const appendixMarkers = ['STRAWBERRY 长考', 'STRAWBERRY长考'];

// 去掉页尾信息
const footerMarkers = ['进技术交流群请添加', '关于AINLP'];
```

**可根据需要修改这些标记**。

---

### 文章元数据结构

**metadata.json 字段说明**:

```json
{
  "id": "文章唯一ID",
  "title": "文章标题",
  "author": "作者",
  "source": "来源（微信公众号）",
  "source_url": "原文链接",
  "crawl_date": "爬取日期",
  "category": "分类",
  "tags": ["标签数组"],
  "read_status": "阅读状态（unread/reading/read）",
  "word_count": "字数",
  "has_qa": "是否有问答",
  "qa_count": "问答数量",
  "attachments": {
    "screenshot": "截图路径",
    "pdf": "PDF路径"
  },
  "notes": "备注"
}
```

---

## 未来扩展

### Notion 集成（计划中）

**需要**:
1. Notion Integration Token
2. Database ID
3. `notion-client` Python 库

**参考**: `KNOWLEDGE_BASE_PLAN.md` 的阶段 2

---

### 其他可能的功能

- [ ] 全文搜索
- [ ] 阅读进度追踪
- [ ] 标签系统
- [ ] Markdown 导出
- [ ] 批量爬取文章列表
- [ ] 图片本地化存储
- [ ] 数据库存储（SQLite）

---

## 联系方式

如果有问题，参考以下文档：
- `KNOWLEDGE_BASE_PLAN.md` - 完整的项目规划
- `WEBCRAWLER_NOTES.md` - 爬虫技术细节
- `CLAUDE.md` - Claude Code 配置

---

## 版本历史

- **v1.0** (2025-01-19) - 初始版本，包含基础功能
  - 文章爬取
  - 自动分类
  - 问答记录
  - 阅读笔记

---

**最后更新**: 2025-01-19
**文档版本**: 1.0
