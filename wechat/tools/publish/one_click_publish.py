#!/usr/bin/env python3
"""
一键发布 — 从选题目录到微信草稿的端到端自动化

流程:
  1. 读取 article_mdnice.md + publish_guide.md + images/
  2. Playwright 打开 mdnice.com → 粘贴 markdown → 选橙心主题 → 复制富文本
  3. Playwright CDP 连接微信编辑器:
     a. 新建图文 → 粘贴富文本
     b. 设标题/简介
     c. HTTPS 服务器 → 上传配图到微信 CDN
     d. 上传封面图
     e. 开启原创+赞赏
     f. 删除空表格 + 保存
  4. 截图验证 → 通知

使用:
  python one_click_publish.py --topic-dir "wechat/公众号选题/2026-02-21|机器人棋局"
  python one_click_publish.py --topic-dir ... --dry-run      # 只走 mdnice 排版+截图，不操作微信
  python one_click_publish.py --topic-dir ... --cdp-url http://localhost:9222
"""

import argparse
import asyncio
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

# 确保 CDP 和 Playwright 连接不走代理
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # nuwa-project/

# mdnice
MDNICE_URL = "https://editor.mdnice.com/"
MDNICE_THEME = "橙心"


def verify_with_claude(screenshot_paths: list[str], article_text: str,
                       expected_images: int, title: str,
                       timeout: int = 120) -> dict:
    """调用 claude -p 验证编辑器截图中的正文和配图。

    与 engine.py 的 run_claude 同一模式：claude -p + Read 工具看截图。
    返回 {"pass": bool, "issues": [...], "summary": str}
    """
    # 构建 prompt：让 claude 读截图并验证
    screenshot_section = "\n".join(f"- {p}" for p in screenshot_paths)

    # 从文章抽关键句作为验证锚点
    lines = [l.strip() for l in article_text.split("\n")
             if l.strip() and not l.strip().startswith("!")]
    probes = []
    for idx in [1, len(lines) // 4, len(lines) // 2, -3]:
        if abs(idx) < len(lines):
            p = lines[idx].strip("*#>- ").replace("**", "")[:60]
            if len(p) > 10:
                probes.append(p)
    probes_section = "\n".join(f"- \"{p}\"" for p in probes)

    prompt = f"""你是发布验证 Agent。请用 Read 工具逐一打开以下编辑器截图，验证微信文章草稿的完整性。

## 截图文件（按页面顺序）
{screenshot_section}

## 验证项

1. **正文完整性**：以下关键句是否都能在截图中找到对应文字？
{probes_section}

2. **配图**：文章中应有 {expected_images} 张正文配图（不含封面）。请数截图中实际可见的图片数量。图片是否正常渲染（不是破图/空白框）？

3. **标题**：编辑器标题是否为「{title}」？

4. **排版**：是否有明显的排版问题（文字截断、乱码、空白段落过多）？

## 输出格式

只输出 JSON，不要其他文字：
```json
{{"pass": true/false, "text_found": 4, "text_total": 4, "images_found": 5, "images_expected": {expected_images}, "title_ok": true/false, "issues": ["issue1", "issue2"]}}
```

如果所有验证项通过，"pass" 为 true，"issues" 为空数组。
"""

    cmd = [
        "claude", "-p",
        "--model", "haiku",
        "--allowedTools", "Read",
        "--effort", "low",
        "--no-session-persistence",
    ]

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            env=env, start_new_session=True,
        )
        stdout, stderr = proc.communicate(input=prompt, timeout=timeout)

        if proc.returncode != 0:
            print(f"  verify_with_claude failed (exit={proc.returncode}): {stderr[:200]}", file=sys.stderr)
            return {"pass": False, "issues": [f"claude verification failed: exit {proc.returncode}"]}

        # 提取 JSON
        text = stdout.strip()
        json_match = re.search(r'\{[^{}]*"pass"[^{}]*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"  verify_with_claude: no JSON in output: {text[:300]}", file=sys.stderr)
            return {"pass": False, "issues": ["could not parse verification output"]}

    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
        return {"pass": False, "issues": ["verification timed out"]}
    except Exception as e:
        return {"pass": False, "issues": [str(e)]}


def parse_publish_guide(guide_path: Path) -> dict:
    """从 publish_guide.md 提取发布信息

    兼容两种格式：
    - 行内格式: **标题：** xxx
    - Section 格式: ## 简介\n\n**xxx**
    """
    text = guide_path.read_text(encoding="utf-8")
    info = {
        "title": "",
        "description": "",
        "cover": "images/cover.png",
        "images": [],
    }

    # 提取标题
    m = re.search(r"\*\*标题\*\*[：:]\s*(.+)", text)
    if not m:
        m = re.search(r"\*\*标题[：:]\*\*\s*(.+)", text)
    if m:
        info["title"] = m.group(1).strip()

    # 提取简介 — 多种格式
    m = re.search(r"\*\*简介[：:]\*\*\s*(.+)", text)
    if not m:
        m = re.search(r"\*\*简介\*\*[：:]\s*(.+)", text)
    if not m:
        m = re.search(r"##\s*简介\s*\n+\*\*(.+?)\*\*", text)
    if not m:
        m = re.search(r"##\s*简介\s*\n+([^\n#].+)", text)
    if m:
        info["description"] = m.group(1).strip()

    # 提取封面图
    m = re.search(r"\*\*封面图[：:]\*\*\s*(\S+)", text)
    if not m:
        m = re.search(r"\*\*封面图\*\*[：:]\s*(\S+)", text)
    if m:
        info["cover"] = m.group(1).strip().split("（")[0].split("(")[0]

    # 提取图片 — 表格中（兼容 backtick、裸路径、带/不带 images/ 前缀）
    for m in re.finditer(r"\|\s*`?(images/\S+?)`?\s*\|", text):
        img = m.group(1).strip()
        if img not in info["images"] and img != info["cover"]:
            info["images"].append(img)

    for m in re.finditer(r"\|\s*`?(\S+\.(?:png|jpg|jpeg|gif))`?\s*\|", text):
        img_name = m.group(1).strip()
        img_path = f"images/{img_name}" if not img_name.startswith("images/") else img_name
        if img_path not in info["images"] and img_path != info["cover"]:
            info["images"].append(img_path)

    for m in re.finditer(r"插图\d+[：:]\s*(\S+\.(?:png|jpg|jpeg|gif))", text):
        img = m.group(1).strip()
        img_path = f"images/{img}" if not img.startswith("images/") else img
        if img_path not in info["images"]:
            info["images"].append(img_path)

    return info


def parse_poll_file(poll_path: Path) -> dict:
    """从 poll.md 提取投票信息：question + options"""
    if not poll_path.exists():
        return {}
    text = poll_path.read_text(encoding="utf-8")
    result = {"question": "", "options": []}
    # 提取问题（兼容两种格式：## 问题\n内容  或  问题：内容）
    m = re.search(r"##\s*问题\s*\n+(.+)", text)
    if not m:
        m = re.search(r"问题[：:]\s*(.+)", text)
    if m:
        result["question"] = m.group(1).strip()
    # 提取选项（数字列表）
    for m in re.finditer(r"^\d+\.\s*(.+)", text, re.MULTILINE):
        result["options"].append(m.group(1).strip())
    return result


def start_https_server(images_dir: Path, port: int = 18443) -> subprocess.Popen:
    """启动 HTTPS 图片服务器（后台进程）"""
    # 先杀掉可能残留的旧服务器
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                subprocess.run(["kill", pid.strip()], timeout=5)
            time.sleep(1)
    except Exception:
        pass

    server_script = SCRIPT_DIR / "https_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(server_script), str(images_dir), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    if proc.poll() is not None:
        stderr = proc.stderr.read().decode()
        print(f"HTTPS server failed: {stderr}", file=sys.stderr)
        return None
    print(f"HTTPS server started on port {port} (PID {proc.pid})")
    return proc


MDNICE_PROFILE = os.path.expanduser("~/.mdnice-profile")


async def _hide_modals(page):
    """JS 强制隐藏 mdnice 的所有 ant-modal 弹窗（版本更新、登录提示等）"""
    await page.evaluate("""() => {
        document.querySelectorAll(
            '.ant-modal-root, .ant-modal-mask, .ant-modal-wrap, .global-mask'
        ).forEach(el => el.style.display = 'none');
    }""")
    await asyncio.sleep(0.3)


async def _ensure_article(page, md_text: str):
    """确保有活跃文章（预览区才能渲染）。

    如果没有活跃文章，通过 Cmd+V 触发"新增文章"对话框创建一篇。
    创建后编辑器会被清空，需要重新粘贴内容。
    返回 True 表示有活跃文章（可能是已有的或新创建的）。
    """
    # 检查是否已有活跃文章（#nice 预览区有内容）
    has_article = await page.evaluate("""() => {
        const nice = document.querySelector('#nice');
        return nice && nice.children.length > 0;
    }""")
    if has_article:
        return True

    print("  No active article, creating one...")
    # Cmd+V 粘贴内容 → 触发 "新增文章" 对话框
    subprocess.run(["pbcopy"], input=md_text.encode("utf-8"), timeout=5)
    editor = await page.query_selector(".CodeMirror")
    if editor:
        await editor.click(force=True)
        await asyncio.sleep(0.3)
    await page.keyboard.press("Meta+v")
    await asyncio.sleep(2)

    # 恢复被隐藏的 modal（之前 _hide_modals 可能隐藏了）
    await page.evaluate("""() => {
        document.querySelectorAll('.ant-modal-root, .ant-modal-mask, .ant-modal-wrap')
            .forEach(el => el.style.display = '');
    }""")
    await asyncio.sleep(0.5)

    # 处理"新增文章"对话框
    has_dialog = await page.evaluate("""() => {
        const wraps = document.querySelectorAll('.ant-modal-wrap');
        for (const w of wraps) {
            if (getComputedStyle(w).display !== 'none' && w.textContent.includes('新增文章'))
                return true;
        }
        return false;
    }""")
    if not has_dialog:
        return False

    # 选择文件夹（ant-select 下拉框）
    select_el = await page.query_selector('.ant-modal .ant-select-selector')
    if select_el:
        await select_el.click(force=True)
        await asyncio.sleep(1)
        first_opt = await page.query_selector('.ant-select-item-option')
        if first_opt and await first_opt.is_visible():
            await first_opt.click(force=True)
            await asyncio.sleep(0.5)

    # 点击"新增"按钮
    create_btn = await page.query_selector('.ant-modal .ant-btn-primary')
    if create_btn and not await create_btn.is_disabled():
        await create_btn.click(force=True)
        await asyncio.sleep(3)
        print("  Article created")
        await _hide_modals(page)
        return True

    return False


async def mdnice_render(md_text: str, screenshot_dir: Path = None,
                        keep_browser: bool = False) -> bool:
    """用 Playwright 持久化浏览器操作 mdnice.com 排版，复制富文本到剪贴板

    使用 persistent context 保持登录状态，无需每次扫码。
    流程：打开 mdnice → 关闭弹窗 → 确保有文章 → 设置内容 → 选主题 → 复制到微信

    Args:
        keep_browser: True 时不关闭浏览器（调试/dry-run 用）
    """
    from playwright.async_api import async_playwright

    print("--- mdnice 排版 ---")

    # 清理可能残留的锁文件
    for lock in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        lock_path = os.path.join(MDNICE_PROFILE, lock)
        if os.path.exists(lock_path):
            os.remove(lock_path)

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=MDNICE_PROFILE,
        headless=False,
        viewport={"width": 1280, "height": 720},
    )
    page = context.pages[0] if context.pages else await context.new_page()

    try:
        # 1. 打开 mdnice
        print("  Opening mdnice.com...")
        await page.goto(MDNICE_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # 1.5 检测登录状态，未登录则等待扫码
        needs_login = await page.evaluate("""() => {
            const modals = document.querySelectorAll('.ant-modal-wrap');
            for (const m of modals) {
                if (getComputedStyle(m).display !== 'none' && m.textContent.includes('登录'))
                    return true;
            }
            return !document.querySelector('.CodeMirror');
        }""")
        if needs_login:
            qr_path = "/tmp/mdnice_qr_login.png"
            await page.screenshot(path=qr_path)
            print(f"\n{'='*50}")
            print("⏳ mdnice 未登录，请在弹出的浏览器窗口扫码登录")
            print(f"   截图已保存: {qr_path}")
            print(f"{'='*50}\n")
            max_wait, elapsed = 120, 0
            while elapsed < max_wait:
                await asyncio.sleep(3)
                elapsed += 3
                has_editor = await page.evaluate(
                    "() => !!document.querySelector('.CodeMirror')"
                )
                if has_editor:
                    print("  ✅ mdnice 登录成功！")
                    break
                if elapsed % 15 == 0:
                    await page.screenshot(path=qr_path)
                    print(f"   仍在等待扫码... ({elapsed}s/{max_wait}s)")
            else:
                print("  ERROR: mdnice 登录超时（120秒）", file=sys.stderr)
                return False

        await _hide_modals(page)

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_01_loaded.png"))

        # 2. 确保有活跃文章（否则预览不渲染、复制不工作）
        await _ensure_article(page, md_text)

        # 3. 通过剪贴板粘贴 markdown（Cmd+V 触发预览渲染，setValue 不行）
        print("  Pasting markdown content...")
        subprocess.run(["pbcopy"], input=md_text.encode("utf-8"), timeout=5)
        editor = await page.query_selector(".CodeMirror")
        if editor:
            await editor.click(force=True)
            await asyncio.sleep(0.3)
            await page.keyboard.press("Meta+a")
            await asyncio.sleep(0.1)
            await page.keyboard.press("Meta+v")
            await asyncio.sleep(3)  # 等待预览渲染

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_02_pasted.png"))

        # 4. 选择橙心主题
        print(f"  Selecting theme: {MDNICE_THEME}...")
        await page.click("a.nice-menu-link:has-text('主题')", force=True)
        await asyncio.sleep(2)

        # 在主题列表中找到橙心并点击其"使用"按钮
        theme_applied = await page.evaluate("""(themeName) => {
            const items = document.querySelectorAll('.theme-list > *');
            for (const item of items) {
                if (item.textContent.includes(themeName)) {
                    const btn = item.querySelector('button');
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
        await page.keyboard.press("Escape")  # 关闭主题面板
        await asyncio.sleep(1)

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_03_themed.png"))

        # 5. 点击右侧栏微信复制按钮
        print("  Copying formatted content for WeChat...")
        wechat_btn = await page.query_selector("a.nice-btn-wechat")
        if wechat_btn:
            await wechat_btn.click(force=True)
            await asyncio.sleep(2)
            print("  Copied to clipboard via WeChat button")
        else:
            print("  WARNING: WeChat 复制按钮未找到", file=sys.stderr)
            return False

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_04_copied.png"))

        return True

    except Exception as e:
        print(f"  mdnice error: {e}", file=sys.stderr)
        if screenshot_dir:
            try:
                await page.screenshot(path=str(screenshot_dir / "_mdnice_error.png"))
            except Exception:
                pass
        return False

    finally:
        if keep_browser:
            print("  Browser kept open — Ctrl+C to close")
            try:
                while True:
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                await context.close()
                await pw.stop()
        else:
            await context.close()
            await pw.stop()


async def publish(topic_dir: Path, dry_run: bool = False,
                  cdp_url: str = "http://localhost:9222", port: int = 18443):
    """完整发布流程

    关键改进（v2）：
    - 图片先上传到微信 CDN → 拿到 CDN URL → 替换 markdown 里的本地路径
    - mdnice 渲染时图片已是 CDN URL → 富文本粘贴到编辑器后图片自动显示
    - 原创对话框用 Playwright keyboard 输入作者（触发 Vue v-model）
    - 验证改为检查草稿箱（不只是截图编辑器）
    """

    # ── Step 0: 验证文件 ──
    guide_path = topic_dir / "publish_guide.md"
    md_path = topic_dir / "article_mdnice.md"
    images_dir = topic_dir / "images"

    if not guide_path.exists():
        print(f"ERROR: 缺少 {guide_path}", file=sys.stderr)
        return 1
    if not md_path.exists():
        print(f"ERROR: 缺少 {md_path}", file=sys.stderr)
        return 1

    info = parse_publish_guide(guide_path)
    print(f"Title: {info['title']}")
    print(f"Description: {info['description'][:50]}...")
    print(f"Cover: {info['cover']}")
    print(f"Images: {len(info['images'])} files")

    md_text = md_path.read_text(encoding="utf-8")
    print(f"Markdown: {len(md_text)} chars")

    # ── Dry run: 只走 mdnice，不操作微信 ──
    if dry_run:
        ok = await mdnice_render(md_text, screenshot_dir=topic_dir,
                                 keep_browser=False)
        if not ok:
            print("ERROR: mdnice 排版失败", file=sys.stderr)
            return 1
        print("\n=== DRY RUN ===")
        print("mdnice 排版完成，富文本已在剪贴板")
        final_shot = topic_dir / "_mdnice_03_themed.png"
        if final_shot.exists():
            subprocess.run(["open", str(final_shot)], timeout=5)
            print(f"已打开截图: {final_shot}")
        return 0

    # ── Step 1: 连接微信后台 + 上传图片到 CDN ──
    sys.path.insert(0, str(SCRIPT_DIR))
    from wechat_automator import WeChatAutomator

    auto = WeChatAutomator(cdp_url=cdp_url)
    await auto.connect()

    # 确保有可用的 MP 页面（用于上传图片等 API 调用）
    mp_ready = await auto.find_or_create_mp_page()
    if not mp_ready:
        print("ERROR: 无法访问微信后台，请先在 Chrome 中登录", file=sys.stderr)
        await auto.close()
        return 1

    # 关闭之前残留的失效编辑器 tab
    for page in list(auto.context.pages):
        if page != auto.page and ("appmsg_edit" in page.url or "appmsg" in page.url):
            if "token=" not in page.url:
                await page.close()
                print(f"  Closed stale tab: {page.url[:60]}")

    # 上传所有图片到微信 CDN，收集 CDN URL 映射（base64，不依赖 HTTPS 服务器）
    cdn_map = {}  # "images/xxx.png" -> "https://mmbiz.qpic.cn/..."
    # 从 publish_guide 获取列表，同时扫描 images/ 目录补充实际存在的文件
    all_images = list(info["images"])
    if images_dir.exists():
        for img_file in sorted(images_dir.glob("img_*.png")):
            rel = f"images/{img_file.name}"
            if rel not in all_images:
                all_images.append(rel)
        for img_file in sorted(images_dir.glob("img_*.jpg")):
            rel = f"images/{img_file.name}"
            if rel not in all_images:
                all_images.append(rel)
    if info["cover"] and info["cover"] not in all_images:
        all_images.append(info["cover"])

    https_proc = None
    if images_dir.exists() and all_images:
        print(f"\n--- 上传 {len(all_images)} 张图片到 CDN ---")
        for img_rel in all_images:
            img_path = topic_dir / img_rel
            if not img_path.exists():
                print(f"  SKIP (not found): {img_rel}")
                continue
            try:
                result = await auto.upload_image_file(img_path)
                if result.get("ok") and result.get("cdn_url"):
                    cdn_map[img_rel] = result["cdn_url"]
                    cdn_map[img_path.name] = result["cdn_url"]
            except Exception as e:
                print(f"  WARNING: Upload failed for {img_path.name}: {e}", file=sys.stderr)
            await asyncio.sleep(0.5)

    print(f"\n  CDN mapping: {len(cdn_map)} images uploaded")
    for local, cdn in cdn_map.items():
        if "/" in local:  # 只打印带路径的
            print(f"    {local} → {cdn[:60]}...")

    # ── Step 2: 替换 markdown 中的本地路径为 CDN URL ──
    md_for_mdnice = md_text
    for local_path, cdn_url in cdn_map.items():
        md_for_mdnice = md_for_mdnice.replace(local_path, cdn_url)

    replacements = md_text.count("images/") - md_for_mdnice.count("images/")
    print(f"  Replaced {replacements} image references with CDN URLs")

    # ── Step 2.5: 修复 mdnice 加粗+引号渲染 bug ──
    # mdnice 的 markdown 解析器在 ** 紧邻引号字符时不触发粗体
    # 例如 **"text"** 不会加粗，改用 <strong> HTML 标签
    bold_quote_fixes = 0
    def _fix_bold_quote(m):
        nonlocal bold_quote_fixes
        bold_quote_fixes += 1
        return f"<strong>{m.group(1)}</strong>"
    quote_chars = r'[""\u201c\u201d\u2018\u2019\u300a\u300b]'
    md_for_mdnice = re.sub(
        rf'\*\*({quote_chars}.*?{quote_chars})\*\*',
        _fix_bold_quote,
        md_for_mdnice,
    )
    if bold_quote_fixes:
        print(f"  Fixed {bold_quote_fixes} bold+quote patterns for mdnice")

    # ── Step 3: mdnice 排版 → 富文本到剪贴板 ──
    ok = await mdnice_render(md_for_mdnice, screenshot_dir=topic_dir)
    if not ok:
        print("ERROR: mdnice 排版失败", file=sys.stderr)
        if https_proc:
            https_proc.terminate()
        await auto.close()
        return 1

    # ── Step 4: 新建图文 + 粘贴 ──
    print("\n--- 新建图文 ---")
    await auto.new_post()
    await asyncio.sleep(2)

    print("\n--- 粘贴正文 ---")
    await auto.paste_clipboard()
    await asyncio.sleep(3)  # 给编辑器时间处理富文本

    # ── Step 5: 设置标题和简介 ──
    if info["title"]:
        print(f"\n--- 设置标题: {info['title'][:30]}... ---")
        try:
            await auto.set_title(info["title"])
        except Exception as e:
            print(f"  WARNING: 设置标题失败: {e}", file=sys.stderr)
        await asyncio.sleep(0.5)

    if info["description"]:
        print(f"\n--- 设置简介: {info['description'][:30]}... ---")
        try:
            await auto.set_description(info["description"])
        except Exception as e:
            print(f"  WARNING: 设置简介失败: {e}", file=sys.stderr)
        await asyncio.sleep(0.5)

    # ── Step 5.5: 清理残留弹窗（防止二次运行脏状态） ──
    print("\n--- 清理残留弹窗 ---")
    await auto.cleanup_stale_dialogs()

    # ── Step 6a: 设置封面图 ──
    if info["cover"]:
        cover_name = Path(info["cover"]).name
        print(f"\n--- 设置封面图: {cover_name} ---")
        try:
            ok = await auto.set_cover_image(cover_name)
            if not ok:
                print("  WARNING: 封面图设置失败，请手动设置", file=sys.stderr)
        except Exception as e:
            print(f"  WARNING: 封面图设置异常: {e}", file=sys.stderr)
        await asyncio.sleep(1)

    # ── Step 6b: 开启原创 ──
    print("\n--- 开启原创 ---")
    try:
        await auto.enable_original()
    except Exception as e:
        print(f"WARNING: 原创开启失败: {e}", file=sys.stderr)
    await asyncio.sleep(1)

    # ── Step 6c: 开启赞赏 ──
    print("\n--- 开启赞赏 ---")
    try:
        await auto.enable_reward()
    except Exception as e:
        print(f"WARNING: 赞赏开启失败: {e}", file=sys.stderr)
    await asyncio.sleep(1)

    # ── Step 7: 插入投票 ──
    poll_path = topic_dir / "poll.md"
    poll_info = parse_poll_file(poll_path)
    if poll_info.get("question") and poll_info.get("options"):
        print(f"\n--- 插入投票: {poll_info['question'][:30]}... ---")
        try:
            ok = await auto.add_poll(poll_info["question"], poll_info["options"])
            if not ok:
                print("  WARNING: 投票插入失败，请手动添加", file=sys.stderr)
        except Exception as e:
            print(f"  WARNING: 投票插入异常: {e}", file=sys.stderr)
        await asyncio.sleep(1)
    else:
        print("\n--- 无投票文件，跳过 ---")

    # ── Step 8: 清除空表格 + 保存 ──
    print("\n--- 清除空表格 ---")
    await auto.remove_empty_tables()

    print("\n--- 保存草稿 ---")
    await auto.trigger_save()
    await asyncio.sleep(3)

    # ── Step 8: 验证草稿（内容级检查） ──
    print(f"\n--- 验证草稿 ---")
    draft_screenshot = str(topic_dir / "_draft_verify.png")
    found = await auto.verify_draft(info["title"], screenshot_path=draft_screenshot)
    if found:
        print(f"  VERIFIED: 草稿箱中找到文章")
    else:
        print(f"  WARNING: 草稿箱中未找到文章", file=sys.stderr)
        await auto.screenshot(str(topic_dir / "_editor_debug.png"))

    # ── Step 8.5: 内容验证（正文+配图，带等待重试） ──
    print(f"\n--- 内容验证 ---")
    verify_ok = True
    try:
        editor_page = auto.page

        # --- 正文验证：从 article_mdnice.md 抽关键句，等待编辑器渲染 ---
        lines = md_text.split("\n")
        non_empty = [l.strip() for l in lines if l.strip() and not l.strip().startswith("!")]
        # 抽首段、中间、末段各一句作为探针（去掉 markdown 格式标记）
        probes = []
        for idx in [1, len(non_empty) // 2, -2]:
            if abs(idx) < len(non_empty):
                probe = non_empty[idx].strip("*#>- ").replace("**", "")[:40]
                if len(probe) > 10:
                    probes.append(probe)

        text_ok = False
        for attempt in range(5):  # 最多等 10s
            editor_text = await editor_page.evaluate("""() => {
                const el = document.querySelector('#js_editor')
                    || document.querySelector('.edui-body-container')
                    || document.querySelector('[contenteditable]');
                return el ? el.innerText.substring(0, 5000) : '';
            }""")
            matched = sum(1 for p in probes if p in editor_text)
            if matched >= max(1, len(probes) - 1):
                text_ok = True
                break
            await asyncio.sleep(2)

        if text_ok:
            print(f"  ✅ 正文验证通过（{matched}/{len(probes)} 探针匹配）")
        else:
            print(f"  ❌ 正文验证失败：只匹配 {matched}/{len(probes)} 探针", file=sys.stderr)
            for p in probes:
                hit = "✓" if p in editor_text else "✗"
                print(f"     {hit} \"{p[:30]}...\"")
            verify_ok = False

        # --- 配图验证：等待图片加载，检查 naturalWidth > 0 ---
        expected_images = len([f for f in (info.get("images") or []) if not f.endswith("cover.png")])
        loaded_count = 0
        for attempt in range(5):  # 最多等 15s
            loaded_count = await editor_page.evaluate("""() => {
                const el = document.querySelector('#js_editor')
                    || document.querySelector('.edui-body-container')
                    || document.querySelector('[contenteditable]');
                if (!el) return 0;
                const imgs = el.querySelectorAll('img');
                let loaded = 0;
                for (const img of imgs) {
                    if (img.naturalWidth > 0 && img.src.includes('mmbiz')) loaded++;
                }
                return loaded;
            }""")
            if loaded_count >= expected_images:
                break
            await asyncio.sleep(3)

        total_imgs = await editor_page.evaluate("""() => {
            const el = document.querySelector('#js_editor')
                || document.querySelector('.edui-body-container')
                || document.querySelector('[contenteditable]');
            return el ? el.querySelectorAll('img').length : 0;
        }""")

        if loaded_count >= expected_images:
            print(f"  ✅ 配图验证通过（{loaded_count} 张加载成功，共 {total_imgs} 张 img 标签）")
        else:
            print(f"  ❌ 配图验证失败：{loaded_count}/{expected_images} 张加载成功（共 {total_imgs} 张 img）", file=sys.stderr)
            verify_ok = False

        # --- 逐屏截图：滚动编辑器，每屏截一张 ---
        scroll_shots = await editor_page.evaluate("""() => {
            const el = document.querySelector('#js_editor')
                || document.querySelector('.edui-body-container')
                || document.querySelector('[contenteditable]');
            if (!el) return {scrollHeight: 0, clientHeight: 0};
            return {scrollHeight: el.scrollHeight, clientHeight: el.clientHeight || 600};
        }""")
        scroll_h = scroll_shots.get("scrollHeight", 0)
        client_h = scroll_shots.get("clientHeight", 600) or 600
        num_screens = max(1, min(10, (scroll_h + client_h - 1) // client_h))

        for i in range(num_screens):
            await editor_page.evaluate(f"""() => {{
                const el = document.querySelector('#js_editor')
                    || document.querySelector('.edui-body-container')
                    || document.querySelector('[contenteditable]');
                if (el) el.scrollTop = {i * client_h};
            }}""")
            await asyncio.sleep(0.5)
            shot_path = str(topic_dir / f"_verify_{i+1:02d}.png")
            await editor_page.screenshot(path=shot_path)
        print(f"  📸 逐屏截图: {num_screens} 张 (_verify_01.png ~ _verify_{num_screens:02d}.png)")

        # 全页截图（兜底）
        content_screenshot = str(topic_dir / "_content_verify.png")
        await editor_page.screenshot(path=content_screenshot, full_page=True)

    except Exception as e:
        print(f"  内容验证异常: {e}", file=sys.stderr)
        verify_ok = False

    await auto.close()

    # ── Step 9: Claude 视觉验证（最后一道关） ──
    print(f"\n--- Claude 视觉验证 ---")
    verify_screenshots = sorted(str(p) for p in topic_dir.glob("_verify_*.png"))
    if verify_screenshots:
        expected_img_count = len([f for f in (info.get("images") or []) if not f.endswith("cover.png")])
        claude_result = verify_with_claude(
            screenshot_paths=verify_screenshots,
            article_text=md_text,
            expected_images=expected_img_count,
            title=info["title"],
        )
        if claude_result.get("pass"):
            print(f"  ✅ Claude 验证通过: "
                  f"文字 {claude_result.get('text_found', '?')}/{claude_result.get('text_total', '?')}, "
                  f"配图 {claude_result.get('images_found', '?')}/{claude_result.get('images_expected', '?')}")
        else:
            issues = claude_result.get("issues", [])
            print(f"  ❌ Claude 验证未通过:", file=sys.stderr)
            for issue in issues:
                print(f"     - {issue}", file=sys.stderr)
            verify_ok = False
    else:
        print(f"  ⚠️ 无逐屏截图，跳过 Claude 验证")

    # ── Step 10: 通知 ──
    status = "VERIFIED" if found else "UNVERIFIED"
    # 通知文本中去掉特殊字符避免 osascript 语法错误
    safe_title = info['title'][:20].replace('"', '').replace("'", "").replace('\\', '')
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "草稿{status}" with title "{safe_title}"'
        ], timeout=5)
    except Exception:
        pass

    print(f"\n{'='*60}")
    if found and verify_ok:
        print(f"DONE: 草稿已保存，正文+配图验证通过")
    elif found and not verify_ok:
        print(f"WARNING: 草稿已保存，但正文/配图验证未通过，请手动检查")
    else:
        print(f"FAIL: 草稿可能未保存，请手动检查")
    print(f"验证截图: {draft_screenshot}")
    print(f"逐屏截图: {topic_dir}/_verify_*.png")
    print(f"{'='*60}")
    return 0 if (found and verify_ok) else 1


def main():
    parser = argparse.ArgumentParser(description="一键发布到微信公众号")
    parser.add_argument("--topic-dir", required=True, help="选题目录路径")
    parser.add_argument("--dry-run", action="store_true",
                        help="只走 mdnice 排版，不操作微信编辑器")
    parser.add_argument("--cdp-url", default="http://localhost:9222",
                        help="Chrome CDP URL (微信编辑器)")
    parser.add_argument("--port", type=int, default=18443,
                        help="HTTPS 图片服务器端口")
    args = parser.parse_args()

    topic_dir = Path(args.topic_dir).resolve()
    if not topic_dir.exists():
        topic_dir = PROJECT_ROOT / args.topic_dir
    if not topic_dir.exists():
        print(f"ERROR: 目录不存在: {args.topic_dir}", file=sys.stderr)
        sys.exit(1)

    rc = asyncio.run(publish(
        topic_dir,
        dry_run=args.dry_run,
        cdp_url=args.cdp_url,
        port=args.port,
    ))
    sys.exit(rc)


if __name__ == "__main__":
    main()
