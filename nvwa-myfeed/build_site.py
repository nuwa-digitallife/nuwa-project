#!/usr/bin/env python3
"""构建脚本：将 output/*.md 转换为 site/data/digests.json"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
SITE_DIR = SCRIPT_DIR / "site"
DATA_DIR = SITE_DIR / "data"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML frontmatter，返回 (metadata, body)。"""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta = {}
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    val = val.strip().strip('"').strip("'")
                    meta[key.strip()] = val
            return meta, parts[2].strip()
    return {}, content


def extract_date_from_filename(filename: str) -> str:
    """从文件名提取日期，如 2026-02-11.md → 2026-02-11。"""
    match = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", filename)
    return match.group(1) if match else ""


def extract_summary_from_body(body: str) -> str:
    """从 markdown 正文提取'今日一句话'内容（兼容无 frontmatter 的旧格式）。"""
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if "今日一句话" in line:
            for next_line in lines[i + 1:]:
                stripped = next_line.strip()
                if stripped:
                    return stripped
    return ""


def md_to_html(md: str) -> str:
    """简易 Markdown → HTML 转换（覆盖日报用到的语法）。"""
    lines = md.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # 空行
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
            continue

        # 标题
        if stripped.startswith("### "):
            html_lines.append(f"<h3>{inline_md(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            html_lines.append(f"<h2>{inline_md(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            html_lines.append(f"<h1>{inline_md(stripped[2:])}</h1>")
            continue

        # 引用块
        if stripped.startswith("> "):
            html_lines.append(f"<blockquote>{inline_md(stripped[2:])}</blockquote>")
            continue

        # 分割线
        if stripped == "---" or stripped == "***":
            html_lines.append("<hr>")
            continue

        # 无序列表
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{inline_md(stripped[2:])}</li>")
            continue

        # 普通段落
        if in_list:
            html_lines.append("</ul>")
            in_list = False
        html_lines.append(f"<p>{inline_md(stripped)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def inline_md(text: str) -> str:
    """处理行内 Markdown：加粗、链接、行内代码。"""
    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # 加粗 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def build():
    """主构建流程。"""
    if not OUTPUT_DIR.exists():
        print(f"错误: 输出目录不存在: {OUTPUT_DIR}")
        return

    md_files = sorted(OUTPUT_DIR.glob("*.md"))
    if not md_files:
        print("没有找到 markdown 文件")
        return

    digests = []
    for md_file in md_files:
        print(f"  处理 {md_file.name} ...", end=" ")
        content = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)

        date = meta.get("date") or extract_date_from_filename(md_file.name)
        if not date:
            print("跳过（无法确定日期）")
            continue

        title = meta.get("title", f"AI 推特日报 {date}")
        summary = meta.get("summary") or extract_summary_from_body(body)
        html_content = md_to_html(body)

        digests.append({
            "date": date,
            "title": title,
            "summary": summary,
            "html": html_content,
        })
        print("OK")

    # 按日期排序
    digests.sort(key=lambda d: d["date"])

    # 写入 JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "digests.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(digests, f, ensure_ascii=False, indent=2)

    print(f"\n构建完成! {len(digests)} 篇日报 → {out_path}")


if __name__ == "__main__":
    build()
