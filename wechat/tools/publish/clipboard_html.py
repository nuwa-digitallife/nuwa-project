#!/usr/bin/env python3
"""
HTML → macOS 剪贴板（保留富文本格式）

使用 AppKit NSPasteboard 将 HTML 写入剪贴板的 NSHTMLPboardType。
Chrome 粘贴时会保留完整的 HTML 格式，包括内联 CSS。

使用:
  python clipboard_html.py rendered.html       # 从文件读取
  echo '<h1>test</h1>' | python clipboard_html.py  # 从 stdin 读取
  python clipboard_html.py --text "纯文本"     # 纯文本模式
"""

import argparse
import sys
from pathlib import Path


def copy_html_to_clipboard(html: str) -> bool:
    """将 HTML 复制到 macOS 剪贴板（NSHTMLPboardType + 纯文本 fallback）"""
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeHTML, NSPasteboardTypeString
    except ImportError:
        print("缺少 PyObjC: pip install pyobjc-framework-Cocoa", file=sys.stderr)
        return _fallback_copy(html)

    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()

    # 同时写入 HTML 和纯文本格式
    pb.setString_forType_(html, NSPasteboardTypeHTML)

    # 纯文本 fallback（去除 HTML 标签）
    import re
    plain = re.sub(r"<[^>]+>", "", html)
    plain = re.sub(r"\s+", " ", plain).strip()
    pb.setString_forType_(plain, NSPasteboardTypeString)

    return True


def copy_text_to_clipboard(text: str) -> bool:
    """纯文本复制"""
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString
    except ImportError:
        return _fallback_copy(text)

    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(text, NSPasteboardTypeString)
    return True


def _fallback_copy(content: str) -> bool:
    """fallback: 用 pbcopy"""
    import subprocess
    try:
        proc = subprocess.run(
            ["pbcopy"],
            input=content.encode("utf-8"),
            timeout=5,
        )
        if proc.returncode == 0:
            print("WARNING: 使用 pbcopy fallback（纯文本，无富文本格式）", file=sys.stderr)
            return True
    except Exception as e:
        print(f"Clipboard error: {e}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="HTML → macOS 剪贴板")
    parser.add_argument("input", nargs="?", help="HTML 文件路径（不指定则读 stdin）")
    parser.add_argument("--text", help="直接复制纯文本")
    args = parser.parse_args()

    if args.text:
        ok = copy_text_to_clipboard(args.text)
        if ok:
            print(f"Copied text ({len(args.text)} chars)")
        return 0 if ok else 1

    # 读取 HTML
    if args.input:
        html = Path(args.input).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        html = sys.stdin.read()
    else:
        print("用法: python clipboard_html.py <file.html>", file=sys.stderr)
        return 1

    ok = copy_html_to_clipboard(html)
    if ok:
        print(f"Copied HTML ({len(html)} chars) to clipboard")
    else:
        print("Failed to copy to clipboard", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
