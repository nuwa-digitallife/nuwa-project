#!/usr/bin/env python3
"""
微信文章抓取工具 — 给 URL 就能抓取内容并保存为 Markdown。

使用方式：
  source ~/venv/automation/bin/activate
  python fetch_article.py <url> [url2 ...] [-o 输出目录]

示例：
  # 抓一篇，默认存到当前目录
  python fetch_article.py https://mp.weixin.qq.com/s/xxxxx

  # 抓多篇，指定输出目录
  python fetch_article.py url1 url2 url3 -o /path/to/output/

  # 入库到知识库（自动分类）
  python fetch_article.py https://mp.weixin.qq.com/s/xxxxx --kb

前置条件：
  - exporter 服务运行中 (localhost:3000)
  - pip install requests html2text
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("缺少 requests，请运行: pip install requests")
    sys.exit(1)

try:
    import html2text
except ImportError:
    print("缺少 html2text，请运行: pip install html2text")
    sys.exit(1)

EXPORTER_API = "http://localhost:3000/api/public/v1/download"

SCRIPT_DIR = Path(__file__).resolve().parent
KB_ROOT = SCRIPT_DIR.parent
KNOWLEDGE_BASE_DIR = KB_ROOT / "knowledge_base"
INDEX_FILE = KNOWLEDGE_BASE_DIR / "_index" / "articles_index.json"
RULES_FILE = KNOWLEDGE_BASE_DIR / "_index" / "classification_rules.json"


def sanitize_filename(title: str, max_len: int = 80) -> str:
    """清理文件名中的非法字符"""
    title = re.sub(r'[/\\:*?"<>|\n\r]', '_', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title[:max_len]


def fetch_article(url: str) -> dict | None:
    """
    从 exporter API 抓取文章，返回:
    {title, author, date, url, content_md, content_html,
     comment_id, elected_comment_total_cnt}
    """
    try:
        resp = requests.get(EXPORTER_API, params={"url": url, "format": "json"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  抓取失败: {e}")
        return None

    title = data.get("title", "untitled")
    author = data.get("meta_article_source", "") or data.get("author", "")
    create_time = data.get("create_time", 0)

    if isinstance(create_time, (int, float)) and create_time > 0:
        date_str = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d")
    else:
        date_str = "unknown"

    # HTML → Markdown
    html_content = data.get("content_noencode", "") or ""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0
    content_md = h.handle(html_content)

    return {
        "title": title,
        "author": author,
        "date": date_str,
        "url": url,
        "content_md": content_md,
        "content_html": html_content,
        "comment_id": data.get("comment_id", ""),
        "elected_comment_total_cnt": data.get("elected_comment_total_cnt", 0),
    }


def save_as_markdown(article: dict, output_dir: str) -> str:
    """保存为 Markdown 文件，返回文件路径"""
    os.makedirs(output_dir, exist_ok=True)

    safe_title = sanitize_filename(article["title"])
    filepath = os.path.join(output_dir, f"{safe_title}.md")

    # 避免重名
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filepath)
        i = 2
        while os.path.exists(f"{base}_{i}{ext}"):
            i += 1
        filepath = f"{base}_{i}{ext}"

    md = f"# {article['title']}\n\n"
    md += f"> 来源: {article['author']} | 日期: {article['date']} | [原文链接]({article['url']})\n"
    if article.get("elected_comment_total_cnt"):
        md += f"> 精选评论: {article['elected_comment_total_cnt']} 条\n"
    md += f"\n---\n\n"
    md += article["content_md"]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    return filepath


def classify_article(title: str, content: str) -> str:
    """根据 classification_rules.json 自动分类"""
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            rules = json.load(f)
    except Exception:
        return "未分类"

    text = (title + " " + content[:2000]).lower()
    best_cat = "未分类"
    best_score = 0

    for cat, info in rules.get("categories", {}).items():
        keywords = info.get("keywords", [])
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > best_score:
            best_score = score
            best_cat = cat

    return best_cat if best_score >= 2 else "未分类"


def save_to_knowledge_base(article: dict) -> str:
    """入库到知识库目录结构，返回保存路径"""
    category = classify_article(article["title"], article["content_md"])
    safe_title = sanitize_filename(article["title"])
    author = article["author"] or "未知来源"
    safe_author = sanitize_filename(author, max_len=30)

    article_dir = KNOWLEDGE_BASE_DIR / category / safe_author / safe_title
    article_dir.mkdir(parents=True, exist_ok=True)

    # article.md
    md = f"# {article['title']}\n\n"
    md += f"> 来源: {article['author']} | 日期: {article['date']} | [原文链接]({article['url']})\n\n"
    md += f"---\n\n"
    md += article["content_md"]
    (article_dir / "article.md").write_text(md, encoding="utf-8")

    # qa.md
    (article_dir / "qa.md").write_text(f"# Q&A: {article['title']}\n\n> 暂无问答记录\n", encoding="utf-8")

    # notes.md
    (article_dir / "notes.md").write_text(f"# 笔记: {article['title']}\n\n> 暂无笔记\n", encoding="utf-8")

    # metadata.json
    meta = {
        "title": article["title"],
        "author": article["author"],
        "source_url": article["url"],
        "crawl_date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "comment_id": article.get("comment_id", ""),
        "elected_comment_total_cnt": article.get("elected_comment_total_cnt", 0),
    }
    (article_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 更新索引
    _update_index(article, category, f"{category}/{safe_author}/{safe_title}")

    return str(article_dir)


def _update_index(article: dict, category: str, path: str):
    """更新 articles_index.json"""
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index = json.load(f)
    except Exception:
        return

    # 检查是否已存在
    for a in index["articles"]:
        if a["title"] == article["title"]:
            return

    today = datetime.now().strftime("%Y-%m-%d")
    new_id = f"article_{today.replace('-', '')}_{len(index['articles']) + 1:03d}"

    index["articles"].append({
        "id": new_id,
        "title": article["title"],
        "category": category,
        "author": article["author"],
        "crawl_date": today,
        "word_count": len(article["content_md"]),
        "read_status": "unread",
        "path": path,
        "tags": [],
    })
    index["total_articles"] = len(index["articles"])
    index["last_updated"] = today

    # 更新统计
    for cat in index.get("statistics", {}):
        index["statistics"][cat] = sum(1 for a in index["articles"] if a["category"] == cat)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, ensure_ascii=False, indent=2, fp=f)


def main():
    parser = argparse.ArgumentParser(description="微信文章抓取工具")
    parser.add_argument("urls", nargs="+", help="微信文章 URL（支持多个）")
    parser.add_argument("-o", "--output", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--kb", action="store_true", help="入库到知识库（自动分类）")
    args = parser.parse_args()

    # 检查 exporter
    try:
        requests.get("http://localhost:3000", timeout=5)
    except Exception:
        print("exporter 服务不可达 (localhost:3000)，请先启动")
        sys.exit(1)

    success, failed = 0, 0
    for i, url in enumerate(args.urls):
        print(f"[{i + 1}/{len(args.urls)}] {url}")
        article = fetch_article(url)
        if not article:
            failed += 1
            continue

        if args.kb:
            path = save_to_knowledge_base(article)
            print(f"  ✓ 入库: {path}")
        else:
            path = save_as_markdown(article, args.output)
            print(f"  ✓ 保存: {path}")

        success += 1
        if i < len(args.urls) - 1:
            time.sleep(0.3)

    print(f"\n完成: {success} 成功, {failed} 失败")


if __name__ == "__main__":
    main()
