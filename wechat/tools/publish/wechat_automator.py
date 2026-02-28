#!/usr/bin/env python3
"""
微信公众号编辑器 Playwright 自动化

通过 CDP 连接已登录的 Chrome (--remote-debugging-port=9222)，
自动完成：新建图文 → 粘贴 → 设标题 → 上传图片 → 开原创 → 保存。

比 AppleScript inject_js.py 更稳定：
- 能等待元素加载
- 能截图验证状态
- 不依赖前台窗口
- 能读取 DOM 状态

使用:
  python wechat_automator.py new-post              # 新建图文
  python wechat_automator.py paste                  # Cmd+V 粘贴剪贴板
  python wechat_automator.py set-title "标题"       # 设置标题
  python wechat_automator.py set-desc "简介"        # 设置简介
  python wechat_automator.py upload-cover cover.png  # 上传封面图
  python wechat_automator.py enable-original        # 开启原创+赞赏
  python wechat_automator.py save                   # 保存草稿
  python wechat_automator.py screenshot out.png     # 截图当前状态
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
JS_DIR = SCRIPT_DIR / "js"

# WeChat MP editor URL patterns
EDITOR_URL_PATTERN = "mp.weixin.qq.com"
NEW_POST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77"
DRAFT_LIST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_list&type=77"


class WeChatAutomator:
    """Playwright CDP 控制微信公众号编辑器"""

    def __init__(self, cdp_url: str = "http://localhost:9222", headless: bool = False):
        self.cdp_url = cdp_url
        self.headless = headless
        self.browser = None
        self.page = None

    async def connect(self):
        """连接到已运行的 Chrome 实例"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("缺少 playwright: pip install playwright && playwright install chromium", file=sys.stderr)
            sys.exit(1)

        self.pw = await async_playwright().__aenter__()
        self.browser = await self.pw.chromium.connect_over_cdp(self.cdp_url)
        # 获取第一个 context（已登录的）
        contexts = self.browser.contexts
        if not contexts:
            print("ERROR: Chrome 没有打开任何页面", file=sys.stderr)
            sys.exit(1)
        self.context = contexts[0]
        print(f"Connected to Chrome ({len(self.context.pages)} tabs)")

    async def find_editor_page(self):
        """找到微信编辑器 tab"""
        for page in self.context.pages:
            if "appmsg_edit" in page.url or "appmsg" in page.url:
                self.page = page
                await self.page.bring_to_front()
                print(f"Found editor: {page.url[:80]}")
                return True
        # 没找到，看看有没有微信后台页面
        for page in self.context.pages:
            if EDITOR_URL_PATTERN in page.url:
                self.page = page
                print(f"Found MP page: {page.url[:80]}")
                return True
        print("WARNING: 未找到微信公众号页面", file=sys.stderr)
        return False

    async def new_post(self):
        """导航到新建图文页面"""
        if not self.page:
            # 新开一个 tab
            self.page = await self.context.new_page()

        await self.page.goto(NEW_POST_URL, wait_until="domcontentloaded", timeout=30000)
        # 等待编辑器加载
        try:
            await self.page.wait_for_selector(
                '[contenteditable="true"]', timeout=15000
            )
            print("Editor loaded")
        except Exception:
            print("WARNING: 编辑器可能未完全加载", file=sys.stderr)
        return True

    async def paste_clipboard(self):
        """模拟 Cmd+V 粘贴"""
        if not self.page:
            raise RuntimeError("No page connected")

        # 点击编辑区域获得焦点
        editors = await self.page.query_selector_all('[contenteditable="true"]')
        if len(editors) > 1:
            # 第二个 contenteditable 通常是正文编辑器
            await editors[1].click()
        elif editors:
            await editors[0].click()
        else:
            print("WARNING: 未找到编辑区域", file=sys.stderr)
            return False

        await asyncio.sleep(0.3)

        # Cmd+V
        await self.page.keyboard.press("Meta+v")
        await asyncio.sleep(1)  # 等待粘贴完成

        print("Pasted clipboard content")
        return True

    async def set_title(self, title: str):
        """设置文章标题"""
        js = (JS_DIR / "set_title.js").read_text(encoding="utf-8")
        js = js.replace("__TITLE__", title.replace('"', '\\"').replace("'", "\\'"))
        result = await self.page.evaluate(js)
        print(f"Title set: {result}")
        return result

    async def set_description(self, desc: str):
        """设置文章简介"""
        js = (JS_DIR / "set_description.js").read_text(encoding="utf-8")
        js = js.replace("__DESCRIPTION__", desc.replace('"', '\\"').replace("'", "\\'"))
        result = await self.page.evaluate(js)
        print(f"Description set: {result}")
        return result

    async def upload_image_via_js(self, image_url: str, image_name: str = "image.png"):
        """通过 JS 注入上传图片到微信 CDN"""
        js = (JS_DIR / "upload_image.js").read_text(encoding="utf-8")

        # 从页面 URL 提取 token
        token = ""
        url_match = re.search(r"token=(\d+)", self.page.url)
        if url_match:
            token = url_match.group(1)

        js = js.replace("__IMAGE_URL__", image_url)
        js = js.replace("__TOKEN__", token)
        js = js.replace("__IMAGE_NAME__", image_name)

        result = await self.page.evaluate(js)
        print(f"Upload {image_name}: {result}")
        return result

    async def enable_original(self):
        """开启原创 + 赞赏"""
        js = (JS_DIR / "enable_original_reward.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"Original: {result}")

        # 等一下，可能会弹出确认对话框
        await asyncio.sleep(1)

        # 点击确认
        js_confirm = (JS_DIR / "click_confirm.js").read_text(encoding="utf-8")
        result2 = await self.page.evaluate(js_confirm)
        print(f"Confirm: {result2}")
        return result

    async def remove_empty_tables(self):
        """清除空表格"""
        js = (JS_DIR / "remove_empty_tables.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"Tables: {result}")
        return result

    async def trigger_save(self):
        """触发保存"""
        js = (JS_DIR / "trigger_save.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"Save: {result}")

        # 也尝试 Ctrl+S
        await self.page.keyboard.press("Meta+s")
        await asyncio.sleep(2)
        return result

    async def screenshot(self, output_path: str = "/tmp/wechat_editor.png"):
        """截图当前页面"""
        await self.page.screenshot(path=output_path, full_page=False)
        print(f"Screenshot: {output_path}")
        return output_path

    async def get_token(self) -> str:
        """从页面 URL 提取 token"""
        match = re.search(r"token=(\d+)", self.page.url)
        return match.group(1) if match else ""

    async def close(self):
        """关闭连接（不关闭浏览器）"""
        if self.pw:
            await self.pw.__aexit__(None, None, None)


async def run_command(args):
    """执行单个命令"""
    auto = WeChatAutomator(cdp_url=args.cdp_url)
    await auto.connect()

    found = await auto.find_editor_page()

    if args.command == "new-post":
        await auto.new_post()

    elif args.command == "paste":
        if not found:
            print("ERROR: 需要先打开编辑器", file=sys.stderr)
            return 1
        await auto.paste_clipboard()

    elif args.command == "set-title":
        if not found:
            return 1
        await auto.set_title(args.value)

    elif args.command == "set-desc":
        if not found:
            return 1
        await auto.set_description(args.value)

    elif args.command == "upload-cover":
        if not found:
            return 1
        # 启动 HTTPS 服务器后上传
        img_path = Path(args.value).resolve()
        print(f"Upload cover: {img_path}")
        await auto.upload_image_via_js(
            f"https://localhost:18443/{img_path.name}",
            img_path.name
        )

    elif args.command == "enable-original":
        if not found:
            return 1
        await auto.enable_original()

    elif args.command == "save":
        if not found:
            return 1
        await auto.trigger_save()

    elif args.command == "screenshot":
        if not found:
            return 1
        out = args.value if args.value else "/tmp/wechat_editor.png"
        await auto.screenshot(out)

    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    await auto.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="微信公众号编辑器自动化")
    parser.add_argument("command", choices=[
        "new-post", "paste", "set-title", "set-desc",
        "upload-cover", "enable-original", "save", "screenshot"
    ])
    parser.add_argument("value", nargs="?", default="", help="命令参数")
    parser.add_argument("--cdp-url", default="http://localhost:9222",
                        help="Chrome CDP URL")
    args = parser.parse_args()

    return asyncio.run(run_command(args))


if __name__ == "__main__":
    sys.exit(main())
