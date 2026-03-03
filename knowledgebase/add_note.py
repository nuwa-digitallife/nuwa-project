#!/usr/bin/env python3
"""
添加阅读笔记到文章
使用方式：
  1. python add_note.py  (交互式输入)
  2. python add_note.py "笔记内容"  (快速添加到最近的文章)
  3. python add_note.py --article "文章标题关键词" "笔记内容"
"""
import json
import sys
from datetime import datetime
from pathlib import Path


KNOWLEDGE_BASE_DIR = Path("knowledge_base")
INDEX_FILE = KNOWLEDGE_BASE_DIR / "_index" / "articles_index.json"


def load_articles_index():
    """加载文章索引"""
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_article(keyword=None):
    """
    查找文章
    如果没有关键词，返回最新的文章
    """
    index = load_articles_index()
    articles = index['articles']

    if not articles:
        print("❌ 知识库中还没有文章")
        return None

    if not keyword:
        # 返回最新的文章（最后一个）
        return articles[-1]

    # 搜索包含关键词的文章
    matches = [a for a in articles if keyword.lower() in a['title'].lower()]

    if not matches:
        print(f"❌ 未找到包含 '{keyword}' 的文章")
        return None

    if len(matches) == 1:
        return matches[0]

    # 多个匹配，让用户选择
    print(f"\n找到 {len(matches)} 篇匹配的文章：")
    for i, article in enumerate(matches, 1):
        print(f"{i}. {article['title']} ({article['category']})")

    choice = input(f"\n选择文章 (1-{len(matches)}): ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx]
    except:
        pass

    print("❌ 无效的选择")
    return None


def add_note_to_article(article_info, note_content):
    """添加笔记到文章"""
    article_path = KNOWLEDGE_BASE_DIR / article_info['path']
    notes_file = article_path / "notes.md"

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 如果文件不存在，创建它
    if not notes_file.exists():
        with open(notes_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 阅读笔记

> 文章：{article_info['title']}

---

## {timestamp}

{note_content}

---

<!-- 继续在下方添加你的笔记 -->
""")
        print(f"✓ 已创建 notes.md 并添加笔记")
    else:
        # 读取现有内容
        with open(notes_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 在文件末尾添加新笔记
        new_note = f"""
## {timestamp}

{note_content}

---
"""

        # 在最后的注释前插入
        if "<!-- 继续在下方添加你的笔记 -->" in content:
            content = content.replace(
                "<!-- 继续在下方添加你的笔记 -->",
                f"{new_note}\n<!-- 继续在下方添加你的笔记 -->"
            )
        else:
            # 如果没有注释标记，直接追加
            content += new_note

        with open(notes_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ 已添加笔记到 notes.md")

    return notes_file


def interactive_mode():
    """交互式添加笔记"""
    print("=" * 60)
    print("交互式添加阅读笔记")
    print("=" * 60)

    # 1. 选择文章
    print("\n1. 选择文章")
    choice = input("   输入文章标题关键词 (直接回车选择最新文章): ").strip()

    article = find_article(choice if choice else None)

    if not article:
        return

    print(f"\n✓ 已选择文章: {article['title']}")

    # 2. 输入笔记
    print("\n2. 输入笔记内容 (输入完成后按 Ctrl+D 或输入 END 结束):")
    print("-" * 60)

    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
    except EOFError:
        pass

    note_content = "\n".join(lines).strip()

    if not note_content:
        print("❌ 笔记内容为空，取消添加")
        return

    print("-" * 60)

    # 3. 保存笔记
    notes_file = add_note_to_article(article, note_content)

    print("\n" + "=" * 60)
    print("✅ 笔记添加成功！")
    print("=" * 60)
    print(f"\n文章: {article['title']}")
    print(f"路径: {notes_file}")
    print(f"\n笔记内容：")
    print("-" * 60)
    print(note_content)
    print("-" * 60)


def quick_mode(note_content, article_keyword=None):
    """快速添加笔记"""
    article = find_article(article_keyword)

    if not article:
        return

    print(f"✓ 文章: {article['title']}")

    notes_file = add_note_to_article(article, note_content)

    print(f"✓ 路径: {notes_file}")
    print(f"\n笔记内容：")
    print("-" * 60)
    print(note_content)
    print("-" * 60)


def main():
    """主函数"""
    args = sys.argv[1:]

    if not args:
        # 无参数 - 交互式模式
        interactive_mode()
    elif len(args) == 1:
        # 一个参数 - 快速添加到最新文章
        quick_mode(args[0])
    elif len(args) >= 2 and args[0] in ['--article', '-a']:
        # 指定文章添加
        keyword = args[1]
        note = " ".join(args[2:]) if len(args) > 2 else None

        if not note:
            print("❌ 缺少笔记内容")
            print("使用方式: python add_note.py --article '关键词' '笔记内容'")
            return

        quick_mode(note, keyword)
    else:
        print("使用方式：")
        print("  1. python add_note.py                          # 交互式输入")
        print("  2. python add_note.py '笔记内容'                # 添加到最新文章")
        print("  3. python add_note.py -a '关键词' '笔记内容'    # 添加到指定文章")


if __name__ == "__main__":
    main()
