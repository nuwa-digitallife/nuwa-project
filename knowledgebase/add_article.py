#!/usr/bin/env python3
"""
自动添加文章到知识库
使用方式：python add_article.py "文章URL"
"""
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


# 配置
KNOWLEDGE_BASE_DIR = Path("knowledge_base")
INDEX_DIR = KNOWLEDGE_BASE_DIR / "_index"
CLASSIFICATION_RULES_FILE = INDEX_DIR / "classification_rules.json"
ARTICLES_INDEX_FILE = INDEX_DIR / "articles_index.json"


def load_classification_rules():
    """加载分类规则"""
    with open(CLASSIFICATION_RULES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_articles_index():
    """加载文章索引"""
    with open(ARTICLES_INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_articles_index(index_data):
    """保存文章索引"""
    with open(ARTICLES_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def classify_article(title, content):
    """
    自动分类文章
    返回：(主分类, 标签列表, 得分字典)
    """
    rules = load_classification_rules()
    categories = rules['categories']

    # 合并标题和内容前500字进行分析
    text_to_analyze = title + " " + content[:500]
    text_lower = text_to_analyze.lower()

    # 计算每个分类的得分
    scores = {}
    matched_keywords = {}

    for category, info in categories.items():
        score = 0
        keywords_found = []

        for keyword in info['keywords']:
            # 统计关键词出现次数
            count = text_to_analyze.count(keyword)
            if count > 0:
                score += count
                keywords_found.append(keyword)

        scores[category] = score
        matched_keywords[category] = keywords_found

    # 找出得分最高的分类
    max_score = max(scores.values())

    # 如果得分低于阈值，归入"未分类"
    min_threshold = rules['rules']['min_score_threshold']
    if max_score < min_threshold:
        return "未分类", [], scores

    # 选择得分最高的分类
    best_category = max(scores, key=scores.get)

    # 提取标签（得分前3的关键词）
    tags = matched_keywords[best_category][:5] if matched_keywords[best_category] else []

    return best_category, tags, scores


def sanitize_filename(name):
    """清理文件名，移除特殊字符"""
    # 替换特殊字符为下划线
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 移除多余的空格
    name = re.sub(r'\s+', '_', name)
    # 限制长度
    if len(name) > 100:
        name = name[:100]
    return name


def generate_article_id():
    """生成文章ID"""
    today = datetime.now().strftime("%Y%m%d")

    # 读取现有索引，找到今天已有的文章数量
    index = load_articles_index()
    today_articles = [a for a in index['articles'] if a['id'].startswith(f"article_{today}")]

    # 生成新ID
    seq = len(today_articles) + 1
    return f"article_{today}_{seq:03d}"


async def crawl_article(url):
    """
    爬取文章内容
    返回：{title, author, content, url}
    """
    print(f"正在爬取文章: {url}")

    async with async_playwright() as p:
        try:
            # 连接到现有的 Chrome 实例
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✓ 已连接到 Chrome")

            # 获取所有页面
            contexts = browser.contexts
            pages = []
            if contexts:
                for context in contexts:
                    pages.extend(context.pages)

            # 查找微信文章标签页
            weixin_page = None
            for page in pages:
                if url in page.url or "mp.weixin.qq.com" in page.url:
                    weixin_page = page
                    break

            if not weixin_page:
                print(f"⚠️  未找到文章页面，请在 Chrome 中打开: {url}")
                return None

            print(f"✓ 找到文章页面")

            # 等待页面加载
            await weixin_page.wait_for_load_state("domcontentloaded")

            # 检查是否需要验证
            page_text = await weixin_page.evaluate('document.body.innerText')

            if '环境异常' in page_text or '验证' in page_text:
                print("⚠️  检测到验证页面，等待60秒...")

                for i in range(12):
                    await weixin_page.wait_for_timeout(5000)
                    current_text = await weixin_page.evaluate('document.body.innerText')
                    if '环境异常' not in current_text and '验证' not in current_text and len(current_text) > 200:
                        print("✓ 验证完成")
                        break
                    print(f"等待中... ({(i+1)*5}/60秒)")

            # 提取文章内容
            article_data = await weixin_page.evaluate('''() => {
                // 获取标题
                let title = '';
                const titleSelectors = [
                    '#activity-name',
                    'h1',
                    '.rich_media_title',
                    '[id*="title"]'
                ];

                for (let selector of titleSelectors) {
                    const element = document.querySelector(selector);
                    if (element && element.innerText.trim()) {
                        title = element.innerText.trim();
                        break;
                    }
                }

                if (!title) {
                    title = document.title;
                }

                // 获取文章内容
                let content = '';
                let selector_used = '';

                const contentSelectors = [
                    '#js_content',
                    '.rich_media_content',
                    '#img-content',
                    'div[id*="content"]',
                    'article'
                ];

                for (let selector of contentSelectors) {
                    const element = document.querySelector(selector);
                    if (element && element.innerText.length > 100) {
                        content = element.innerText;
                        selector_used = selector;
                        break;
                    }
                }

                if (!content) {
                    content = document.body.innerText;
                    selector_used = 'body';
                }

                // 清理内容
                let cleanContent = content;

                // 去掉附录部分
                const appendixMarkers = ['STRAWBERRY 长考', 'STRAWBERRY长考'];
                for (let marker of appendixMarkers) {
                    const idx = cleanContent.indexOf(marker);
                    if (idx > 0) {
                        cleanContent = cleanContent.substring(0, idx).trim();
                        break;
                    }
                }

                // 去掉页尾信息
                const footerMarkers = ['进技术交流群请添加', '关于AINLP'];
                for (let marker of footerMarkers) {
                    const idx = cleanContent.indexOf(marker);
                    if (idx > 0) {
                        cleanContent = cleanContent.substring(0, idx).trim();
                        break;
                    }
                }

                // 获取作者信息
                let author = '';
                try {
                    const authorElem = document.querySelector('#js_name, .profile_nickname');
                    if (authorElem) {
                        author = authorElem.innerText.trim();
                    }
                } catch (e) {}

                return {
                    title: title,
                    author: author,
                    content: cleanContent,
                    originalLength: content.length,
                    cleanedLength: cleanContent.length,
                    selector: selector_used,
                    url: window.location.href
                };
            }''')

            print(f"✓ 标题: {article_data['title']}")
            if article_data['author']:
                print(f"✓ 作者: {article_data['author']}")
            print(f"✓ 内容长度: {article_data['cleanedLength']} 字符")

            # 生成截图和PDF
            await weixin_page.evaluate('window.scrollTo(0, 0)')
            await weixin_page.wait_for_timeout(2000)

            # 临时保存截图和PDF
            screenshot_path = "/tmp/temp_screenshot.png"
            pdf_path = "/tmp/temp_article.pdf"

            await weixin_page.screenshot(path=screenshot_path, full_page=False)
            await weixin_page.pdf(
                path=pdf_path,
                format='A4',
                print_background=True,
                margin={'top': '1cm', 'bottom': '1cm', 'left': '1cm', 'right': '1cm'}
            )

            article_data['screenshot_path'] = screenshot_path
            article_data['pdf_path'] = pdf_path

            return article_data

        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            return None


def create_article_directory(article_data, category, tags):
    """
    创建文章目录并保存文件
    返回：文章目录路径
    """
    # 生成文章ID和目录名
    article_id = generate_article_id()
    dir_name = sanitize_filename(article_data['title'])

    # 创建文章目录（新结构: 分类/公众号/文章标题）
    author = article_data.get('author', '').strip() or '未知公众号'
    author_dir_name = sanitize_filename(author)
    article_dir = KNOWLEDGE_BASE_DIR / category / author_dir_name / dir_name
    attachments_dir = article_dir / "attachments"

    article_dir.mkdir(parents=True, exist_ok=True)
    attachments_dir.mkdir(exist_ok=True)

    print(f"\n正在保存到: {article_dir}")

    # 1. 保存 article.md
    today = datetime.now().strftime("%Y-%m-%d")
    article_md = article_dir / "article.md"

    with open(article_md, 'w', encoding='utf-8') as f:
        f.write(f"""---
id: {article_id}
title: {article_data['title']}
author: {article_data.get('author', '')}
source: 微信公众号
source_url: {article_data['url']}
crawl_date: {today}
category: {category}
tags: {tags}
read_status: unread
word_count: {len(article_data['content'])}
---

# {article_data['title']}

{article_data['content']}
""")

    print(f"✓ article.md 已保存")

    # 2. 保存 qa.md
    qa_md = article_dir / "qa.md"
    with open(qa_md, 'w', encoding='utf-8') as f:
        f.write(f"""# 问答记录

> 关联文章：{article_data['title']}
>
> 文章路径：[article.md](./article.md)

---

<!-- 问答记录将在这里添加 -->
<!-- 格式示例：

## {datetime.now().strftime("%Y-%m-%d %H:%M")}

**Q**: 你的问题

**A**: Claude 的回答

**💡 我的笔记**：
- 你的想法和笔记

---

-->
""")

    print(f"✓ qa.md 已保存")

    # 2.5 创建 notes.md
    notes_md = article_dir / "notes.md"
    with open(notes_md, 'w', encoding='utf-8') as f:
        f.write(f"""# 阅读笔记

> 文章：{article_data['title']}

---

<!-- 在下方添加你的阅读随笔和感想 -->
<!-- 使用 add_note.py 脚本可以快速添加笔记 -->
""")

    print(f"✓ notes.md 已保存")

    # 3. 保存 metadata.json
    metadata_json = article_dir / "metadata.json"
    metadata = {
        "id": article_id,
        "title": article_data['title'],
        "author": article_data.get('author', ''),
        "source": "微信公众号",
        "source_url": article_data['url'],
        "crawl_date": today,
        "category": category,
        "tags": tags,
        "read_status": "unread",
        "word_count": len(article_data['content']),
        "has_qa": False,
        "qa_count": 0,
        "attachments": {
            "screenshot": "attachments/screenshot.png",
            "pdf": "attachments/article.pdf"
        },
        "notes": ""
    }

    with open(metadata_json, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✓ metadata.json 已保存")

    # 4. 保存附件
    if 'screenshot_path' in article_data:
        import shutil
        shutil.copy(article_data['screenshot_path'], attachments_dir / "screenshot.png")
        print(f"✓ screenshot.png 已保存")

    if 'pdf_path' in article_data:
        import shutil
        shutil.copy(article_data['pdf_path'], attachments_dir / "article.pdf")
        print(f"✓ article.pdf 已保存")

    return {
        "id": article_id,
        "title": article_data['title'],
        "category": category,
        "author": article_data.get('author', ''),
        "crawl_date": today,
        "word_count": len(article_data['content']),
        "read_status": "unread",
        "path": f"{category}/{author_dir_name}/{dir_name}",
        "tags": tags
    }


def update_index(article_info):
    """更新全局索引"""
    index = load_articles_index()

    # 添加文章
    index['articles'].append(article_info)
    index['total_articles'] = len(index['articles'])

    # 更新统计
    category = article_info['category']
    if category in index['statistics']:
        index['statistics'][category] += 1

    # 更新时间
    index['last_updated'] = datetime.now().strftime("%Y-%m-%d")

    save_articles_index(index)
    print(f"\n✓ 已更新索引文件")


async def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("使用方式: python add_article.py <文章URL>")
        print("示例: python add_article.py https://mp.weixin.qq.com/s/xxxxx")
        return

    url = sys.argv[1]

    print("=" * 60)
    print("开始添加文章到知识库")
    print("=" * 60)

    # 1. 爬取文章
    article_data = await crawl_article(url)
    if not article_data:
        print("\n❌ 爬取失败，请检查Chrome是否在调试模式运行")
        print("启动命令: ./start_chrome_debug.sh")
        return

    # 2. 自动分类
    print(f"\n正在分类文章...")
    category, tags, scores = classify_article(
        article_data['title'],
        article_data['content']
    )

    print(f"\n分类结果：")
    print(f"  主分类: {category}")
    print(f"  标签: {tags}")
    print(f"  各分类得分: {dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3])}")

    # 询问用户是否修改分类
    print(f"\n是否修改分类？(直接回车使用'{category}')")
    user_category = input("输入新分类 (人工智能/商业/金融/个人成长/历史/哲学/文学): ").strip()

    if user_category:
        category = user_category
        print(f"✓ 已修改为: {category}")

    # 3. 创建文章目录
    article_info = create_article_directory(article_data, category, tags)

    # 4. 更新索引
    update_index(article_info)

    print("\n" + "=" * 60)
    print("✅ 文章添加完成！")
    print("=" * 60)
    print(f"\n文章信息：")
    print(f"  ID: {article_info['id']}")
    print(f"  标题: {article_info['title']}")
    print(f"  分类: {article_info['category']}")
    print(f"  路径: knowledge_base/{article_info['path']}/")
    print(f"  字数: {article_info['word_count']}")
    print(f"\n文件结构：")
    print(f"  ├── article.md        # 文章正文")
    print(f"  ├── qa.md            # 问答记录")
    print(f"  ├── notes.md         # 阅读笔记")
    print(f"  ├── metadata.json    # 元数据")
    print(f"  └── attachments/")
    print(f"      ├── screenshot.png")
    print(f"      └── article.pdf")
    print(f"\n💡 提示：")
    print(f"  - 使用 add_note.py 添加阅读笔记")
    print(f"  - 使用 ask_article.py 进行问答（即将实现）")


if __name__ == "__main__":
    asyncio.run(main())
