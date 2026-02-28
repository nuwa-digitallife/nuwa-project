#!/usr/bin/env python3
"""
Markdown → 带内联 CSS 的 HTML（微信公众号兼容）

跳过 mdnice.com 依赖，完全本地渲染。

流程:
  1. 读取 article_mdnice.md
  2. python-markdown 转 HTML
  3. 用 theme_orange.css 内联化所有样式
  4. 输出可直接粘贴到微信编辑器的 HTML

使用:
  python render_html.py article_mdnice.md                # → stdout
  python render_html.py article_mdnice.md -o output.html  # → 文件
  python render_html.py article_mdnice.md --preview        # → 浏览器预览
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
THEME_CSS = SCRIPT_DIR / "theme_orange.css"


def load_css(css_path: Path = None) -> str:
    """加载 CSS 文件"""
    path = css_path or THEME_CSS
    if not path.exists():
        print(f"WARNING: CSS not found at {path}, using minimal styles", file=sys.stderr)
        return "section { font-size: 16px; line-height: 1.8; color: #3f3f3f; }"
    return path.read_text(encoding="utf-8")


def markdown_to_html(md_text: str) -> str:
    """Markdown → raw HTML（不含 CSS）"""
    try:
        import markdown
    except ImportError:
        print("缺少 markdown: pip install markdown", file=sys.stderr)
        sys.exit(1)

    extensions = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.nl2br",
        "markdown.extensions.sane_lists",
    ]

    html = markdown.markdown(md_text, extensions=extensions, output_format="html5")
    return html


def inline_css(html: str, css_text: str) -> str:
    """将 CSS 规则内联到 HTML 元素的 style 属性中"""
    try:
        from premailer import transform
        # premailer 需要完整的 HTML 文档
        full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{css_text}</style>
</head><body><section>{html}</section></body></html>"""

        result = transform(
            full_html,
            remove_classes=True,
            strip_important=True,
            keep_style_tags=False,
            cssutils_logging_level="CRITICAL",
        )
        # 提取 <section> 内容
        match = re.search(r"<section[^>]*>(.*?)</section>", result, re.DOTALL)
        if match:
            return match.group(0)
        return result

    except ImportError:
        # fallback: 手动包裹 <style> 标签（不内联，但基本可用）
        print("WARNING: premailer not installed, using <style> fallback", file=sys.stderr)
        print("  pip install premailer", file=sys.stderr)
        return f"<style>{css_text}</style>\n<section>{html}</section>"


def strip_image_comments(html: str) -> str:
    """保留 HTML 注释（插图标记），微信编辑器会忽略它们"""
    return html


def render(md_path: str, css_path: str = None) -> str:
    """完整渲染流程: md文件 → 内联CSS的HTML"""
    md_text = Path(md_path).read_text(encoding="utf-8")
    css_text = load_css(Path(css_path) if css_path else None)
    raw_html = markdown_to_html(md_text)
    styled_html = inline_css(raw_html, css_text)
    return styled_html


def preview_in_browser(html: str):
    """在浏览器中预览渲染结果"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Preview</title>
<style>body {{ max-width: 680px; margin: 20px auto; }}</style>
</head><body>{html}</body></html>""")
        tmp_path = f.name
    subprocess.run(["open", tmp_path])
    print(f"Preview: {tmp_path}")


def main():
    parser = argparse.ArgumentParser(description="Markdown → 微信兼容 HTML")
    parser.add_argument("input", help="Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（默认 stdout）")
    parser.add_argument("--css", help="自定义 CSS 文件路径")
    parser.add_argument("--preview", action="store_true", help="在浏览器中预览")
    args = parser.parse_args()

    html = render(args.input, args.css)

    if args.preview:
        preview_in_browser(html)
    elif args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        print(f"Output: {args.output}")
    else:
        print(html)


if __name__ == "__main__":
    main()
