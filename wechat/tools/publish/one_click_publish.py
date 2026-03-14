#!/usr/bin/env python3
"""
一键发布 — 从选题目录到微信草稿的端到端自动化

流程:
  1. 读取 article_mdnice.md + publish_guide.md + images/
  2. CDP Chrome tab 中打开 mdnice → 粘贴 markdown → 选橙心主题 → 复制富文本
  3. CDP 连接微信编辑器:
     a. 新建图文 → 粘贴富文本
     b. 设标题/简介
     c. 上传配图到微信 CDN（base64，不依赖 HTTPS 服务器）
     d. 上传封面图
     e. 开启原创+赞赏
     f. 删除空表格 + 保存
  4. 草稿列表验证 + Claude 视觉验证 → 结构化报告

使用:
  python one_click_publish.py --topic-dir "wechat/公众号选题/2026-02-21|机器人棋局"
  python one_click_publish.py --topic-dirs "dir1" "dir2" "dir3"   # 多篇
  python one_click_publish.py --topic-dir ... --dry-run           # 只走 mdnice 排版
  python one_click_publish.py --topic-dir ... --resume-from title # 断点续跑
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from publish_types import ArticleResult, PublishReport, StepResult, StepStatus

# 确保 CDP 和 Playwright 连接不走代理
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # nuwa-project/

# 发布步骤（有序）— resume 机制按此顺序执行
PUBLISH_STEPS = [
    "upload_images",    # 上传图片到微信 CDN
    "mdnice",           # mdnice 排版 + 复制富文本到剪贴板
    "paste",            # 新建图文 + 粘贴正文
    "inject_images",    # 注入配图到编辑器（mdnice 未带入时的兜底）
    "title",            # 设置标题
    "desc",             # 设置简介
    "cover",            # 设置封面图
    "original",         # 开启原创
    "reward",           # 开启赞赏
    "poll",             # 插入投票
    "save",             # 清除空表格 + 保存
    "verify",           # 验证草稿（8项完整验收）
]


def checkpoint_path(topic_dir: Path) -> Path:
    """Per-article checkpoint file"""
    return topic_dir / "_publish_checkpoint.json"


def load_checkpoint(topic_dir: Path) -> dict:
    """加载 checkpoint"""
    cp = checkpoint_path(topic_dir)
    if not cp.exists():
        return {}
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
        return data
    except Exception:
        return {}


def save_checkpoint(topic_dir: Path, step: str, completed_steps: list, extra: dict = None):
    """保存 checkpoint（保留已有的 extra 数据如 cdn_map）"""
    # 先读取已有 checkpoint，保留之前步骤写入的 extra 数据
    existing = load_checkpoint(topic_dir)
    data = {
        "topic_dir": str(topic_dir),
        "last_step": step,
        "completed_steps": completed_steps,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    # 保留已有的非核心字段（如 cdn_map）
    for k, v in existing.items():
        if k not in data:
            data[k] = v
    # 新 extra 覆盖旧值
    if extra:
        data.update(extra)
    checkpoint_path(topic_dir).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def clear_checkpoint(topic_dir: Path):
    """清除 checkpoint"""
    cp = checkpoint_path(topic_dir)
    if cp.exists():
        cp.unlink()


    # verify_with_claude 已删除 — 用 open_draft_preview() 代替（打开预览页截图，不调 AI）


def parse_publish_guide(guide_path: Path) -> dict:
    """从 publish_guide.md 提取发布信息"""
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

    # 提取简介
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

    # 提取图片
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
    """从 poll.md 提取投票信息"""
    if not poll_path.exists():
        return {}
    text = poll_path.read_text(encoding="utf-8")
    result = {"question": "", "options": []}
    m = re.search(r"##\s*问题\s*\n+(.+)", text)
    if not m:
        m = re.search(r"问题[：:]\s*(.+)", text)
    if m:
        result["question"] = m.group(1).strip()
    for m in re.finditer(r"^\d+\.\s*(.+)", text, re.MULTILINE):
        result["options"].append(m.group(1).strip())
    return result


async def publish_one(auto, topic_dir: Path, resume_from: str = None,
                      dry_run: bool = False) -> ArticleResult:
    """发布单篇文章，收集每步 StepResult → ArticleResult"""

    article = ArticleResult(topic_dir=str(topic_dir))

    # ── 验证文件 ──
    guide_path = topic_dir / "publish_guide.md"
    md_path = topic_dir / "article_mdnice.md"
    images_dir = topic_dir / "images"

    if not guide_path.exists():
        article.steps.append(StepResult("validate", StepStatus.FAILED, f"缺少 {guide_path}"))
        return article
    if not md_path.exists():
        article.steps.append(StepResult("validate", StepStatus.FAILED, f"缺少 {md_path}"))
        return article

    info = parse_publish_guide(guide_path)
    article.title = info["title"]
    print(f"\n{'='*60}")
    print(f"  PUBLISHING: {info['title']}")
    print(f"{'='*60}")
    print(f"  Description: {info['description'][:50]}...")
    print(f"  Cover: {info['cover']}")
    print(f"  Images: {len(info['images'])} files")

    md_text = md_path.read_text(encoding="utf-8")
    print(f"  Markdown: {len(md_text)} chars")

    # ── Resume 逻辑 ──
    ckpt = load_checkpoint(topic_dir)
    completed_steps = []

    if resume_from:
        if resume_from not in PUBLISH_STEPS:
            article.steps.append(StepResult("validate", StepStatus.FAILED,
                                            f"无效步骤 '{resume_from}'"))
            return article
        for s in PUBLISH_STEPS:
            if s == resume_from:
                break
            completed_steps.append(s)
        print(f"  RESUME: 从 '{resume_from}' 开始，跳过 {len(completed_steps)} 步")
    elif ckpt.get("completed_steps"):
        completed_steps = ckpt["completed_steps"]
        next_step = None
        for s in PUBLISH_STEPS:
            if s not in completed_steps:
                next_step = s
                break
        if next_step:
            print(f"  CHECKPOINT: 从 '{next_step}' 恢复")
        else:
            completed_steps = []

    def should_run(step: str) -> bool:
        return step not in completed_steps

    def mark_done(step: str, extra: dict = None):
        if step not in completed_steps:
            completed_steps.append(step)
        save_checkpoint(topic_dir, step, completed_steps, extra)

    # ── Dry run ──
    if dry_run:
        result = await auto.mdnice_render_in_tab(md_text, screenshot_dir=topic_dir)
        article.steps.append(result)
        if result.ok:
            print("\n=== DRY RUN: mdnice 排版完成 ===")
        return article

    # ── 每篇发布前复查登录态 ──
    if not await auto.check_login():
        article.steps.append(StepResult("login", StepStatus.FAILED, "登录超时"))
        return article

    # 确保有 MP 页面（如果跳过 paste 步骤，找已有编辑器）
    if not should_run("paste"):
        found_editor = await auto.find_editor_page()
        if not found_editor:
            article.steps.append(StepResult("paste", StepStatus.FAILED,
                                            "未找到编辑器页面（resume 需要已打开的编辑器）"))
            return article
    else:
        mp_ready = await auto.find_or_create_mp_page()
        if not mp_ready:
            article.steps.append(StepResult("paste", StepStatus.FAILED, "无法访问微信后台"))
            return article

        # 关闭残留的失效编辑器 tab（用 CDP API 而非 page.close，后者会挂）
        for page in list(auto.context.pages):
            if page != auto.page and ("appmsg_edit" in page.url or "appmsg" in page.url):
                if "token=" not in page.url:
                    try:
                        cdp = await page.context.new_cdp_session(page)
                        await cdp.send("Page.close")
                    except Exception:
                        pass  # 关不掉就算了，不影响主流程

    print(f"  [DEBUG] Building image list...")
    # ── upload_images ──
    cdn_map = {}
    all_images = list(info["images"])
    if images_dir.exists():
        for img_file in sorted(images_dir.glob("img_*.png")) + sorted(images_dir.glob("img_*.jpg")):
            rel = f"images/{img_file.name}"
            if rel not in all_images:
                all_images.append(rel)

    # ⛔ 封面唯一化：用标题 hash 给 cover 命名，防止多篇文章 cover.png 互相覆盖
    import hashlib, shutil
    cover_unique_name = None
    if info["cover"]:
        cover_src = topic_dir / info["cover"]
        if cover_src.exists():
            slug = hashlib.md5(info["title"].encode()).hexdigest()[:8]
            cover_unique_name = f"cover_{slug}{cover_src.suffix}"
            cover_tmp = cover_src.parent / cover_unique_name
            shutil.copy2(cover_src, cover_tmp)
            # 用唯一名替换 all_images 中的 cover 路径
            unique_rel = f"images/{cover_unique_name}"
            info["cover"] = unique_rel
            print(f"  Cover renamed: {cover_src.name} → {cover_unique_name}")

    if info["cover"] and info["cover"] not in all_images:
        all_images.append(info["cover"])

    if should_run("upload_images"):
        if images_dir.exists() and all_images:
            print(f"\n--- 上传 {len(all_images)} 张图片到 CDN ---")
            failed_uploads = []
            for img_rel in all_images:
                img_path = topic_dir / img_rel
                if not img_path.exists():
                    continue
                try:
                    result = await auto.upload_image_file(img_path)
                    if result.get("ok") and result.get("cdn_url"):
                        cdn_map[img_rel] = result["cdn_url"]
                        cdn_map[img_path.name] = result["cdn_url"]
                    else:
                        failed_uploads.append(img_rel)
                except Exception as e:
                    failed_uploads.append(img_rel)
                    print(f"  Upload failed: {img_rel}: {e}", file=sys.stderr)
                await asyncio.sleep(0.5)

            print(f"  CDN mapping: {len(cdn_map)} images uploaded")
            step_msg = f"{len(cdn_map)} uploaded"
            if failed_uploads:
                step_msg += f", {len(failed_uploads)} failed: {', '.join(failed_uploads)}"
            article.steps.append(StepResult("upload_images", StepStatus.SUCCESS, step_msg))
        else:
            article.steps.append(StepResult("upload_images", StepStatus.SKIPPED, "无图片"))
        mark_done("upload_images", {"cdn_map": {k: v for k, v in cdn_map.items() if "/" in k}})
    else:
        saved_cdn = ckpt.get("cdn_map", {})
        if saved_cdn:
            cdn_map.update(saved_cdn)
            for k, v in list(saved_cdn.items()):
                cdn_map[Path(k).name] = v
        article.steps.append(StepResult("upload_images", StepStatus.SKIPPED,
                                        f"restored {len(saved_cdn)} from checkpoint"))

    # ── 替换本地路径为 CDN URL ──
    md_for_mdnice = md_text
    for local_path, cdn_url in cdn_map.items():
        md_for_mdnice = md_for_mdnice.replace(local_path, cdn_url)

    # ── 修复 mdnice 加粗+引号渲染 bug ──
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
        print(f"  Fixed {bold_quote_fixes} bold+quote patterns")

    # ── mdnice ──
    if should_run("mdnice"):
        result = await auto.mdnice_render_in_tab(md_for_mdnice, screenshot_dir=topic_dir)
        article.steps.append(result)
        if not result.ok:
            return article  # mdnice 失败则无法继续
        mark_done("mdnice")
    else:
        article.steps.append(StepResult("mdnice", StepStatus.SKIPPED))

    # ── paste ──
    if should_run("paste"):
        print("\n--- 新建图文 ---")
        await auto.new_post()
        await asyncio.sleep(2)
        print("\n--- 粘贴正文 ---")
        result = await auto.paste_clipboard()
        article.steps.append(result)
        await asyncio.sleep(3)
        mark_done("paste")
    else:
        article.steps.append(StepResult("paste", StepStatus.SKIPPED))

    # ── inject_images ──
    if should_run("inject_images"):
        if cdn_map:
            print(f"\n--- 注入配图 ({len(cdn_map)} URLs) ---")
            result = await auto.inject_images(cdn_map)
            article.steps.append(result)
            if result.ok:
                await asyncio.sleep(2)
        else:
            article.steps.append(StepResult("inject_images", StepStatus.SKIPPED, "no cdn_map"))
        mark_done("inject_images")
    else:
        article.steps.append(StepResult("inject_images", StepStatus.SKIPPED))

    # ── title ──
    if should_run("title"):
        if info["title"]:
            print(f"\n--- 设置标题 ---")
            result = await auto.set_title(info["title"])
            article.steps.append(result)
        else:
            article.steps.append(StepResult("title", StepStatus.SKIPPED, "无标题"))
        mark_done("title")
    else:
        article.steps.append(StepResult("title", StepStatus.SKIPPED))

    # ── desc ──
    if should_run("desc"):
        if info["description"]:
            print(f"\n--- 设置简介 ---")
            result = await auto.set_description(info["description"])
            article.steps.append(result)
        else:
            article.steps.append(StepResult("desc", StepStatus.SKIPPED, "无简介"))
        mark_done("desc")
    else:
        article.steps.append(StepResult("desc", StepStatus.SKIPPED))

    # ── 清理残留弹窗 ──
    await auto.cleanup_stale_dialogs()

    # ── cover ──
    if should_run("cover"):
        if info["cover"]:
            cover_name = Path(info["cover"]).name
            print(f"\n--- 设置封面图: {cover_name} ---")
            result = await auto.set_cover_image(cover_name)
            article.steps.append(result)
        else:
            article.steps.append(StepResult("cover", StepStatus.SKIPPED, "无封面"))
        mark_done("cover")
    else:
        article.steps.append(StepResult("cover", StepStatus.SKIPPED))

    # ── original ──
    if should_run("original"):
        print("\n--- 开启原创 ---")
        result = await auto.enable_original()
        article.steps.append(result)
        await asyncio.sleep(1)
        mark_done("original")
    else:
        article.steps.append(StepResult("original", StepStatus.SKIPPED))

    # ── reward ──
    if should_run("reward"):
        print("\n--- 开启赞赏 ---")
        result = await auto.enable_reward()
        article.steps.append(result)
        await asyncio.sleep(1)
        mark_done("reward")
    else:
        article.steps.append(StepResult("reward", StepStatus.SKIPPED))

    # ── poll ──
    if should_run("poll"):
        poll_info = parse_poll_file(topic_dir / "poll.md")
        if poll_info.get("question") and poll_info.get("options"):
            print(f"\n--- 插入投票 ---")
            result = await auto.add_poll(poll_info["question"], poll_info["options"])
            article.steps.append(result)
        else:
            article.steps.append(StepResult("poll", StepStatus.SKIPPED, "无投票文件"))
        await asyncio.sleep(1)
        mark_done("poll")
    else:
        article.steps.append(StepResult("poll", StepStatus.SKIPPED))

    # ── save ──
    if should_run("save"):
        print("\n--- 保存草稿 ---")
        result = await auto.save_draft()
        article.steps.append(result)
        mark_done("save")
    else:
        article.steps.append(StepResult("save", StepStatus.SKIPPED))

    # ── verify ──
    # ⛔ 验证是 BLOCKING 的：DOM 检查 + Claude 视觉验证都必须通过才算成功。
    # 视觉验证不是可选的附加步骤，而是最终判定标准。
    # 这条规则代码化在此，任何 Agent 都跳不过。
    if should_run("verify"):
        print(f"\n--- 验证草稿（DOM 检查 + 视觉验证，两关都必须过） ---")

        expected_img_count = len([f for f in (info.get("images") or []) if not f.endswith("cover.png")])

        # 第一关：DOM 检查（标题/简介/封面/原创/赞赏/正文/配图/投票）
        verify_result = await auto.verify_article_complete(
            expected_title=info["title"],
            expected_desc=info.get("desc", ""),
            expected_image_count=expected_img_count,
            screenshot_dir=str(topic_dir),
        )
        article.steps.append(verify_result)

        # 草稿列表验证
        list_result = await auto.verify_draft_in_list(info["title"], str(topic_dir))
        article.steps.append(list_result)

        # 第二关：打开草稿预览页截图（用人类的方式验证，固化为代码）
        # ⛔ 这步是代码化的铁律：不是"记住要打开预览"，而是代码强制打开。
        from wechat_automator import safe_screenshot
        preview_ok = False
        try:
            preview_result = await auto.open_draft_preview(info["title"], str(topic_dir))
            article.steps.append(preview_result)
            preview_ok = preview_result.ok
        except Exception as e:
            article.steps.append(StepResult("preview", StepStatus.FAILED, str(e)))
            print(f"  预览页打开失败: {e}", file=sys.stderr)

        # 最终判定：DOM 检查 + 预览截图都要有
        if verify_result.ok:
            if preview_ok:
                print(f"\n  ✓ DOM 检查通过 + 预览截图已保存")
            else:
                print(f"\n  ✓ DOM 检查通过（预览截图失败，不阻塞）")
            clear_checkpoint(topic_dir)
        else:
            print(f"\n  ⛔ DOM 检查有失败项，草稿未确认。", file=sys.stderr)

        mark_done("verify")
    else:
        article.steps.append(StepResult("verify", StepStatus.SKIPPED))
        clear_checkpoint(topic_dir)

    # 通知
    status_text = "OK" if article.success else "ISSUES"
    safe_title = info['title'][:20].replace('"', '').replace("'", "").replace('\\', '')
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "草稿 {status_text}" with title "{safe_title}"'
        ], timeout=5, capture_output=True)
    except Exception:
        pass

    return article


async def publish_all(topic_dirs: list[Path], dry_run: bool = False,
                      cdp_url: str = "http://localhost:9222",
                      resume_from: str = None) -> PublishReport:
    """多篇编排：连接一次 → 逐篇发布 → 停在草稿列表 → 结构化报告"""

    sys.path.insert(0, str(SCRIPT_DIR))
    from wechat_automator import WeChatAutomator

    report = PublishReport()
    auto = WeChatAutomator(cdp_url=cdp_url)
    await auto.connect()

    # 预检登录态
    if not dry_run:
        login_ok = await auto.check_login()
        if not login_ok:
            print("ERROR: 无法登录微信后台", file=sys.stderr)
            await auto.disconnect()
            for td in topic_dirs:
                report.articles.append(ArticleResult(
                    topic_dir=str(td),
                    steps=[StepResult("login", StepStatus.FAILED, "登录超时")]
                ))
            return report

    for i, topic_dir in enumerate(topic_dirs):
        print(f"\n{'#'*60}")
        print(f"  Article {i+1}/{len(topic_dirs)}: {topic_dir.name}")
        print(f"{'#'*60}")

        result = await publish_one(auto, topic_dir, resume_from=resume_from, dry_run=dry_run)
        report.articles.append(result)

        # 发完一篇后，如果不是最后一篇，新建下一篇需要的编辑器页面
        # （publish_one 内部会调 new_post）

    # 全部发完，停在草稿列表
    if not dry_run:
        await auto.leave_on_draft_list()

    await auto.disconnect()
    return report


def main():
    parser = argparse.ArgumentParser(
        description="一键发布到微信公众号",
        epilog=f"可用步骤（--resume-from）: {', '.join(PUBLISH_STEPS)}"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic-dir", help="选题目录路径（单篇）")
    group.add_argument("--topic-dirs", nargs="+", help="选题目录路径（多篇）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只走 mdnice 排版，不操作微信编辑器")
    parser.add_argument("--resume-from", choices=PUBLISH_STEPS, default=None,
                        help="从指定步骤恢复（跳过之前的步骤）")
    parser.add_argument("--cdp-url", default="http://localhost:9222",
                        help="Chrome CDP URL")
    args = parser.parse_args()

    # 收集目录
    if args.topic_dir:
        raw_dirs = [args.topic_dir]
    else:
        raw_dirs = args.topic_dirs

    topic_dirs = []
    for d in raw_dirs:
        td = Path(d).resolve()
        if not td.exists():
            td = PROJECT_ROOT / d
        if not td.exists():
            print(f"ERROR: 目录不存在: {d}", file=sys.stderr)
            sys.exit(1)
        topic_dirs.append(td)

    report = asyncio.run(publish_all(
        topic_dirs,
        dry_run=args.dry_run,
        cdp_url=args.cdp_url,
        resume_from=args.resume_from,
    ))

    print(report.summary())

    # exit code: 0 if all success, 1 if any failed
    sys.exit(0 if all(a.success for a in report.articles) else 1)


if __name__ == "__main__":
    main()
