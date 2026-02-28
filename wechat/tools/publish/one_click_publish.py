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
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # nuwa-project/

# mdnice
MDNICE_URL = "https://editor.mdnice.com/"
MDNICE_THEME = "橙心"


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

    # 提取图片 — 表格中（兼容 backtick 和裸路径）
    for m in re.finditer(r"\|\s*`?(images/\S+?)`?\s*\|", text):
        img = m.group(1).strip()
        if img not in info["images"] and img != info["cover"]:
            info["images"].append(img)

    for m in re.finditer(r"\|\s*`(\S+\.(?:png|jpg|jpeg|gif))`\s*\|", text):
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


def start_https_server(images_dir: Path, port: int = 18443) -> subprocess.Popen:
    """启动 HTTPS 图片服务器（后台进程）"""
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


async def mdnice_render(md_text: str, screenshot_dir: Path = None) -> bool:
    """用 Playwright 操作 mdnice.com 排版，复制富文本到剪贴板

    流程：打开 mdnice → 清空编辑器 → 粘贴 markdown → 选橙心主题 → 点复制
    """
    from playwright.async_api import async_playwright

    print("--- mdnice 排版 ---")
    pw = await async_playwright().__aenter__()
    browser = await pw.chromium.launch(headless=False)  # 需要看得见剪贴板交互
    page = await browser.new_page()

    try:
        # 1. 打开 mdnice
        print("  Opening mdnice.com...")
        await page.goto(MDNICE_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_01_loaded.png"))

        # 2. 找到编辑器（CodeMirror），清空并填入 markdown
        print("  Pasting markdown into editor...")
        # mdnice 用 CodeMirror，找 .CodeMirror textarea 或直接操作
        editor = await page.query_selector(".CodeMirror")
        if not editor:
            # 备选：找 textarea 或 contenteditable
            editor = await page.query_selector("textarea")
        if not editor:
            print("  ERROR: 找不到 mdnice 编辑器", file=sys.stderr)
            if screenshot_dir:
                await page.screenshot(path=str(screenshot_dir / "_mdnice_error.png"))
            return False

        # 点击编辑器获得焦点
        await editor.click()
        await asyncio.sleep(0.3)

        # 全选 + 删除现有内容
        await page.keyboard.press("Meta+a")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)

        # 输入 markdown（通过剪贴板粘贴，比逐字输入快）
        # 先把 md 写入系统剪贴板
        proc = subprocess.run(
            ["pbcopy"], input=md_text.encode("utf-8"), timeout=5
        )
        await page.keyboard.press("Meta+v")
        await asyncio.sleep(2)  # 等待渲染

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_02_pasted.png"))

        # 3. 选择橙心主题
        print(f"  Selecting theme: {MDNICE_THEME}...")
        # 点击主题按钮（通常在顶部工具栏）
        theme_btn = await page.query_selector('[class*="theme"]')
        if not theme_btn:
            # 尝试找包含"主题"文字的按钮
            theme_btn = await page.get_by_text("主题").first.element_handle()
        if theme_btn:
            await theme_btn.click()
            await asyncio.sleep(1)

            # 在主题列表中找橙心
            orange = await page.get_by_text(MDNICE_THEME).first.element_handle()
            if orange:
                await orange.click()
                await asyncio.sleep(1)
                # 点"使用"按钮
                use_btn = await page.get_by_text("使用").first.element_handle()
                if use_btn:
                    await use_btn.click()
                    await asyncio.sleep(1)
                    print(f"  Theme '{MDNICE_THEME}' applied")
            else:
                print(f"  WARNING: 主题 '{MDNICE_THEME}' 未找到", file=sys.stderr)
        else:
            print("  WARNING: 主题按钮未找到", file=sys.stderr)

        if screenshot_dir:
            await page.screenshot(path=str(screenshot_dir / "_mdnice_03_themed.png"))

        # 4. 点击复制按钮
        print("  Copying formatted content...")
        copy_btn = await page.get_by_text("复制").first.element_handle()
        if not copy_btn:
            copy_btn = await page.query_selector('[class*="copy"]')
        if copy_btn:
            await copy_btn.click()
            await asyncio.sleep(1)
            print("  Copied to clipboard")
        else:
            print("  WARNING: 复制按钮未找到，尝试手动复制右侧预览", file=sys.stderr)
            # fallback: 选中右侧预览区域内容并复制
            preview = await page.query_selector('[class*="preview"]')
            if preview:
                await preview.click()
                await page.keyboard.press("Meta+a")
                await page.keyboard.press("Meta+c")
                await asyncio.sleep(1)

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
        await browser.close()
        await pw.__aexit__(None, None, None)


