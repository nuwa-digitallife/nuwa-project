#!/usr/bin/env python3
"""
发布步骤逐步测试脚本

每步：连接 CDP → 执行操作 → 截图 → 打印结果 → 断开（不关 Chrome）

用法：
  python test_steps.py connect                         # 测试 CDP 连接（幂等）
  python test_steps.py title "测试标题"                 # 测试设置标题
  python test_steps.py desc "测试简介"                  # 测试设置简介
  python test_steps.py cover cover.png                  # 测试设置封面
  python test_steps.py original                         # 测试开启原创
  python test_steps.py reward                           # 测试开启赞赏
  python test_steps.py poll                             # 测试插入投票
  python test_steps.py cleanup                          # 测试清理弹窗
  python test_steps.py save                             # 测试保存
  python test_steps.py mdnice                           # 测试 mdnice in-tab
  python test_steps.py all                              # 全部步骤
  python test_steps.py --cdp-url http://localhost:9222  # 指定 CDP 地址
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

# 确保 CDP 不走代理
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

SCRIPT_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = Path("/tmp/test_steps")

# 测试用数据
TEST_TITLE = "测试标题-自动化验证"
TEST_DESC = "这是一段测试简介，用于验证自动化发布流程。"
TEST_POLL_Q = "你觉得这个自动化好用吗？"
TEST_POLL_OPTS = ["非常好用", "还行", "不太行"]


def screenshot_path(step: str) -> str:
    return str(SCREENSHOT_DIR / f"{step}_{int(time.time())}.png")


def print_step_result(result):
    """打印 StepResult，兼容 bool 和 StepResult"""
    if hasattr(result, 'step'):
        status = "PASS" if result.ok else "FAIL"
        print(f"  {status}: [{result.step}] {result.message}")
        if result.retries > 0:
            print(f"  (retries: {result.retries})")
        return result.ok
    # backward compat: plain bool
    return bool(result)


async def safe_screenshot(page, path: str):
    """截图，超时不阻塞测试"""
    try:
        await page.screenshot(path=path, full_page=False, timeout=10000)
        print(f"  Screenshot: {path}")
    except Exception as e:
        print(f"  Screenshot skipped: {e}")


async def get_automator(cdp_url: str):
    """连接 CDP 并找到编辑器页面"""
    sys.path.insert(0, str(SCRIPT_DIR))
    from wechat_automator import WeChatAutomator

    auto = WeChatAutomator(cdp_url=cdp_url)
    await auto.connect()
    found = await auto.find_editor_page()
    if not found:
        print("WARNING: 未找到编辑器页面，尝试找 MP 页面...")
        await auto.find_or_create_mp_page()
    return auto


async def test_connect(cdp_url: str) -> bool:
    """测试 CDP 连接（包括幂等性测试）"""
    print("\n=== test: connect ===")
    auto = await get_automator(cdp_url)
    shot = screenshot_path("connect")
    if auto.page:
        await safe_screenshot(auto.page, shot)
        url = auto.page.url[:80]
        print(f"  Page URL: {url}")
        is_editor = "appmsg_edit" in auto.page.url
        print(f"  Is editor: {is_editor}")

    # 幂等性测试：再连一次不应报错
    print("  Testing idempotent connect...")
    await auto.connect()  # 应该打印 "Already connected"
    print("  Idempotent: OK")

    await auto.disconnect()
    print("  PASS: CDP 连接成功")
    return True


async def test_title(cdp_url: str, title: str) -> bool:
    """测试设置标题"""
    print(f"\n=== test: title '{title[:30]}' ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.set_title(title)
    shot = screenshot_path("title")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    return print_step_result(result)


async def test_desc(cdp_url: str, desc: str) -> bool:
    """测试设置简介"""
    print(f"\n=== test: desc '{desc[:30]}' ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.set_description(desc)
    shot = screenshot_path("desc")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    return print_step_result(result)


async def test_cover(cdp_url: str, cover_name: str) -> bool:
    """测试设置封面图"""
    print(f"\n=== test: cover '{cover_name}' ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.set_cover_image(cover_name)
    shot = screenshot_path("cover")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    return print_step_result(result)


async def test_original(cdp_url: str) -> bool:
    """测试开启原创"""
    print("\n=== test: original ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.enable_original()
    shot = screenshot_path("original")
    await safe_screenshot(auto.page, shot)

    # 额外检查原创标签
    status = await auto.page.evaluate("""() => {
        var el = document.querySelector('.original_primary_tips, .js_original_tips');
        return el ? el.textContent.trim() : '';
    }""")
    print(f"  Original status: '{status}'")

    await auto.disconnect()
    return print_step_result(result)


async def test_reward(cdp_url: str) -> bool:
    """测试开启赞赏"""
    print("\n=== test: reward ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.enable_reward()
    shot = screenshot_path("reward")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    return print_step_result(result)


async def test_poll(cdp_url: str) -> bool:
    """测试插入投票"""
    print("\n=== test: poll ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.add_poll(TEST_POLL_Q, TEST_POLL_OPTS)
    shot = screenshot_path("poll")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    return print_step_result(result)


async def test_cleanup(cdp_url: str) -> bool:
    """测试清理弹窗"""
    print("\n=== test: cleanup ===")
    auto = await get_automator(cdp_url)
    if not auto.page:
        print("  SKIP: 无页面")
        await auto.disconnect()
        return False

    await auto.cleanup_stale_dialogs()
    shot = screenshot_path("cleanup")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    print("  PASS: 清理完成")
    return True


async def test_save(cdp_url: str) -> bool:
    """测试保存"""
    print("\n=== test: save ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    result = await auto.save_draft()
    shot = screenshot_path("save")
    await safe_screenshot(auto.page, shot)
    await auto.disconnect()
    return print_step_result(result)


async def test_mdnice(cdp_url: str) -> bool:
    """测试 mdnice in-tab 排版"""
    print("\n=== test: mdnice (in-tab) ===")
    auto = await get_automator(cdp_url)

    test_md = "# 测试标题\n\n这是测试内容。\n\n## 第二节\n\n更多内容。"
    result = await auto.mdnice_render_in_tab(test_md)
    await auto.disconnect()
    return print_step_result(result)


async def test_verify(cdp_url: str) -> bool:
    """测试完整验收（8项清单）"""
    print("\n=== test: verify (8-item checklist) ===")
    auto = await get_automator(cdp_url)
    if not auto.page or "appmsg_edit" not in auto.page.url:
        print("  SKIP: 不在编辑器页面")
        await auto.disconnect()
        return False

    # Read title from editor to use as expected
    title = await auto.page.evaluate("""() => {
        var el = document.querySelector('#title');
        return el ? el.value : '';
    }""")
    print(f"  Editor title: '{title}'")

    result = await auto.verify_article_complete(
        expected_title=title,
        expected_image_count=0,  # unknown, just check what's there
        screenshot_dir=str(SCREENSHOT_DIR),
    )
    await auto.disconnect()
    return print_step_result(result)


async def test_all(cdp_url: str, title: str, desc: str) -> bool:
    """运行所有测试步骤"""
    print("\n" + "=" * 60)
    print("  RUNNING ALL TESTS")
    print("=" * 60)

    results = {}

    results["connect"] = await test_connect(cdp_url)
    if not results["connect"]:
        print("\n  ABORT: 连接失败，跳过后续测试")
        return False

    results["cleanup"] = await test_cleanup(cdp_url)
    results["title"] = await test_title(cdp_url, title)
    results["desc"] = await test_desc(cdp_url, desc)
    results["original"] = await test_original(cdp_url)
    results["reward"] = await test_reward(cdp_url)
    results["save"] = await test_save(cdp_url)
    # poll, cover, mdnice 跳过（需要特定条件）

    print("\n" + "=" * 60)
    print("  TEST RESULTS")
    print("=" * 60)
    all_pass = True
    for step, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {step:12s}: {status}")
        if not ok:
            all_pass = False

    print("=" * 60)
    if all_pass:
        print("  ALL TESTS PASSED")
    else:
        failed = [s for s, ok in results.items() if not ok]
        print(f"  FAILED: {', '.join(failed)}")
    print("=" * 60)
    return all_pass


def main():
    parser = argparse.ArgumentParser(description="发布步骤逐步测试")
    parser.add_argument("step", choices=[
        "connect", "title", "desc", "cover", "original",
        "reward", "poll", "cleanup", "save", "mdnice", "verify", "all"
    ], help="要测试的步骤")
    parser.add_argument("value", nargs="?", default="", help="步骤参数（标题/简介/封面文件名）")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="Chrome CDP URL")
    args = parser.parse_args()

    # 确保截图目录存在
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    step = args.step
    cdp = args.cdp_url

    if step == "connect":
        ok = asyncio.run(test_connect(cdp))
    elif step == "title":
        ok = asyncio.run(test_title(cdp, args.value or TEST_TITLE))
    elif step == "desc":
        ok = asyncio.run(test_desc(cdp, args.value or TEST_DESC))
    elif step == "cover":
        ok = asyncio.run(test_cover(cdp, args.value or "cover.png"))
    elif step == "original":
        ok = asyncio.run(test_original(cdp))
    elif step == "reward":
        ok = asyncio.run(test_reward(cdp))
    elif step == "poll":
        ok = asyncio.run(test_poll(cdp))
    elif step == "cleanup":
        ok = asyncio.run(test_cleanup(cdp))
    elif step == "save":
        ok = asyncio.run(test_save(cdp))
    elif step == "mdnice":
        ok = asyncio.run(test_mdnice(cdp))
    elif step == "verify":
        ok = asyncio.run(test_verify(cdp))
    elif step == "all":
        ok = asyncio.run(test_all(
            cdp,
            args.value or TEST_TITLE,
            TEST_DESC,
        ))

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
