#!/usr/bin/env python3
"""
通过 AppleScript 向 Chrome 微信编辑器注入 JS 并执行。

核心技巧：中文在 AppleScript 嵌套 JS 时会报转义错误，
所以先 base64 编码，再用 eval(atob('...')) 执行。

用法：
  # 执行 JS 文件
  python inject_js.py path/to/script.js

  # 执行 JS 文件，替换模板变量
  python inject_js.py path/to/template.js --var __TITLE__="我的标题" --var __DESC__="简介"

  # 直接执行 JS 字符串
  python inject_js.py --eval "document.title"
"""
import argparse
import base64
import json
import subprocess
import sys
import time


def find_wechat_editor_window():
    """在所有 Chrome 窗口中找到微信编辑器 tab"""
    script = '''
    tell application "Google Chrome"
        set windowCount to count of windows
        repeat with w from 1 to windowCount
            set tabCount to count of tabs of window w
            repeat with t from 1 to tabCount
                set tabUrl to URL of tab t of window w
                if tabUrl contains "appmsg_edit" then
                    return (w as string) & "|" & (t as string)
                end if
            end repeat
        end repeat
        return "not_found"
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    output = result.stdout.strip()
    if output == "not_found" or not output:
        return None, None
    parts = output.split('|')
    return int(parts[0].strip()), int(parts[1].strip())


def inject_js(js_code, window_idx=None, tab_idx=None, timeout=30):
    """注入 JS 到 Chrome 并返回结果"""
    # Base64 encode to avoid AppleScript escaping issues
    b64 = base64.b64encode(js_code.encode('utf-8')).decode('ascii')

    if window_idx is None or tab_idx is None:
        window_idx, tab_idx = find_wechat_editor_window()
        if window_idx is None:
            print("ERROR: 未找到微信编辑器 tab（URL 包含 appmsg_edit）", file=sys.stderr)
            sys.exit(1)

    script = f'''
    tell application "Google Chrome"
        set idx to {window_idx}
        set tidx to {tab_idx}
        tell tab tidx of window idx
            set jsResult to execute javascript "eval(decodeURIComponent(escape(atob('{b64}'))))"
            return jsResult
        end tell
    end tell
    '''
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True, text=True, timeout=timeout
    )

    if result.returncode != 0:
        print(f"AppleScript error: {result.stderr.strip()}", file=sys.stderr)
        return None

    return result.stdout.strip()


def inject_js_file(filepath, variables=None, window_idx=None, tab_idx=None):
    """读取 JS 文件，替换模板变量，注入执行"""
    with open(filepath, 'r', encoding='utf-8') as f:
        js_code = f.read()

    if variables:
        for key, value in variables.items():
            # Escape for JS string
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            js_code = js_code.replace(key, escaped)

    return inject_js(js_code, window_idx, tab_idx)


def main():
    parser = argparse.ArgumentParser(description='向 Chrome 微信编辑器注入 JS')
    parser.add_argument('file', nargs='?', help='JS 文件路径')
    parser.add_argument('--eval', '-e', dest='js_eval', help='直接执行 JS 字符串')
    parser.add_argument('--var', '-v', action='append', default=[], help='模板变量 KEY=VALUE')
    parser.add_argument('--window', '-w', type=int, help='Chrome 窗口编号')
    parser.add_argument('--tab', '-t', type=int, help='Chrome tab 编号')
    parser.add_argument('--wait', type=float, default=0, help='执行前等待秒数')
    args = parser.parse_args()

    if args.wait > 0:
        time.sleep(args.wait)

    # Parse variables
    variables = {}
    for v in args.var:
        key, value = v.split('=', 1)
        variables[key] = value

    if args.js_eval:
        result = inject_js(args.js_eval, args.window, args.tab)
    elif args.file:
        result = inject_js_file(args.file, variables or None, args.window, args.tab)
    else:
        parser.print_help()
        sys.exit(1)

    if result is not None:
        print(result)
    return 0 if result is not None else 1


if __name__ == '__main__':
    sys.exit(main())