async def publish(topic_dir: Path, dry_run: bool = False,
                  cdp_url: str = "http://localhost:9222", port: int = 18443):
    """完整发布流程"""

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

    # ── Step 1: mdnice 排版 → 富文本到剪贴板 ──
    ok = await mdnice_render(md_text, screenshot_dir=topic_dir)
    if not ok:
        print("ERROR: mdnice 排版失败", file=sys.stderr)
        return 1

    if dry_run:
        print("\n=== DRY RUN ===")
        print("mdnice 排版完成，富文本已在剪贴板")
        print("截图保存在选题目录（_mdnice_*.png）")
        print("Skipping 微信编辑器操作")
        return 0

    # ── Step 2: Playwright CDP → 微信编辑器 ──
    from wechat_automator import WeChatAutomator
    sys.path.insert(0, str(SCRIPT_DIR))

    auto = WeChatAutomator(cdp_url=cdp_url)
    await auto.connect()

    # 2a. 新建图文
    print("\n--- 新建图文 ---")
    await auto.new_post()
    await asyncio.sleep(2)
    await auto.find_editor_page()

    # 2b. 粘贴 mdnice 富文本
    print("\n--- 粘贴正文 ---")
    await auto.paste_clipboard()
    await asyncio.sleep(2)

    # 2c. 设置标题
    if info["title"]:
        print(f"\n--- 设置标题: {info['title'][:30]}... ---")
        await auto.set_title(info["title"])
        await asyncio.sleep(0.5)

    # 2d. 设置简介
    if info["description"]:
        print(f"\n--- 设置简介: {info['description'][:30]}... ---")
        await auto.set_description(info["description"])
        await asyncio.sleep(0.5)

    # 2e. 上传图片
    https_proc = None
    if images_dir.exists() and info["images"]:
        print(f"\n--- 上传 {len(info['images'])} 张图片 ---")
        https_proc = start_https_server(images_dir, port)
        if https_proc:
            for img_rel in info["images"]:
                img_name = Path(img_rel).name
                img_url = f"https://localhost:{port}/{img_name}"
                print(f"  Uploading: {img_name}")
                try:
                    await auto.upload_image_via_js(img_url, img_name)
                except Exception as e:
                    print(f"  WARNING: Upload failed for {img_name}: {e}", file=sys.stderr)
                await asyncio.sleep(1)

    # 2f. 上传封面图
    if info["cover"]:
        cover_path = topic_dir / info["cover"]
        if cover_path.exists():
            print(f"\n--- 上传封面图: {info['cover']} ---")
            if not https_proc and images_dir.exists():
                https_proc = start_https_server(images_dir, port)
            if https_proc:
                cover_url = f"https://localhost:{port}/{cover_path.name}"
                try:
                    await auto.upload_image_via_js(cover_url, cover_path.name)
                except Exception as e:
                    print(f"  WARNING: Cover upload failed: {e}", file=sys.stderr)

    # 2g. 开启原创 + 赞赏
    print("\n--- 开启原创+赞赏 ---")
    try:
        await auto.enable_original()
    except Exception as e:
        print(f"WARNING: 原创开启失败: {e}", file=sys.stderr)
    await asyncio.sleep(1)

    # 2h. 清除空表格
    print("\n--- 清除空表格 ---")
    await auto.remove_empty_tables()

    # 2i. 保存
    print("\n--- 保存草稿 ---")
    await auto.trigger_save()
    await asyncio.sleep(2)

    # ── Step 3: 截图验证 ──
    screenshot_path = str(topic_dir / "_publish_screenshot.png")
    print(f"\n--- 截图验证 ---")
    await auto.screenshot(screenshot_path)

    # 清理
    if https_proc:
        https_proc.terminate()
        print("HTTPS server stopped")

    await auto.close()

    # ── Step 4: 通知 ──
    notify_msg = f"草稿已保存: {info['title'][:30]}"
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{notify_msg}" with title "降临派手记 · 发布"'
        ], timeout=5)
    except Exception:
        pass

    print(f"\n{'='*60}")
    print(f"DONE: 草稿已保存到微信后台")
    print(f"截图: {screenshot_path}")
    print(f"请在微信后台确认并发布")
    print(f"{'='*60}")
    return 0


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
