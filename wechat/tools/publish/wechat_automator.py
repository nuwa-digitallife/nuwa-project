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
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

# 确保 Playwright CDP 连接不走代理（ClashX 等会拦截 localhost）
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

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

        self.pw = await async_playwright().start()
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

    async def find_or_create_mp_page(self):
        """确保有一个 MP 页面可用（用于 API 调用如图片上传）。

        如果没有任何 tab，创建新 tab 并导航到 MP 首页。
        如果有 tab 但不在 MP 域名，导航到 MP 首页。
        返回 True 表示 self.page 已设置到可用的 MP 页面。
        """
        # 先试已有页面
        for page in self.context.pages:
            if EDITOR_URL_PATTERN in page.url and "token=" in page.url:
                self.page = page
                print(f"Using MP page: {page.url[:80]}")
                return True

        # 没有带 token 的 MP 页面，尝试导航
        if self.context.pages:
            page = self.context.pages[0]
        else:
            page = await self.context.new_page()

        print("Navigating to MP home...")
        await page.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # 检查是否登录（URL 应包含 token）
        if "token=" in page.url:
            self.page = page
            print(f"MP page ready: {page.url[:80]}")
            return True

        # 未登录，截图二维码页面并等待扫码
        qr_screenshot = "/tmp/wechat_qr_login.png"
        await page.screenshot(path=qr_screenshot)
        print(f"\n{'='*50}")
        print("⏳ 未检测到登录状态，请在手机上扫码登录微信公众平台")
        print(f"   二维码截图已保存: {qr_screenshot}")
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
                print(f"✅ 登录成功！MP page ready: {page.url[:80]}")
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
        """导航到新建图文页面"""
        # 从已登录页面提取 token（每个请求都需要）
        token = await self._get_token()
        if not token:
            print("ERROR: 未找到 token，可能未登录", file=sys.stderr)
            return False

        url = f"{NEW_POST_URL}&token={token}"

        if not self.page:
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

    async def _cdp_type(self, selector: str, text: str):
        """用 CDP Input.dispatchKeyEvent 逐字输入。

        这是唯一能触发微信编辑器 Vue v-model 的方式。
        Playwright 的 fill()/keyboard.type()/press_sequentially() 全部无效。
        """
        locator = self.page.locator(selector)
        await locator.click()
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

    async def set_title(self, title: str):
        """设置文章标题（CDP 逐字输入，触发 Vue v-model）"""
        await self._cdp_type("#title", title)
        # 验证
        actual = await self.page.evaluate('() => document.querySelector("#title").value')
        ok = actual == title
        print(f"Title set: {'OK' if ok else 'MISMATCH'} ('{actual[:30]}')")
        return ok

    async def set_description(self, desc: str):
        """设置文章简介（CDP 逐字输入，触发 Vue v-model）"""
        await self._cdp_type("#js_description", desc)
        actual = await self.page.evaluate('() => document.querySelector("#js_description").value')
        ok = actual == desc
        print(f"Description set: {'OK' if ok else 'MISMATCH'} ('{actual[:30]}')")
        return ok

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

    async def add_poll(self, question: str, options: list) -> bool:
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
            print("  ERROR: #js_editor_insertvote 未找到，跳过")
            return False

        await asyncio.sleep(1.5)

        # 检查对话框是否出现
        dialog_visible = await self.page.evaluate("""(sel) => {
            var d = document.querySelector(sel);
            return d && d.offsetParent !== null;
        }""", DIALOG_SEL)
        if not dialog_visible:
            print("  ERROR: 投票对话框未弹出，跳过")
            return False
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
        return "clicked" in confirmed

    async def enable_reward(self) -> bool:
        """开启赞赏（账户：降临派手记）。

        流程：点页面级赞赏开关(.js_reward_open) → 对话框预填账户 → 点确定
        账户输入框已预填"降临派手记"，协议已勾选，直接点确定即可。
        """
        r = await self.page.evaluate("""() => {
            var el = document.querySelector('.js_reward_open');
            if (el) { el.click(); return el.textContent.trim(); }
            return 'not found';
        }""")
        print(f"  Reward switch: {r}")
        if r == 'not found':
            return False
        await asyncio.sleep(1.5)

        # 确认账户（点「最近使用」链接确保选中）
        await self.page.evaluate("""() => {
            var links = document.querySelectorAll('.weui-desktop-dialog a');
            for (var i=0;i<links.length;i++) {
                if (links[i].textContent.trim() === '降临派手记' && links[i].offsetParent) {
                    links[i].click(); return;
                }
            }
        }""")
        await asyncio.sleep(0.5)

        # 点确定
        confirmed = await self.page.evaluate("""() => {
            var btns = document.querySelectorAll('.weui-desktop-dialog button');
            for (var i=0;i<btns.length;i++) {
                if (btns[i].textContent.trim() === '确定' && btns[i].offsetParent) {
                    btns[i].click(); return 'clicked';
                }
            }
            return 'not found';
        }""")
        print(f"  Reward confirm: {confirmed}")
        await asyncio.sleep(1)

        status = await self.page.evaluate("""() => {
            var el = document.querySelector('.js_reward_setting_tips, .js_reward_open');
            return el ? el.textContent.trim() : '';
        }""")
        ok = '账户' in status or '降临派手记' in status
        print(f"  Reward status: {status} → {'OK' if ok else 'FAILED'}")
        return ok

    async def set_cover_image(self, cover_filename: str = "cover.png") -> bool:
        """从图片库选封面图。

        流程：点封面区域(.js_cover_btn_area) → 从图片库选择(.js_imagedialog)
              → 找匹配文件名的图片 → 下一步 → 等待裁切加载 → 确认

        前提：cover 图片已通过 upload_image_file 上传到微信 CDN（会出现在图片库）
        """
        # Step 1: 点封面按钮（用 Playwright click，确保事件传播）
        await self.page.click('.js_cover_btn_area', force=True)
        await asyncio.sleep(1.5)

        # Step 2: 点「从图片库选择」
        r = await self.page.evaluate("""() => {
            var el = document.querySelector('.pop-opr__button.js_imagedialog');
            if (el) { el.click(); return 'clicked'; }
            return 'not found';
        }""")
        print(f"  Cover menu: {r}")
        if r != 'clicked':
            return False
        await asyncio.sleep(2)

        # Step 3: 点第一个匹配文件名的图片项
        selected = await self.page.evaluate("""(fname) => {
            var items = document.querySelectorAll('.weui-desktop-img-picker__item');
            for (var i=0;i<items.length;i++) {
                var title = items[i].querySelector('.weui-desktop-img-picker__img-title');
                if (title && title.textContent.trim() === fname) {
                    items[i].click();
                    return 'selected item ' + i;
                }
            }
            // fallback: 点第一张图
            if (items.length > 0) { items[0].click(); return 'selected first'; }
            return 'not found';
        }""", cover_filename)
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
        return r3 == 'confirmed'

    async def enable_original(self, author: str = "降临派手记"):
        """开启原创声明（仅原创，不开赞赏）

        已验证工作流程：
        1. 点击原创 switch → 弹出对话框
        2. 关闭对话框内的赞赏开关（避免"请选择赞赏账户"阻塞）
        3. 用 CDP Input.dispatchKeyEvent 填作者（唯一能触发 Vue v-model 的方式）
        4. 点击 .weui-desktop-icon-checkbox 勾选协议（在 dialog footer，不在 body 内）
        5. 点击确定

        DOM 结构要点：
        - #js_original_edit_box = dialog body（作者、赞赏 switch 在这里）
        - .weui-desktop-dialog__ft = dialog footer（checkbox、确定/取消按钮在这里）
        - 两个 author input 在页面上，必须用 #js_original_edit_box 限定
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
            print("  WARNING: 原创对话框未弹出")
            return result

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

        # Step 3: 用 CDP 填写作者（keyboard.type/fill 都无法触发 Vue v-model）
        dialog_author_selector = f'{DIALOG_BODY} input[placeholder*="作者"]'
        # 先清空
        await self.page.evaluate("""(sel) => {
            var inp = document.querySelector(sel);
            if (!inp) return;
            var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setter.call(inp, '');
            inp.dispatchEvent(new Event('input', {bubbles: true}));
        }""", dialog_author_selector)
        await asyncio.sleep(0.3)

        # 点击 input 获取焦点
        try:
            await self.page.locator(dialog_author_selector).click(timeout=3000)
        except Exception:
            await self.page.locator(dialog_author_selector).click(force=True, timeout=3000)
        await asyncio.sleep(0.3)

        # CDP dispatchKeyEvent 逐字输入
        cdp = await self.context.new_cdp_session(self.page)
        for char in author:
            await cdp.send('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': char})
            await cdp.send('Input.dispatchKeyEvent', {'type': 'char', 'text': char})
            await cdp.send('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': char})
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.5)

        # 验证
        val = await self.page.evaluate("""(sel) => {
            var inp = document.querySelector(sel);
            return inp ? inp.value : '';
        }""", dialog_author_selector)
        print(f"  Author (CDP): '{val}' {'OK' if val == author else 'MISMATCH'}")
        await cdp.detach()

        # Step 4: 勾选协议 checkbox（在 footer 的 .original_agreement 内）
        icon_locator = self.page.locator(
            '.weui-desktop-dialog:has(#js_original_edit_box) .original_agreement .weui-desktop-icon-checkbox'
        )
        try:
            is_checked = await self.page.evaluate("""() => {
                var body = document.querySelector('#js_original_edit_box');
                var dialog = body.closest('.weui-desktop-dialog');
                var cb = dialog.querySelector('.original_agreement .weui-desktop-form__checkbox');
                return cb ? cb.checked : false;
            }""")
            if not is_checked and await icon_locator.count() > 0:
                await icon_locator.click(timeout=3000)
                await asyncio.sleep(0.3)
            print(f"  Checkbox: {'already checked' if is_checked else 'checked'}")
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
                return result

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

        # 仍未关闭 → 取消
        print("  WARNING: 原创设置失败，点取消退出", file=sys.stderr)
        try:
            cancel = self.page.locator('.weui-desktop-dialog:has(#js_original_edit_box) .weui-desktop-btn_default')
            if await cancel.count() > 0:
                await cancel.first.click(force=True, timeout=3000)
                print("  Cancelled")
        except Exception:
            pass
        await asyncio.sleep(1)
        print("  NOTE: 请手动设置原创")
        return result

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
        """触发保存"""
        js = (JS_DIR / "trigger_save.js").read_text(encoding="utf-8")
        result = await self.page.evaluate(js)
        print(f"Save: {result}")

        # 也尝试 Ctrl+S
        await self.page.keyboard.press("Meta+s")
        await asyncio.sleep(2)
        return result

    async def screenshot(self, output_path: str = "/tmp/wechat_editor.png", full_page: bool = True):
        """截图当前页面（默认长截图）"""
        await self.page.screenshot(path=output_path, full_page=full_page)
        print(f"Screenshot: {output_path}")
        return output_path

    async def get_token(self) -> str:
        """从页面 URL 提取 token"""
        match = re.search(r"token=(\d+)", self.page.url)
        return match.group(1) if match else ""

    async def verify_draft(self, expected_title: str, screenshot_path: str = None) -> bool:
        """验证草稿是否已保存且包含预期标题。

        优先用 DOM 验证（编辑器标题 + 保存状态），API 做辅助。
        """
        page = self.page

        # 方法1: DOM 验证 — 直接检查编辑器中的标题和保存状态
        dom_result = await page.evaluate("""() => {
            var result = {};

            // 标题：#title 输入框
            var titleEl = document.querySelector('#title');
            result.title = titleEl ? titleEl.value : '';

            // 保存状态：底部状态栏是否显示「已保存」
            var saveStatus = document.querySelector('.tips_global, .editor-tips, .preview-tips');
            result.saveText = saveStatus ? saveStatus.textContent.trim() : '';

            // 原创状态
            var origLabel = document.querySelector('.original_primary_tips, .js_original_tips');
            result.originalText = origLabel ? origLabel.textContent.trim() : '';

            // 正文字数
            var wordCount = document.querySelector('.editor_footer .count_tips, .js_word_count');
            result.wordCount = wordCount ? wordCount.textContent.trim() : '';

            return result;
        }""")

        title_in_editor = dom_result.get("title", "")
        save_text = dom_result.get("saveText", "")
        original_text = dom_result.get("originalText", "")
        word_count = dom_result.get("wordCount", "")

        print(f"  Editor title: '{title_in_editor}'")
        print(f"  Save status: '{save_text}'")
        if original_text:
            print(f"  Original: '{original_text}'")
        if word_count:
            print(f"  Word count: '{word_count}'")

        if screenshot_path:
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                pass

        # 判定：标题匹配 + 已保存
        title_match = expected_title[:10] in title_in_editor if title_in_editor else False
        is_saved = "已保存" in save_text or "saved" in save_text.lower()

        if title_match and is_saved:
            print(f"  VERIFIED (DOM): title matches, draft saved")
            return True
        elif title_match:
            print(f"  VERIFIED (DOM): title matches (save status unclear: '{save_text}')")
            return True
        elif title_in_editor:
            print(f"  WARNING: title mismatch - expected '{expected_title[:20]}', got '{title_in_editor[:20]}'")
            return False

        # 方法2 fallback: API 验证
        print(f"  DOM verification inconclusive, trying API...")
        token = await self._get_token()
        if not token:
            print("  ERROR: no token for API verification")
            return False

        api_result = await page.evaluate("""(token) => {
            var endpoints = [
                '/cgi-bin/appmsg?action=list_ex&begin=0&count=5&type=77&token=' + token + '&lang=zh_CN&f=json',
                '/cgi-bin/appmsg?action=list_ex&begin=0&count=5&type=10&token=' + token + '&lang=zh_CN&f=json',
                '/cgi-bin/draft?action=list&begin=0&count=5&token=' + token + '&lang=zh_CN&f=json'
            ];

            for (var i = 0; i < endpoints.length; i++) {
                try {
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', endpoints[i], false);
                    xhr.send();
                    if (xhr.status !== 200) continue;
                    var data = JSON.parse(xhr.responseText);

                    if (data.app_msg_list && data.app_msg_list.length > 0) {
                        return {
                            ok: true, endpoint: i,
                            titles: data.app_msg_list.map(function(item) {
                                return item.title || item.digest || '';
                            }).slice(0, 5)
                        };
                    }

                    if (data.item && data.item.length > 0) {
                        var titles = [];
                        for (var j = 0; j < data.item.length && j < 5; j++) {
                            var content = data.item[j].content;
                            if (content && content.news_item) {
                                for (var k = 0; k < content.news_item.length; k++) {
                                    titles.push(content.news_item[k].title);
                                }
                            }
                        }
                        if (titles.length > 0) {
                            return {ok: true, endpoint: i, titles: titles};
                        }
                    }
                } catch (e) {}
            }
            return {ok: false, error: 'all endpoints failed'};
        }""", token)

        if api_result.get("ok") and api_result.get("titles"):
            titles = api_result["titles"]
            print(f"  Draft titles (API endpoint {api_result.get('endpoint')}): {titles[:3]}")
            found = any(expected_title[:10] in t for t in titles if t)
            print(f"  Found '{expected_title[:10]}': {found}")
            return found

        print("  Draft verification inconclusive")
        return False

    async def close(self):
        """关闭连接（不关闭浏览器）"""
        if hasattr(self, 'pw') and self.pw:
            await self.pw.stop()


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
