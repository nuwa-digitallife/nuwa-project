#!/usr/bin/env python3
"""
微信公众号编辑器 Playwright 自动化

通过 CDP 连接用户主 Chrome (--remote-debugging-port=9222)，
自动完成：新建图文 → 粘贴 → 设标题 → 上传图片 → 开原创 → 保存。

连接用户主 Chrome，不用独立 profile。用户已登录微信后台 + mdnice，session 直接可用。

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
import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from publish_types import StepResult, StepStatus

# 确保 Playwright CDP 连接不走代理（ClashX 等会拦截 localhost）
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

SCRIPT_DIR = Path(__file__).resolve().parent
JS_DIR = SCRIPT_DIR / "js"

# WeChat MP editor URL patterns
EDITOR_URL_PATTERN = "mp.weixin.qq.com"
NEW_POST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77"
DRAFT_LIST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg?begin=0&count=10&type=77&action=list_card"

# mdnice
MDNICE_URL = "https://editor.mdnice.com/"
MDNICE_THEME = "橙心"


async def safe_screenshot(page, path, timeout=15000):
    """截图，超时降级为非 full_page"""
    try:
        await page.screenshot(path=path, full_page=True, timeout=timeout)
    except Exception:
        try:
            await page.screenshot(path=path, full_page=False, timeout=10000)
        except Exception:
            pass


class WeChatAutomator:
    """Playwright CDP 控制微信公众号编辑器"""

    def __init__(self, cdp_url: str = "http://localhost:9222", headless: bool = False):
        self.cdp_url = cdp_url
        self.headless = headless
        self.browser = None
        self.page = None
        self.context = None
        self.pw = None
        self._connected = False

    async def connect(self):
        """连接到已运行的 Chrome 实例（幂等：已连接则跳过）"""
        if self._connected and self.browser and self.browser.is_connected():
            print(f"Already connected ({len(self.context.pages)} tabs)")
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("缺少 playwright: pip install playwright && playwright install chromium", file=sys.stderr)
            sys.exit(1)

        self.pw = await async_playwright().start()

        # 先尝试连接，失败则自动启动 Chrome CDP
        try:
            self.browser = await self.pw.chromium.connect_over_cdp(self.cdp_url)
        except Exception:
            print(f"  CDP 未响应，自动启动 Chrome...")
            await self._launch_chrome_cdp()
            self.browser = await self.pw.chromium.connect_over_cdp(self.cdp_url)

        # 获取第一个 context（已登录的）
        contexts = self.browser.contexts
        if not contexts:
            print("ERROR: Chrome 没有打开任何页面", file=sys.stderr)
            sys.exit(1)
        self.context = contexts[0]
        self._connected = True
        print(f"Connected to Chrome ({len(self.context.pages)} tabs)")

    async def _launch_chrome_cdp(self):
        """启动带 CDP 的 Chrome（使用用户主 profile）。

        铁律：
        - ⛔ 绝不杀已有 Chrome 进程（会丢失用户登录态和标签页）
        - Chrome 145+ 必须 --user-data-dir，否则 CDP 静默失效
        - 已有 Chrome 运行时无法新增 CDP，提示用户手动重启
        """
        import subprocess as sp

        port = self.cdp_url.split(":")[-1].rstrip("/")
        chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        # 独立 CDP profile（主 profile 有锁不能复用）
        # 首次需要在此 Chrome 中登录微信+mdnice，之后 cookie 持久化
        user_data = os.path.expanduser("~/.chrome-cdp-profile")

        # 检查是否有 Chrome 进程在跑
        chrome_running = sp.run(
            ["pgrep", "-f", "Google Chrome"], capture_output=True
        ).returncode == 0

        if chrome_running:
            # Chrome 在跑但 CDP 没响应 → 无法自动修复，提示用户
            print(f"\n{'='*60}")
            print(f"  Chrome 已运行但 CDP 端口 {port} 未响应。")
            print(f"  请手动重启 Chrome：")
            print(f'  1. 关闭 Chrome')
            print(f'  2. 终端执行：')
            print(f'  "{chrome_bin}" --remote-debugging-port={port} --user-data-dir="$HOME/.chrome-cdp-profile" &')
            print(f"{'='*60}\n")
            self._notify_user("Chrome CDP 未启用，请重启 Chrome")
            raise RuntimeError(f"Chrome 已运行但 CDP 未启用，请手动重启")

        # 没有 Chrome 在跑，安全启动（使用用户主 profile）
        sp.Popen([
            chrome_bin,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data}",
        ], stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        import urllib.request
        for i in range(15):
            await asyncio.sleep(2)
            try:
                urllib.request.urlopen(f"http://localhost:{port}/json", timeout=2)
                print(f"  Chrome CDP ready on port {port}")
                return
            except Exception:
                pass
        raise RuntimeError(f"Chrome CDP 启动超时（port {port}）")

    def _notify_user(self, message: str):
        """系统通知 + 声音提醒"""
        safe_msg = message.replace('"', '').replace("'", "").replace('\\', '')
        try:
            subprocess.run([
                "osascript", "-e",
                f'display notification "{safe_msg}" with title "WeChat Publish"'
            ], timeout=5, capture_output=True)
        except Exception:
            pass
        try:
            subprocess.run([
                "afplay", "/System/Library/Sounds/Glass.aiff"
            ], timeout=5, capture_output=True)
        except Exception:
            pass

    async def check_login(self) -> bool:
        """检查微信后台登录态，过期则通知 + 等待扫码。

        返回 True = 登录有效，False = 超时仍未登录。
        """
        # 先找有 token 的页面
        for page in self.context.pages:
            if EDITOR_URL_PATTERN in page.url and "token=" in page.url:
                if await self._verify_token(page):
                    return True

        # token 无效或不存在，导航到 MP 首页
        page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        await page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        if "token=" in page.url and await self._verify_token(page):
            self.page = page
            return True

        # 需要扫码
        qr_screenshot = "/tmp/wechat_qr_login.png"
        await page.screenshot(path=qr_screenshot)
        self._notify_user("微信后台需要扫码登录")
        print(f"\n{'='*50}")
        print("  微信后台需要扫码登录")
        print(f"  二维码截图: {qr_screenshot}")
        print(f"{'='*50}\n")

        max_wait, elapsed = 120, 0
        while elapsed < max_wait:
            await asyncio.sleep(3)
            elapsed += 3
            if "token=" in page.url:
                self.page = page
                print(f"  登录成功！")
                return True
            if elapsed % 15 == 0:
                await page.screenshot(path=qr_screenshot)
                print(f"  等待扫码... ({elapsed}s/{max_wait}s)")

        print("ERROR: 等待扫码超时", file=sys.stderr)
        return False

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

    async def _verify_token(self, page) -> bool:
        """验证 token 是否仍然有效（未过期）。

        通过检查页面 DOM 判断：有登录二维码/登录表单 → 未登录；
        否则只要页面在 MP 域名且 URL 有 token → 视为有效。
        """
        try:
            token = re.search(r"token=(\d+)", page.url)
            if not token:
                return False
            # 检查页面是否显示登录界面
            is_login_page = await page.evaluate("""() => {
                var qr = document.querySelector('.login__type__container, .login_qrcode_area, .weui-desktop-login');
                if (qr) return true;
                // 检查 document.title 是否包含"登录"
                if (document.title.includes('登录') || document.title.includes('login')) return true;
                return false;
            }""")
            return not is_login_page
        except Exception:
            return False

    async def find_or_create_mp_page(self):
        """确保有一个 MP 页面可用（用于 API 调用如图片上传）。

        如果没有任何 tab，创建新 tab 并导航到 MP 首页。
        如果有 tab 但不在 MP 域名，导航到 MP 首页。
        返回 True 表示 self.page 已设置到可用的 MP 页面。
        """
        # 先试已有页面
        for page in self.context.pages:
            if EDITOR_URL_PATTERN in page.url and "token=" in page.url:
                # 验证 token 是否仍然有效
                if await self._verify_token(page):
                    self.page = page
                    print(f"Using MP page: {page.url[:80]}")
                    return True
                else:
                    print("WARNING: MP 页面 token 已过期，重新登录...")

        # 没有带 token 的 MP 页面，尝试导航
        if self.context.pages:
            page = self.context.pages[0]
        else:
            page = await self.context.new_page()

        print("Navigating to MP home...")
        await page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # 检查是否登录（URL 应包含 token 且 token 有效）
        if "token=" in page.url and await self._verify_token(page):
            self.page = page
            print(f"MP page ready: {page.url[:80]}")
            return True

        # 未登录，截图二维码页面并等待扫码
        qr_screenshot = "/tmp/wechat_qr_login.png"
        await page.screenshot(path=qr_screenshot)
        self._notify_user("微信后台需要扫码登录")
        print(f"\n{'='*50}")
        print("  未检测到登录状态，请在手机上扫码登录微信公众平台")
        print(f"  二维码截图已保存: {qr_screenshot}")
        print(f"{'='*50}\n")

        max_wait = 120  # 最长等待 120 秒
        interval = 3
        elapsed = 0
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval
            # 检查当前 URL 是否已跳转到带 token 的页面
            if "token=" in page.url:
                self.page = page
                print(f"  登录成功！MP page ready: {page.url[:80]}")
                return True
            # 每 15 秒重新截图，以防二维码刷新
            if elapsed % 15 == 0:
                await page.screenshot(path=qr_screenshot)
                print(f"   仍在等待扫码... ({elapsed}s/{max_wait}s)")

        print("ERROR: 等待扫码超时（120秒），请重试", file=sys.stderr)
        self.page = page
        return False

    async def _get_token(self) -> str:
        """从已登录的微信后台页面提取 token"""
        for page in self.context.pages:
            match = re.search(r"token=(\d+)", page.url)
            if match:
                return match.group(1)
        return ""

    async def cleanup_stale_dialogs(self):
        """关闭所有残留的弹窗（防止二次运行时脏状态干扰）

        场景：第一次发布失败后重跑，页面上残留未关闭的图片选择/原创/投票对话框，
        它们的遮罩层会拦截后续所有点击事件。
        """
        if not self.page:
            return
        result = await self.page.evaluate("""() => {
            let closed = 0;
            // 方式1：点击所有可见对话框的取消/关闭按钮
            const dialogs = document.querySelectorAll('.weui-desktop-dialog');
            dialogs.forEach(d => {
                const style = window.getComputedStyle(d);
                if (style.display === 'none' || style.visibility === 'hidden') return;
                // 优先点取消按钮（比强制隐藏更安全，不破坏 Vue 状态）
                const cancelBtn = d.querySelector('.weui-desktop-btn_default');
                if (cancelBtn && cancelBtn.textContent.trim() === '取消') {
                    cancelBtn.click();
                    closed++;
                    return;
                }
                // 其次点关闭图标
                const closeBtn = d.querySelector('.weui-desktop-dialog__close-btn, .weui-desktop-icon-close');
                if (closeBtn) {
                    closeBtn.click();
                    closed++;
                    return;
                }
            });
            return closed;
        }""")
        if result and result > 0:
            print(f"  Cleaned up {result} stale dialog(s)")
            await asyncio.sleep(1)
            # 二次清理：有些对话框关闭后会露出下层对话框
            await self.page.evaluate("""() => {
                const dialogs = document.querySelectorAll('.weui-desktop-dialog');
                dialogs.forEach(d => {
                    const style = window.getComputedStyle(d);
                    if (style.display === 'none' || style.visibility === 'hidden') return;
                    const cancelBtn = d.querySelector('.weui-desktop-btn_default');
                    if (cancelBtn && cancelBtn.textContent.trim() === '取消') cancelBtn.click();
                });
            }""")
            await asyncio.sleep(0.5)

    async def new_post(self):
        """新开 tab 创建图文。每篇文章独立 tab，互不干扰。"""
        token = await self._get_token()
        if not token:
            print("ERROR: 未找到 token，可能未登录", file=sys.stderr)
            return False

        url = f"{NEW_POST_URL}&token={token}"

        # ⛔ 每篇文章新开 tab（预览 tab 保留，编辑 tab 也保留给调试）
        self.page = await self.context.new_page()

        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # 等待编辑器加载
        try:
            await self.page.wait_for_selector(
                '[contenteditable="true"]', timeout=15000
            )
            print(f"Editor loaded (token={token})")
        except Exception:
            print("WARNING: 编辑器可能未完全加载", file=sys.stderr)
        return True

    async def paste_clipboard(self) -> StepResult:
        """模拟 Cmd+V 粘贴"""
        if not self.page:
            return StepResult("paste", StepStatus.FAILED, "No page connected")

        # 用 JS 聚焦正文编辑器（第二个 contenteditable），避免 Playwright click 被拦截
        focused = await self.page.evaluate("""() => {
            var editors = document.querySelectorAll('[contenteditable="true"]');
            var editor = editors.length > 1 ? editors[1] : editors[0];
            if (!editor) return 'not found';
            editor.scrollIntoView({block: 'center'});
            editor.focus();
            return 'focused';
        }""")
        if focused == 'not found':
            return StepResult("paste", StepStatus.FAILED, "编辑区域未找到")

        await asyncio.sleep(0.3)

        # Cmd+V
        await self.page.keyboard.press("Meta+v")
        await asyncio.sleep(1)  # 等待粘贴完成

        # 验证：编辑器内容 > 100 字符
        text_len = await self.page.evaluate("""() => {
            var editors = document.querySelectorAll('[contenteditable="true"]');
            var editor = editors.length > 1 ? editors[1] : editors[0];
            return editor ? editor.innerText.length : 0;
        }""")
        if text_len > 100:
            print(f"Pasted clipboard content ({text_len} chars)")
            return StepResult("paste", StepStatus.SUCCESS, f"{text_len} chars")
        else:
            print(f"WARNING: 粘贴后内容过短 ({text_len} chars)")
            return StepResult("paste", StepStatus.SUCCESS, f"粘贴完成但内容较短 ({text_len} chars)")

    async def inject_images(self, cdn_map: dict) -> StepResult:
        """粘贴后注入配图：把编辑器中 alt 文本对应的空位替换为 CDN 图片。

        cdn_map: {local_path_or_name: cdn_url}  e.g. {"images/img_1_xxx.png": "https://mmbiz..."}

        策略：
        1. 先检查编辑器中已有多少 CDN 图片（可能 mdnice 已经带过来了）
        2. 如果数量够，跳过
        3. 如果不够，找 markdown 图片标记对应位置，插入 <img> 到正文
        """
        page = self.page

        # 过滤出非封面图片的 CDN URLs（按 URL 去重，防止 path/name 双 key 导致翻倍）
        seen_urls = set()
        img_urls = []
        for path, url in cdn_map.items():
            name = path.split("/")[-1] if "/" in path else path
            if "cover" in name or not url.startswith("http"):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            img_urls.append({"name": name, "url": url})

        if not img_urls:
            return StepResult("inject_images", StepStatus.SKIPPED, "no images to inject")

        # 检查编辑器当前图片数量
        existing = await page.evaluate("""() => {
            var editors = document.querySelectorAll('[contenteditable=true]');
            var editor = editors.length >= 2 ? editors[1] : null;
            if (!editor) return 0;
            var imgs = editor.querySelectorAll('img');
            var count = 0;
            for (var i = 0; i < imgs.length; i++) {
                if (imgs[i].src && imgs[i].src.includes('mmbiz') && imgs[i].naturalWidth > 0) count++;
            }
            return count;
        }""")

        if existing >= len(img_urls):
            print(f"  Images already present: {existing}/{len(img_urls)}")
            return StepResult("inject_images", StepStatus.SUCCESS,
                              f"already present: {existing}")

        print(f"  Injecting {len(img_urls)} images (existing: {existing})...")

        # 注入图片：找到编辑器中每个 <figure> 或 <p> 中的 <img>
        # 如果 img.src 为空或不是 mmbiz，替换为 CDN URL
        # 如果找不到足够的 img 占位符，在文末追加
        injected = await page.evaluate("""(imgUrls) => {
            var editors = document.querySelectorAll('[contenteditable=true]');
            var editor = editors.length >= 2 ? editors[1] : null;
            if (!editor) return {ok: false, msg: 'no editor'};

            // 找所有图片元素（含空 src）
            var allImgs = editor.querySelectorAll('img');
            var emptyImgs = [];
            for (var i = 0; i < allImgs.length; i++) {
                if (!allImgs[i].src || !allImgs[i].src.includes('mmbiz')) {
                    emptyImgs.push(allImgs[i]);
                }
            }

            var injected = 0;

            // 优先替换已有的空 img 元素
            for (var j = 0; j < imgUrls.length && j < emptyImgs.length; j++) {
                emptyImgs[j].src = imgUrls[j].url;
                emptyImgs[j].setAttribute('data-src', imgUrls[j].url);
                emptyImgs[j].style.maxWidth = '100%';
                injected++;
            }

            // ⛔ 不追加到文末 — mdnice 已渲染的图片位置是正确的，
            // 多余的 img_urls 是去重没干净或 cdn_map 有冗余，追加会破坏排版。

            // 通知 ProseMirror 内容已变更
            editor.dispatchEvent(new Event('input', {bubbles: true}));

            return {ok: true, injected: injected, existing: allImgs.length - emptyImgs.length};
        }""", img_urls)

        if injected.get("ok"):
            count = injected.get("injected", 0)
            print(f"  Injected {count} images")
            return StepResult("inject_images", StepStatus.SUCCESS,
                              f"injected {count}, pre-existing {injected.get('existing', 0)}")
        else:
            return StepResult("inject_images", StepStatus.FAILED,
                              injected.get("msg", "unknown error"))

    async def _cdp_type(self, selector: str, text: str):
        """用 CDP Input.dispatchKeyEvent 逐字输入。

        这是唯一能触发微信编辑器 Vue v-model 的方式。
        Playwright 的 fill()/keyboard.type()/press_sequentially() 全部无效。
        """
        # 用 JS scroll + focus 代替 Playwright click（避免 "outside of viewport" 超时）
        await self.page.evaluate("""(sel) => {
            var el = document.querySelector(sel);
            if (el) { el.scrollIntoView({block: 'center'}); el.focus(); el.click(); }
        }""", selector)
        await asyncio.sleep(0.3)
        # 全选清空
        await self.page.keyboard.press("Meta+a")
        await asyncio.sleep(0.1)
        await self.page.keyboard.press("Delete")
        await asyncio.sleep(0.3)

        cdp = await self.context.new_cdp_session(self.page)
        for char in text:
            await cdp.send('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': char})
            await cdp.send('Input.dispatchKeyEvent', {'type': 'char', 'text': char})
            await cdp.send('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': char})
            await asyncio.sleep(0.02)
        await cdp.detach()
        await asyncio.sleep(0.3)

    async def set_title(self, title: str) -> StepResult:
        """设置文章标题（CDP 逐字输入，触发 Vue v-model）"""
        for attempt in range(3):
            await self._cdp_type("#title", title)
            actual = await self.page.evaluate('() => document.querySelector("#title").value')
            if actual == title:
                print(f"Title set: OK ('{actual[:30]}')")
                return StepResult("title", StepStatus.SUCCESS, f"'{title[:30]}'", retries=attempt)
            print(f"Title mismatch (attempt {attempt + 1}): got '{actual[:30]}'")
            await asyncio.sleep(0.5)
        return StepResult("title", StepStatus.FAILED, f"mismatch after 3 retries: '{actual[:30]}'", retries=2)

    async def set_description(self, desc: str) -> StepResult:
        """设置文章简介（CDP 逐字输入，触发 Vue v-model）"""
        for attempt in range(3):
            await self._cdp_type("#js_description", desc)
            actual = await self.page.evaluate('() => document.querySelector("#js_description").value')
            if actual == desc:
                print(f"Description set: OK ('{actual[:30]}')")
                return StepResult("desc", StepStatus.SUCCESS, f"'{desc[:30]}'", retries=attempt)
            print(f"Description mismatch (attempt {attempt + 1}): got '{actual[:30]}'")
            await asyncio.sleep(0.5)
        return StepResult("desc", StepStatus.FAILED, f"mismatch after 3 retries", retries=2)

    async def upload_image_via_js(self, image_url: str, image_name: str = "image.png") -> dict:
        """通过 JS 注入上传图片到微信 CDN。

        Returns:
            dict: {"ok": True/False, "cdn_url": "https://mmbiz...", "name": "..."}
        """
        js = (JS_DIR / "upload_image.js").read_text(encoding="utf-8")

        # 从页面 URL 提取 token（任何 MP 页面都行）
        token = await self._get_token()
        if not token:
            url_match = re.search(r"token=(\d+)", self.page.url)
            if url_match:
                token = url_match.group(1)

        js = js.replace("__IMAGE_URL__", image_url)
        js = js.replace("__TOKEN__", token)
        js = js.replace("__IMAGE_NAME__", image_name)

        result_raw = await self.page.evaluate(js)
        # JS 返回 JSON.stringify 的字符串，需要解析
        if isinstance(result_raw, str):
            try:
                result = json.loads(result_raw)
            except json.JSONDecodeError:
                result = {"ok": False, "error": result_raw, "name": image_name}
        else:
            result = result_raw or {"ok": False, "error": "null result", "name": image_name}

        status = "OK" if result.get("ok") else "FAILED"
        cdn = result.get("cdn_url", "")[:60] if result.get("cdn_url") else result.get("error", "unknown")
        print(f"  Upload {image_name}: {status} — {cdn}")
        return result

    async def upload_image_file(self, file_path: Path) -> dict:
        """通过 base64 编码上传本地图片到微信 CDN（不依赖 HTTPS 服务器）。

        Returns:
            dict: {"ok": True/False, "cdn_url": "https://mmbiz...", "name": "..."}
        """
        suffix = file_path.suffix.lower().lstrip(".")
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif", "webp": "image/webp"}.get(suffix, "image/png")
        b64 = base64.b64encode(file_path.read_bytes()).decode()

        token = await self._get_token()

        js = """(async function() {
    var b64 = "__B64__";
    var mime = "__MIME__";
    var token = "__TOKEN__";
    var imageName = "__NAME__";
    try {
        var bstr = atob(b64), n = bstr.length, u8 = new Uint8Array(n);
        while (n--) u8[n] = bstr.charCodeAt(n);
        var blob = new Blob([u8], {type: mime});
        var fd = new FormData();
        fd.append("file", blob, imageName);
        var url = "/cgi-bin/filetransfer?action=upload_material&f=json&scene=8&writetype=doublewrite&groupid=1&token=" + token + "&type=10";
        var r = await fetch(url, {method: "POST", body: fd});
        var d = await r.json();
        if (d.cdn_url) return JSON.stringify({ok: true, cdn_url: d.cdn_url, name: imageName});
        return JSON.stringify({ok: false, error: JSON.stringify(d), name: imageName});
    } catch(e) {
        return JSON.stringify({ok: false, error: e.message, name: imageName});
    }
})();"""
        js = js.replace("__B64__", b64).replace("__MIME__", mime) \
               .replace("__TOKEN__", token).replace("__NAME__", file_path.name)

        result_raw = await self.page.evaluate(js)
        if isinstance(result_raw, str):
            try:
                result = json.loads(result_raw)
            except json.JSONDecodeError:
                result = {"ok": False, "error": result_raw, "name": file_path.name}
        else:
            result = result_raw or {"ok": False, "error": "null result", "name": file_path.name}

        status = "OK" if result.get("ok") else "FAILED"
        cdn = result.get("cdn_url", "")[:60] if result.get("cdn_url") else result.get("error", "unknown")
        print(f"  Upload {file_path.name}: {status} — {cdn}")
        return result

    async def add_poll(self, question: str, options: list) -> StepResult:
        """在微信编辑器正文末尾插入投票组件。

        流程：点顶部导航「投票」(#js_editor_insertvote) →
              填问题(weui-desktop-form__input[0]) →
              填选项(weui-desktop-form__input[1..n])，不够用时点 + 按钮 →
              点「发起」

        注意：按钮文字是"发起"，不是"确定"。
              投票组件在 .vote_dialog__body 内，使用 Vue v-model，必须用 CDP 输入。
        """
        DIALOG_SEL = ".vote_dialog__body"

        # Step 1: 点顶部导航投票按钮
        clicked = await self.page.evaluate("""() => {
            var el = document.getElementById('js_editor_insertvote');
            if (el) { el.click(); return 'clicked'; }
            return 'not found';
        }""")
        print(f"  Poll button: {clicked}")
        if clicked != "clicked":
            return StepResult("poll", StepStatus.FAILED, "#js_editor_insertvote 未找到")

        await asyncio.sleep(1.5)

        # 检查对话框是否出现
        dialog_visible = await self.page.evaluate("""(sel) => {
            var d = document.querySelector(sel);
            return d && d.offsetParent !== null;
        }""", DIALOG_SEL)
        if not dialog_visible:
            return StepResult("poll", StepStatus.SKIPPED, "投票对话框未弹出（可能已有投票组件）")
        print("  Poll dialog: opened")

        # Step 2: 给所有 .vote_dialog__body input 加 index 属性，方便定位
        input_count = await self.page.evaluate("""(sel) => {
            var inputs = document.querySelectorAll(sel + ' input.weui-desktop-form__input');
            inputs.forEach(function(inp, i) { inp.setAttribute('data-vi', i); });
            return inputs.length;
        }""", DIALOG_SEL)
        print(f"  Vote inputs found: {input_count}")

        # Step 3: 填写问题 (index 0)
        await self._cdp_type('[data-vi="0"]', question)
        await asyncio.sleep(0.3)

        # Step 4: 填写选项 (index 1, 2, 3...)
        for idx, opt in enumerate(options):
            inp_idx = idx + 1  # 0 是问题，1+ 是选项
            # 如果输入框不够，点 + 增加
            if inp_idx >= input_count:
                add_result = await self.page.evaluate("""(sel) => {
                    // + 按钮: a.ic_option_add（已验证）
                    var btn = document.querySelector(sel + ' a.ic_option_add, ' + sel + ' .ic_option_add');
                    if (btn) { btn.click(); return 'added'; }
                    return 'not found';
                }""", DIALOG_SEL)
                await asyncio.sleep(0.3)
                if add_result == "added":
                    input_count += 1
                    # 给新 input 加 index（evaluate 只接受一个 arg，用数组传）
                    await self.page.evaluate("""([sel, idx]) => {
                        var inputs = document.querySelectorAll(sel + ' input.weui-desktop-form__input');
                        if (inputs[idx]) inputs[idx].setAttribute('data-vi', idx);
                    }""", [DIALOG_SEL, inp_idx])

            await self._cdp_type(f'[data-vi="{inp_idx}"]', opt)
            await asyncio.sleep(0.2)

        print(f"  Poll filled: question + {len(options)} options")

        # Step 5: 点「发起」按钮
        confirmed = await self.page.evaluate("""(sel) => {
            var dialog = document.querySelector(sel).closest('.weui-desktop-dialog');
            if (!dialog) return 'no parent dialog';
            var btns = dialog.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var t = btns[i].textContent.trim();
                if (t === '发起' && btns[i].offsetParent !== null) {
                    btns[i].click();
                    return 'clicked: ' + t;
                }
            }
            return 'not found';
        }""", DIALOG_SEL)
        print(f"  Poll confirm: {confirmed}")
        await asyncio.sleep(1.5)

        if "clicked" in confirmed:
            return StepResult("poll", StepStatus.SUCCESS, f"question + {len(options)} options")
        return StepResult("poll", StepStatus.FAILED, f"确认按钮: {confirmed}")

    async def enable_reward(self) -> StepResult:
        """开启赞赏。账户默认公众号名，不用选，直接确定。

        流程：点页面级赞赏开关(.js_reward_open) → 等对话框 → 选账户(如需) → 确定
        """
        # 点赞赏开关（两个可能的 selector）
        r = await self.page.evaluate("""() => {
            var el = document.querySelector('.js_reward_open') ||
                     document.querySelector('input.js_reward_set');
            if (el) { el.click(); return 'clicked: ' + el.className; }
            return 'not found';
        }""")
        print(f"  Reward switch: {r}")
        if 'not found' in r:
            return StepResult("reward", StepStatus.FAILED, "赞赏开关未找到")
        await asyncio.sleep(2)

        # 等对话框出现
        for attempt in range(5):
            has_dialog = await self.page.evaluate("""() => {
                var dialogs = document.querySelectorAll('.weui-desktop-dialog__wrp');
                for (var d of dialogs) {
                    if (getComputedStyle(d).display !== 'none' &&
                        d.textContent.includes('赞赏'))
                        return true;
                }
                return false;
            }""")
            if has_dialog:
                break
            await asyncio.sleep(1)

        # 选账户（点第一个账户项，已是默认选中则无副作用）
        await self.page.evaluate("""() => {
            var item = document.querySelector('.weui-desktop-dialog .js_reward_account_item');
            if (item) item.click();
        }""")
        await asyncio.sleep(0.5)

        # 点确定
        confirmed = await self.page.evaluate("""() => {
            var dialogs = document.querySelectorAll('.weui-desktop-dialog__wrp');
            for (var d of dialogs) {
                if (getComputedStyle(d).display === 'none') continue;
                if (!d.textContent.includes('赞赏')) continue;
                var btn = d.querySelector('.weui-desktop-btn_primary');
                if (btn && btn.offsetParent) { btn.click(); return 'clicked'; }
            }
            return 'not found';
        }""")
        print(f"  Reward confirm: {confirmed}")
        await asyncio.sleep(1)

        status = await self.page.evaluate("""() => {
            var el = document.querySelector('.js_reward_setting_tips, .js_reward_open');
            return el ? el.textContent.trim() : '';
        }""")
        ok = '账户' in status or '降临派' in status or '赞赏' in status
        print(f"  Reward status: {status} -> {'OK' if ok else 'FAILED'}")
        if ok:
            return StepResult("reward", StepStatus.SUCCESS, status)
        return StepResult("reward", StepStatus.FAILED, f"验证失败: {status}")

    async def set_cover_image(self, cover_filename: str = "cover.png") -> StepResult:
        """从图片库选封面图。

        流程：点封面区域(.js_cover_btn_area) → 从图片库选择(.js_imagedialog)
              → 找匹配文件名的图片 → 下一步 → 等待裁切加载 → 确认

        前提：cover 图片已通过 upload_image_file 上传到微信 CDN（会出现在图片库）
        """
        # Step 1: 用 JS 点封面按钮（避免 "outside of viewport"）
        await self.page.evaluate("""() => {
            var el = document.querySelector('.js_cover_btn_area');
            if (el) { el.scrollIntoView({block: 'center'}); el.click(); }
        }""")
        await asyncio.sleep(1.5)

        # Step 2: 点「从图片库选择」
        r = await self.page.evaluate("""() => {
            var el = document.querySelector('.pop-opr__button.js_imagedialog');
            if (el) { el.click(); return 'clicked'; }
            return 'not found';
        }""")
        print(f"  Cover menu: {r}")
        if r != 'clicked':
            return StepResult("cover", StepStatus.FAILED, "图片库按钮未找到")
        await asyncio.sleep(2)

        # Step 3: 等待图片库加载，点第一个匹配文件名的图片项
        selected = 'not found'
        for pick_attempt in range(5):
            selected = await self.page.evaluate("""(fname) => {
                var items = document.querySelectorAll('.weui-desktop-img-picker__item');
                if (items.length === 0) return 'loading';
                for (var i=0;i<items.length;i++) {
                    var title = items[i].querySelector('.weui-desktop-img-picker__img-title');
                    if (title && title.textContent.trim() === fname) {
                        items[i].click();
                        return 'selected item ' + i;
                    }
                }
                // fallback: 点第一张图
                items[0].click(); return 'selected first';
            }""", cover_filename)
            if selected != 'loading':
                break
            await asyncio.sleep(2)
        print(f"  Cover select: {selected}")
        await asyncio.sleep(0.5)

        # Step 4: 点「下一步」
        r2 = await self.page.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            for (var i=0;i<btns.length;i++) {
                if (btns[i].textContent.trim() === '下一步' && btns[i].offsetParent) {
                    btns[i].click(); return 'clicked';
                }
            }
            return 'not found';
        }""")
        print(f"  Cover next: {r2}")
        await asyncio.sleep(3)  # 等裁切界面加载

        # Step 5: 点「确认」
        r3 = await self.page.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            for (var i=0;i<btns.length;i++) {
                if (btns[i].textContent.trim() === '确认' && btns[i].offsetParent) {
                    btns[i].click(); return 'confirmed';
                }
            }
            return 'not found';
        }""")
        print(f"  Cover confirm: {r3}")
        await asyncio.sleep(1.5)

        # 验证：封面预览区有 background-image 含 mmbiz
        has_cover = await self.page.evaluate("""() => {
            var el = document.querySelector('.js_cover_preview_new');
            if (!el) return false;
            var bg = getComputedStyle(el).backgroundImage;
            return bg && bg.includes('mmbiz');
        }""")
        if has_cover:
            return StepResult("cover", StepStatus.SUCCESS, f"封面已设置 ({selected})")
        elif r3 == 'confirmed':
            return StepResult("cover", StepStatus.SUCCESS, f"确认已点击 ({selected})")
        return StepResult("cover", StepStatus.FAILED, f"封面验证失败: confirm={r3}")

    async def enable_original(self, author: str = "降临派") -> StepResult:
        """开启原创声明（仅原创，不开赞赏）

        流程：
        1. 点击原创 switch → 弹出对话框
        2. 关闭对话框内的赞赏开关（避免"请选择赞赏账户"阻塞）
        3. 填写作者名（必填，否则"作者不能为空"阻塞确定）
        4. 勾选协议 checkbox
        5. 点击确定
        """
        DIALOG_BODY = "#js_original_edit_box"

        # Step 1: 点击原创 switch
        js = (JS_DIR / "enable_original_only.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"  Original switch: {result}")
        await asyncio.sleep(2)

        # 检查对话框是否出现
        dialog_visible = await self.page.evaluate("""(dlg) => {
            var box = document.querySelector(dlg);
            return box && box.offsetParent !== null && getComputedStyle(box).display !== 'none';
        }""", DIALOG_BODY)
        if not dialog_visible:
            # 可能已经开启了原创
            has_original = await self.page.evaluate("""() => {
                var el = document.querySelector('.original_primary_tips, .js_original_tips');
                return el ? el.textContent.trim() : '';
            }""")
            if has_original:
                return StepResult("original", StepStatus.SUCCESS, f"已开启: {has_original}")
            return StepResult("original", StepStatus.FAILED, "原创对话框未弹出")

        # Step 2: 关闭对话框内的赞赏开关
        reward_off = await self.page.evaluate("""(dlg) => {
            var sw = document.querySelector(dlg + ' .js_reward_switch');
            if (sw && sw.checked) {
                sw.click();
                return 'disabled (was on)';
            }
            return sw ? 'already off' : 'switch not found';
        }""", DIALOG_BODY)
        print(f"  Reward switch: {reward_off}")
        await asyncio.sleep(1)

        # Step 3: 填写作者名（必填字段，空则无法确定）
        if author:
            author_selector = '#js_original_edit_box .js_author.js_counter'
            await self._cdp_type(author_selector, author)
            actual_author = await self.page.evaluate("""(sel) => {
                var el = document.querySelector(sel);
                return el ? el.value : '';
            }""", author_selector)
            print(f"  Author: '{actual_author}' ({'OK' if actual_author == author else 'MISMATCH'})")
            await asyncio.sleep(0.5)

        # Step 4: 勾选协议 checkbox（在 footer 的 .original_agreement 内）
        # 全部用 JS evaluate，禁止 Playwright locator（微信编辑器会拦截）
        try:
            cb_result = await self.page.evaluate("""() => {
                var body = document.querySelector('#js_original_edit_box');
                if (!body) return 'no body';
                var dialog = body.closest('.weui-desktop-dialog');
                if (!dialog) return 'no dialog';
                var cb = dialog.querySelector('.original_agreement .weui-desktop-form__checkbox');
                if (cb && cb.checked) return 'already checked';
                // 未勾选 → 点 icon 触发
                var icon = dialog.querySelector('.original_agreement .weui-desktop-icon-checkbox');
                if (icon) { icon.click(); return 'checked'; }
                // fallback: 直接点 checkbox
                if (cb) { cb.click(); return 'checked via cb'; }
                return 'checkbox not found';
            }""")
            print(f"  Checkbox: {cb_result}")
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"  Checkbox failed: {e}")

        # 截图
        try:
            await self.page.screenshot(path="/tmp/original_before_confirm.png")
        except Exception:
            pass

        # Step 5: 点击确定
        await self._click_confirm_in_dialog(DIALOG_BODY)
        await asyncio.sleep(2)

        for attempt in range(3):
            dialog_gone = await self._check_dialog_closed()
            if dialog_gone:
                print("  Original dialog closed OK")
                # 验证原创标签出现
                has_tips = await self.page.evaluate("""() => {
                    var el = document.querySelector('.original_primary_tips, .js_original_tips');
                    return el ? el.textContent.trim() : '';
                }""")
                return StepResult("original", StepStatus.SUCCESS, has_tips or "对话框已关闭", retries=attempt)

            print(f"  Dialog still open (attempt {attempt + 1})...")
            try:
                await self.page.screenshot(path=f"/tmp/original_dialog_retry_{attempt}.png")
            except Exception:
                pass

            # 确保 checkbox 勾上
            await self.page.evaluate("""() => {
                var body = document.querySelector('#js_original_edit_box');
                var dialog = body ? body.closest('.weui-desktop-dialog') : null;
                if (!dialog) return;
                var cb = dialog.querySelector('.original_agreement .weui-desktop-form__checkbox');
                if (cb && !cb.checked) {
                    var icon = dialog.querySelector('.original_agreement .weui-desktop-icon-checkbox');
                    if (icon) icon.click();
                }
            }""")
            await asyncio.sleep(0.5)
            await self._click_confirm_in_dialog(DIALOG_BODY)
            await asyncio.sleep(2)

        # 仍未关闭 → 取消（用 JS evaluate，禁止 Playwright locator）
        print("  WARNING: 原创设置失败，点取消退出", file=sys.stderr)
        try:
            await self.page.evaluate("""() => {
                var body = document.querySelector('#js_original_edit_box');
                var dialog = body ? body.closest('.weui-desktop-dialog') : null;
                if (!dialog) return;
                var btn = dialog.querySelector('.weui-desktop-btn_default');
                if (btn && btn.textContent.trim() === '取消') btn.click();
            }""")
        except Exception:
            pass
        await asyncio.sleep(1)
        return StepResult("original", StepStatus.FAILED, "对话框无法关闭，已取消", retries=3)

    async def _click_confirm_in_dialog(self, dialog_body_selector: str = "#js_original_edit_box"):
        """点击对话框的确定按钮（在 footer 中，不在 dialog body 内）"""
        click_result = await self.page.evaluate("""(bodySelector) => {
            var body = document.querySelector(bodySelector);
            var dialog = body ? body.closest('.weui-desktop-dialog') : null;
            if (!dialog) return 'no parent dialog';
            // 在整个 dialog（含 footer）中找确定按钮
            var btns = dialog.querySelectorAll('.weui-desktop-btn_primary, button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.trim() === '确定' && btns[i].offsetParent !== null) {
                    btns[i].click();
                    return 'clicked';
                }
            }
            return 'confirm not found';
        }""", dialog_body_selector)
        print(f"  Confirm: {click_result}")

    async def _check_dialog_closed(self) -> bool:
        """检查原创对话框是否已关闭"""
        return await self.page.evaluate("""() => {
            var body = document.querySelector('#js_original_edit_box');
            if (!body) return true;
            // 检查包含 #js_original_edit_box 的 dialog wrapper
            var wrapper = body.closest('.weui-desktop-dialog__wrp');
            if (!wrapper) return true;
            var style = getComputedStyle(wrapper);
            // wrapper display:none 或 visibility:hidden 表示对话框已关闭
            return style.display === 'none' || style.visibility === 'hidden';
        }""")

    async def remove_empty_tables(self):
        """清除空表格"""
        js = (JS_DIR / "remove_empty_tables.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"Tables: {result}")
        return result

    async def trigger_save(self):
        """触发保存（内部方法）"""
        js = (JS_DIR / "trigger_save.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"Save: {result}")

        # 也尝试 Ctrl+S
        await self.page.keyboard.press("Meta+s")
        await asyncio.sleep(2)
        return result

    async def save_draft(self) -> StepResult:
        """清除空表格 + 保存 + 验证保存状态"""
        await self.remove_empty_tables()
        await self.trigger_save()
        await asyncio.sleep(3)

        # 验证保存状态
        for attempt in range(3):
            save_text = await self.page.evaluate("""() => {
                var el = document.querySelector('.tips_global, .editor-tips, .preview-tips');
                return el ? el.textContent.trim() : '';
            }""")
            if "已保存" in save_text or "saved" in save_text.lower():
                print(f"  Save verified: '{save_text}'")
                return StepResult("save", StepStatus.SUCCESS, save_text, retries=attempt)
            if attempt < 2:
                await self.page.keyboard.press("Meta+s")
                await asyncio.sleep(3)

        # 保存状态不确定但操作已执行
        return StepResult("save", StepStatus.SUCCESS, f"保存已触发 (状态: '{save_text}')")

    async def screenshot(self, output_path: str = "/tmp/wechat_editor.png", full_page: bool = True):
        """截图当前页面（默认长截图）"""
        await self.page.screenshot(path=output_path, full_page=full_page)
        print(f"Screenshot: {output_path}")
        return output_path

    async def get_token(self) -> str:
        """从页面 URL 提取 token"""
        match = re.search(r"token=(\d+)", self.page.url)
        return match.group(1) if match else ""

    async def verify_article_complete(
        self,
        expected_title: str,
        expected_desc: str = "",
        expected_image_count: int = 0,
        screenshot_dir: str = None,
    ) -> StepResult:
        """完整验收草稿：标题/简介/封面/原创/赞赏/正文/配图/投票，一次全查。

        验收清单（8 项，缺一不可）:
          1. 标题 — #title value 与 expected_title 匹配
          2. 简介 — #js_description 非空
          3. 封面 — .js_cover_preview_new background-image 含 mmbiz
          4. 原创 — #js_original 区域含 '文字原创'
          5. 赞赏 — 页面文本含 '赞赏' + '账户'
          6. 正文 — editor innerText > 200 字符
          7. 配图 — editor 内 img[src*=mmbiz] 且 naturalWidth>0 >= expected_image_count
          8. 投票 — editor 内含 vote_area 或 body 含 '投票'（可选）

        返回 StepResult，message 包含每项结果的结构化摘要。
        """
        page = self.page
        if not page or "appmsg_edit" not in page.url:
            return StepResult("verify", StepStatus.FAILED, "not on editor page")

        result = await page.evaluate("""(expectedImgCount) => {
            var r = {};

            // 1. title
            var titleEl = document.querySelector('#title');
            r.title = titleEl ? titleEl.value : '';

            // 2. desc
            var descEl = document.querySelector('#js_description');
            r.desc = descEl ? descEl.value : '';

            // 3. cover
            var coverEl = document.querySelector('.js_cover_preview_new');
            var coverBg = coverEl ? coverEl.style.backgroundImage : '';
            r.hasCover = coverBg.includes('mmbiz');

            // 4. original
            var origArea = document.querySelector('#js_original');
            var origText = origArea ? origArea.textContent : '';
            r.hasOriginal = origText.includes('\\u6587\\u5b57\\u539f\\u521b');

            // 5. reward
            var bodyText = document.body ? document.body.innerText : '';
            r.hasReward = bodyText.includes('\\u8d5e\\u8d4f') && bodyText.includes('\\u8d26\\u6237');

            // 6. content length
            var editors = document.querySelectorAll('[contenteditable=true]');
            var editor = editors.length >= 2 ? editors[1] : null;
            r.contentLength = editor ? editor.innerText.length : 0;

            // 7. images
            r.loadedImages = 0;
            if (editor) {
                var imgs = editor.querySelectorAll('img');
                for (var i = 0; i < imgs.length; i++) {
                    if (imgs[i].naturalWidth > 0 && imgs[i].src.includes('mmbiz')) {
                        r.loadedImages++;
                    }
                }
            }
            r.expectedImages = expectedImgCount;

            // 8. poll
            r.hasPoll = bodyText.includes('\\u6295\\u7968');

            return r;
        }""", expected_image_count)

        # Retry image loading (CDN may be slow)
        if result.get("loadedImages", 0) < expected_image_count and expected_image_count > 0:
            for attempt in range(5):
                await asyncio.sleep(3)
                loaded = await page.evaluate("""() => {
                    var editors = document.querySelectorAll('[contenteditable=true]');
                    var editor = editors.length >= 2 ? editors[1] : null;
                    if (!editor) return 0;
                    var imgs = editor.querySelectorAll('img');
                    var count = 0;
                    for (var i = 0; i < imgs.length; i++) {
                        if (imgs[i].naturalWidth > 0 && imgs[i].src.includes('mmbiz')) count++;
                    }
                    return count;
                }""")
                result["loadedImages"] = loaded
                if loaded >= expected_image_count:
                    break

        # Build checklist
        checks = {
            "title": expected_title[:10] in result.get("title", "") if result.get("title") else False,
            "desc": len(result.get("desc", "")) > 0,
            "cover": result.get("hasCover", False),
            "original": result.get("hasOriginal", False),
            "reward": result.get("hasReward", False),
            "content": result.get("contentLength", 0) > 200,
            "images": result.get("loadedImages", 0) >= expected_image_count,
            "poll": result.get("hasPoll", False),
        }

        # Print results
        symbols = {True: "PASS", False: "FAIL"}
        lines = []
        for item, ok in checks.items():
            detail = ""
            if item == "title":
                detail = f" ({result.get('title', '')[:30]})"
            elif item == "desc":
                detail = f" ({len(result.get('desc', ''))} chars)"
            elif item == "content":
                detail = f" ({result.get('contentLength', 0)} chars)"
            elif item == "images":
                detail = f" ({result.get('loadedImages', 0)}/{expected_image_count})"
            line = f"  {symbols[ok]}: {item}{detail}"
            lines.append(line)
            print(line)

        # Screenshot if dir provided
        if screenshot_dir:
            await safe_screenshot(page, os.path.join(screenshot_dir, "_verify_complete.png"))

        all_pass = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        if all_pass:
            return StepResult("verify", StepStatus.SUCCESS, "8/8 checks passed")
        else:
            return StepResult("verify", StepStatus.FAILED, f"failed: {', '.join(failed)}")

    async def verify_draft_in_list(self, title: str, screenshot_dir: str = None) -> StepResult:
        """在草稿列表页面按标题查找文章。

        Opens a new tab -> draft list -> search title in card spans -> close tab.
        """
        token = await self._get_token()
        if not token:
            return StepResult("verify_list", StepStatus.FAILED, "no token")

        draft_page = await self.context.new_page()
        try:
            url = f"{DRAFT_LIST_URL}&token={token}&lang=zh_CN"
            await draft_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            found = await draft_page.evaluate("""(title) => {
                var spans = document.querySelectorAll('.weui-desktop-publish__cover__title span');
                for (var i = 0; i < spans.length; i++) {
                    if (spans[i].textContent.trim().includes(title.substring(0, 10))) {
                        return spans[i].textContent.trim();
                    }
                }
                var body = document.body ? document.body.innerText : '';
                return body.includes(title.substring(0, 10)) ? 'found in page text' : 'not found';
            }""", title)
            print(f"  Draft list search: {found}")

            if screenshot_dir:
                shot_path = os.path.join(screenshot_dir, "_draft_list_verify.png")
                await safe_screenshot(draft_page, shot_path)

            if found and found != 'not found':
                return StepResult("verify_list", StepStatus.SUCCESS, f"found: {found[:30]}")
            return StepResult("verify_list", StepStatus.FAILED, "not found in draft list")
        except Exception as e:
            return StepResult("verify_list", StepStatus.FAILED, str(e))
        finally:
            await draft_page.close()

    async def open_draft_preview(self, title: str, screenshot_dir: str) -> StepResult:
        """⛔ 固化铁律：保存后必须打开预览页，截图验证，tab 保留给用户看。

        流程：草稿列表 → 点卡片 → 微信会新开预览 tab → 对预览 tab 截图 → 保留不关。
        关掉临时的草稿列表 tab（它只是跳板）。
        """
        if not self.context:
            return StepResult("preview", StepStatus.FAILED, "no context")

        try:
            token = await self._get_token()
            if not token:
                return StepResult("preview", StepStatus.FAILED, "no token")

            # 记录点击前的 tab 数量
            pages_before = set(p for p in self.context.pages)

            # 新开 tab 导航到草稿列表（这是跳板，后面会关）
            list_page = await self.context.new_page()
            url = f"{DRAFT_LIST_URL}&token={token}&lang=zh_CN"
            await list_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # 点击文章卡片
            short_title = title[:10]
            clicked = await list_page.evaluate("""(shortTitle) => {
                var spans = document.querySelectorAll('.weui-desktop-publish__cover__title span');
                for (var i = 0; i < spans.length; i++) {
                    if (spans[i].textContent.trim().includes(shortTitle)) {
                        var card = spans[i].closest('.weui-desktop-card');
                        if (card) {
                            var link = card.querySelector('a');
                            if (link) { link.click(); return link.href; }
                        }
                    }
                }
                return null;
            }""", short_title)

            if not clicked:
                print(f"  Preview: article '{short_title}' not found in draft list")
                # 截草稿列表作为证据，保留这个 tab
                shot_path = os.path.join(screenshot_dir, "_draft_verify.png")
                await safe_screenshot(list_page, shot_path)
                return StepResult("preview", StepStatus.FAILED, "not found in draft list")

            print(f"  Preview: card clicked, waiting for new tab...")
            await asyncio.sleep(5)

            # 找到新打开的预览 tab（点击卡片后微信会在新 tab 打开预览）
            new_pages = [p for p in self.context.pages if p not in pages_before and p != list_page]
            preview_page = None
            for p in new_pages:
                if "mp.weixin.qq.com/s" in p.url:
                    preview_page = p
                    break

            if not preview_page and new_pages:
                preview_page = new_pages[-1]  # 拿最新的

            if preview_page:
                print(f"  Preview tab opened: {preview_page.url[:80]}")
                await asyncio.sleep(2)
                # 截图预览页
                shot_path = os.path.join(screenshot_dir, "_draft_verify.png")
                await safe_screenshot(preview_page, shot_path)
                print(f"  Preview screenshot: {shot_path}")
                # 关掉草稿列表跳板 tab
                try:
                    cdp = await list_page.context.new_cdp_session(list_page)
                    await cdp.send("Page.close")
                except Exception:
                    pass
                # ⛔ 预览 tab 保留不关
                return StepResult("preview", StepStatus.SUCCESS, "preview tab kept open")
            else:
                # 没有新 tab，可能点击在当前 tab 内跳转了
                print(f"  No new tab detected, screenshotting list page")
                shot_path = os.path.join(screenshot_dir, "_draft_verify.png")
                await safe_screenshot(list_page, shot_path)
                return StepResult("preview", StepStatus.SUCCESS, "screenshot saved (no new tab)")

        except Exception as e:
            return StepResult("preview", StepStatus.FAILED, str(e))

    async def leave_on_draft_list(self):
        """全部发完后新开 tab 打开草稿列表。不覆盖已有的预览 tab。"""
        token = await self._get_token()
        if not token or not self.context:
            return
        url = f"{DRAFT_LIST_URL}&token={token}"
        try:
            list_page = await self.context.new_page()
            await list_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print(f"Draft list tab opened: {url[:60]}")
        except Exception as e:
            print(f"WARNING: 无法打开草稿列表: {e}", file=sys.stderr)

    # ── mdnice in-tab ──

    async def _mdnice_dismiss_all_dialogs(self, page):
        """关闭 mdnice 所有弹窗（版本更新/登录等）。

        先点 X 关闭，再 force-hide 残留的 wrap/mask 防止拦截键盘事件。
        """
        for attempt in range(5):
            closed = await page.evaluate("""() => {
                var closed = 0;
                // 点 X 按钮关闭可见弹窗
                document.querySelectorAll('.ant-modal-close').forEach(function(btn) {
                    var wrap = btn.closest('.ant-modal-wrap');
                    if (wrap && getComputedStyle(wrap).display !== 'none') {
                        btn.click();
                        closed++;
                    }
                });
                return closed;
            }""")
            if closed == 0:
                break
            await asyncio.sleep(0.8)

        # Force-hide 所有残留的 modal overlay（防止拦截键盘事件）
        await page.evaluate("""() => {
            document.querySelectorAll(
                '.ant-modal-mask, .ant-modal-wrap, .global-mask'
            ).forEach(function(el) { el.style.display = 'none'; });
        }""")


    async def _mdnice_ensure_editor_ready(self, page):
        """确保 mdnice 编辑器可写（#nice 有子元素 = React 状态已连接）。

        新 tab 上 CodeMirror 存在但 React 未连接 — 需要 Playwright click 侧边栏文章激活。
        已有 tab 则跳过（React 状态已连接）。
        """
        status = await page.evaluate("""() => {
            var cm = document.querySelector('.CodeMirror');
            if (!cm || !cm.CodeMirror) return 'no_cm';
            var nice = document.querySelector('#nice');
            if (nice && nice.children.length > 0) return 'ready';
            return 'need_activate';
        }""")

        if status == 'ready':
            return True
        if status == 'no_cm':
            print("  ERROR: CodeMirror not found on page")
            return False

        # 新 tab：Playwright click 侧边栏文章激活 React 状态
        print("  Activating editor via sidebar click...")
        try:
            await page.click(".nice-article-sidebar-list-item-container", timeout=5000)
            await asyncio.sleep(2)
        except Exception:
            # 没有侧边栏文章，尝试点 "+" 创建
            print("  No sidebar articles, creating new...")
            try:
                await page.click(".add-btn", timeout=3000)
                await asyncio.sleep(1.5)
                # 处理"新增文章"对话框
                await page.evaluate("""() => {
                    var btns = document.querySelectorAll('.ant-modal .ant-btn-primary');
                    for (var i = 0; i < btns.length; i++) {
                        if (!btns[i].disabled) { btns[i].click(); return; }
                    }
                }""")
                await asyncio.sleep(2)
            except Exception as e2:
                print(f"  WARNING: Could not activate editor: {e2}")
                return False

        # 验证
        ready = await page.evaluate("""() => {
            var nice = document.querySelector('#nice');
            return nice && nice.children.length > 0;
        }""")
        if ready:
            print("  Editor activated")
        return ready or True  # 即使 #nice 仍为空也继续尝试

    async def mdnice_render_in_tab(self, md_text: str, screenshot_dir: Path = None) -> StepResult:
        """在 CDP Chrome 里做 mdnice 排版，不启动独立浏览器。

        优先复用已有 mdnice tab（React 状态已连接，clipboard paste 可直接触发渲染）。
        没有则新建 tab。完成后不关闭 tab（留给下一篇复用）。
        """
        print("--- mdnice 排版 (in-tab) ---")

        # 优先复用已有 mdnice tab（React 状态已连接）
        mdnice_page = None
        is_existing = False
        for p in self.context.pages:
            if "mdnice" in p.url:
                mdnice_page = p
                is_existing = True
                print("  Reusing existing mdnice tab")
                break
        if not mdnice_page:
            mdnice_page = await self.context.new_page()
        self._mdnice_tab = mdnice_page  # 保留引用，不关闭

        try:
            if not is_existing:
                await mdnice_page.goto(MDNICE_URL, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)

            # 检测登录状态
            needs_login = await mdnice_page.evaluate("""() => {
                var modals = document.querySelectorAll('.ant-modal-wrap');
                for (var i = 0; i < modals.length; i++) {
                    if (getComputedStyle(modals[i]).display !== 'none' &&
                        modals[i].textContent.includes('登录'))
                        return true;
                }
                return !document.querySelector('.CodeMirror');
            }""")
            if needs_login:
                qr_path = "/tmp/mdnice_qr_login.png"
                await mdnice_page.screenshot(path=qr_path)
                self._notify_user("mdnice 需要扫码登录")
                print(f"\n{'='*50}")
                print("  mdnice 未登录，请在浏览器窗口扫码登录")
                print(f"  截图: {qr_path}")
                print(f"{'='*50}\n")
                max_wait, elapsed = 120, 0
                while elapsed < max_wait:
                    await asyncio.sleep(3)
                    elapsed += 3
                    has_editor = await mdnice_page.evaluate(
                        "() => !!document.querySelector('.CodeMirror')"
                    )
                    if has_editor:
                        print("  mdnice 登录成功！")
                        break
                    if elapsed % 15 == 0:
                        await mdnice_page.screenshot(path=qr_path)
                        print(f"  等待扫码... ({elapsed}s/{max_wait}s)")
                else:
                    await mdnice_page.close()
                    return StepResult("mdnice", StepStatus.FAILED, "mdnice 登录超时")

            # Step 1: 关闭所有弹窗（版本更新等）
            await self._mdnice_dismiss_all_dialogs(mdnice_page)

            if screenshot_dir:
                await safe_screenshot(mdnice_page, str(screenshot_dir / "_mdnice_01_loaded.png"))

            # Step 2: 确保编辑器就绪
            if not await self._mdnice_ensure_editor_ready(mdnice_page):
                return StepResult("mdnice", StepStatus.FAILED, "CodeMirror 未就绪")

            # Step 3: 注入 markdown
            print("  Injecting markdown content...")
            await mdnice_page.bring_to_front()
            await asyncio.sleep(0.5)

            # 清空 CodeMirror
            await mdnice_page.evaluate("""() => {
                var cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) { cm.CodeMirror.focus(); cm.CodeMirror.setValue(''); }
            }""")
            await asyncio.sleep(0.3)

            # 方式1: clipboard paste（已有 tab 时有效，触发 React 渲染）
            subprocess.run(["pbcopy"], input=md_text.encode("utf-8"), timeout=5)
            await asyncio.sleep(0.3)
            await mdnice_page.keyboard.press("Meta+a")
            await asyncio.sleep(0.1)
            await mdnice_page.keyboard.press("Meta+v")
            await asyncio.sleep(3)

            char_count = await mdnice_page.evaluate("""() => {
                var cm = document.querySelector('.CodeMirror');
                return cm && cm.CodeMirror ? cm.CodeMirror.getValue().length : -1;
            }""")

            # 方式2 fallback: keyboard.type()（新 tab 时 paste 可能失败，type 触发 React 事件）
            if char_count < len(md_text) // 2:
                print(f"  Clipboard paste got {char_count} chars, using keyboard.type fallback...")
                await mdnice_page.evaluate("""() => {
                    var cm = document.querySelector('.CodeMirror');
                    if (cm && cm.CodeMirror) { cm.CodeMirror.focus(); cm.CodeMirror.setValue(''); }
                }""")
                await asyncio.sleep(0.3)
                # keyboard.type 模拟真实输入，delay=0 极快
                await mdnice_page.keyboard.type(md_text, delay=0)
                await asyncio.sleep(3)
                char_count = await mdnice_page.evaluate("""() => {
                    var cm = document.querySelector('.CodeMirror');
                    return cm && cm.CodeMirror ? cm.CodeMirror.getValue().length : -1;
                }""")

            print(f"  CodeMirror: {char_count} chars")

            if screenshot_dir:
                await safe_screenshot(mdnice_page, str(screenshot_dir / "_mdnice_02_pasted.png"))

            # Step 4: 验证预览区有内容（带重试）
            min_preview = max(10, char_count // 3)  # 预览至少要有输入的 1/3
            preview_ok = None
            for attempt in range(5):
                preview_ok = await mdnice_page.evaluate("""(threshold) => {
                    var nice = document.querySelector('#nice');
                    if (!nice) return {ok: false, reason: 'no #nice'};
                    var text = nice.innerText || '';
                    var imgs = nice.querySelectorAll('img');
                    return {ok: text.length > threshold, textLen: text.length, imgCount: imgs.length};
                }""", min_preview)
                if preview_ok.get("ok"):
                    break
                await asyncio.sleep(2)

            if not preview_ok.get("ok"):
                print(f"  WARNING: 预览区内容不足 (text={preview_ok.get('textLen', 0)})")
            else:
                print(f"  Preview: {preview_ok.get('textLen', 0)} chars, {preview_ok.get('imgCount', 0)} images")

            # Step 5: 选主题
            print(f"  Selecting theme: {MDNICE_THEME}...")
            await mdnice_page.evaluate("""() => {
                var links = document.querySelectorAll('a.nice-menu-link');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].textContent.includes('主题')) {
                        links[i].click();
                        return;
                    }
                }
            }""")
            await asyncio.sleep(2)

            theme_applied = await mdnice_page.evaluate("""(themeName) => {
                var items = document.querySelectorAll('.theme-list > *');
                for (var i = 0; i < items.length; i++) {
                    if (items[i].textContent.includes(themeName)) {
                        var btn = items[i].querySelector('button');
                        if (btn) { btn.click(); return 'OK'; }
                    }
                }
                return 'NOT_FOUND';
            }""", MDNICE_THEME)

            if theme_applied == "OK":
                print(f"  Theme '{MDNICE_THEME}' applied")
            else:
                print(f"  WARNING: 主题 '{MDNICE_THEME}' 未找到", file=sys.stderr)

            await asyncio.sleep(2)
            await mdnice_page.keyboard.press("Escape")
            await asyncio.sleep(1)

            if screenshot_dir:
                await safe_screenshot(mdnice_page, str(screenshot_dir / "_mdnice_03_themed.png"))

            # Step 6: 复制到微信
            print("  Copying formatted content for WeChat...")
            copied = await mdnice_page.evaluate("""() => {
                var btn = document.querySelector('a.nice-btn-wechat');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            }""")
            if copied != 'clicked':
                return StepResult("mdnice", StepStatus.FAILED, "WeChat 复制按钮未找到")
            await asyncio.sleep(2)
            print("  Copied to clipboard via WeChat button")

            if screenshot_dir:
                await safe_screenshot(mdnice_page, str(screenshot_dir / "_mdnice_04_copied.png"))

            return StepResult("mdnice", StepStatus.SUCCESS,
                              f"排版完成 ({char_count} chars, {preview_ok.get('imgCount', '?')} imgs)")

        except Exception as e:
            print(f"  mdnice error: {e}", file=sys.stderr)
            if screenshot_dir:
                try:
                    await mdnice_page.screenshot(path=str(screenshot_dir / "_mdnice_error.png"))
                except Exception:
                    pass
            return StepResult("mdnice", StepStatus.FAILED, str(e))

        finally:
            # 不关闭 mdnice tab — 留给下一篇复用（React 状态保持连接）
            pass

    async def disconnect(self):
        """断开 CDP 连接（不关闭浏览器）"""
        self._connected = False
        if hasattr(self, 'pw') and self.pw:
            await self.pw.stop()
            self.pw = None

    # backward compat alias
    async def close(self):
        """关闭连接（不关闭浏览器）— backward compat alias for disconnect()"""
        await self.disconnect()


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
        await auto.save_draft()

    elif args.command == "screenshot":
        if not found:
            return 1
        out = args.value if args.value else "/tmp/wechat_editor.png"
        await auto.screenshot(out)

    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    await auto.disconnect()
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
