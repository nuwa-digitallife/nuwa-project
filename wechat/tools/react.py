#!/usr/bin/env python3
"""
新闻反应管道 — 从链接到草稿的一键流程

场景：看到一篇新闻/公众号文章，想快速出一篇反应文。
输入链接 + 指令 → 获取原文 → 创建选题 → 深度调研 → 写作 → 通知

使用:
  python react.py --url "https://mp.weixin.qq.com/s/xxxxx" --persona 大史
  python react.py --url "https://..." --instructions "和蒸馏门文章关联" --persona 大史 --series 独立篇
  python react.py --url "https://..." --topic "自定义选题名" --persona 章北海
  python react.py --dry-run --url "..."   # 只创建选题+获取原文，不写作

手机触发（SSH）:
  ssh mac-mini "cd ~/nuwa-project && source ~/venv/automation/bin/activate && python wechat/tools/react.py --url '...' --persona 大史"
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # nuwa-project/
WECHAT_DIR = SCRIPT_DIR.parent           # wechat/
LOG_DIR = PROJECT_ROOT / "logs"
DEVLOG_FILE = LOG_DIR / "devlog.jsonl"

TODAY = datetime.now().strftime("%Y-%m-%d")


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def devlog(entry: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now().isoformat()
    entry["project"] = "wechat-react"
    with open(DEVLOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def fetch_article(url: str) -> dict:
    """获取文章内容，返回 {title, content, source}"""
    result = {"title": "", "content": "", "source": url}

    if "mp.weixin.qq.com" in url:
        # 微信文章 → exporter API
        result = fetch_wechat_article(url)
    else:
        # 通用链接 → claude WebFetch
        result = fetch_generic_article(url)

    return result


def fetch_wechat_article(url: str) -> dict:
    """通过 exporter API 获取微信文章

    ⛔ 微信文章有反爬拦截，不能直接 HTTP 请求。
    必须走 exporter API (localhost:3000) + auth-key。
    exporter 用 Chrome cookie 解密绕过反爬。
    """
    import requests

    result = {"title": "", "content": "", "source": url}

    # 获取 auth-key（Chrome cookie 解密）
    sys.path.insert(0, str(SCRIPT_DIR))
    auth_key = None
    try:
        from material_collector import get_auth_key
        auth_key = get_auth_key()
    except Exception as e:
        log(f"WARNING: 无法获取 auth-key: {e}")
        log("确保 exporter 运行中 (localhost:3000) 且 Chrome 已登录微信")

    # 通过 exporter API 获取（唯一可靠路径）
    try:
        api_url = f"http://localhost:3000/api/public/v1/download?url={url}&format=markdown"
        headers = {}
        if auth_key:
            headers["X-Auth-Key"] = auth_key
        resp = requests.get(api_url, headers=headers, timeout=30)
        if resp.status_code == 200:
            content = resp.text
            lines = content.strip().split("\n")
            for line in lines:
                if line.startswith("# "):
                    result["title"] = line[2:].strip()
                    break
            result["content"] = content
            log(f"Fetched via exporter: {result['title'][:40]}...")
            return result
        else:
            log(f"Exporter API returned {resp.status_code}: {resp.text[:100]}")

    except requests.ConnectionError:
        log("ERROR: exporter 未运行。启动: cd wechat-article-exporter && pnpm start")
    except Exception as e:
        log(f"Exporter API failed: {e}")

    # ⛔ 不 fallback 到 WebFetch — 微信文章直接 fetch 必挂
    log("ERROR: 无法获取微信文章。请确保:")
    log("  1. exporter 运行中: http://localhost:3000")
    log("  2. Chrome 已登录微信公众平台")
    log("  3. auth-key 可用（Chrome cookie 未过期）")
    return result


def fetch_generic_article(url: str) -> dict:
    """通用文章获取（claude -p + WebFetch）"""
    result = {"title": "", "content": "", "source": url}

    prompt = f"""请获取以下 URL 的内容，提取标题和正文：
URL: {url}

输出格式：
# {{标题}}

{{正文内容，保留原始结构}}
"""
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "WebFetch"],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            content = proc.stdout.strip()
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    result["title"] = line[2:].strip()
                    break
            result["content"] = content
            log(f"Fetched via claude: {result['title'][:40]}...")
    except Exception as e:
        log(f"Claude fetch failed: {e}")

    return result


def extract_topic_name(article: dict, instructions: str = "") -> str:
    """从文章标题/内容提取简短选题名"""
    title = article.get("title", "")
    if title:
        # 简化标题：去掉标点和过长的部分
        clean = re.sub(r"[｜|：:！!？?—\-\s]+", "", title)
        if len(clean) > 15:
            clean = clean[:15]
        return clean
    return "新闻反应"


def create_topic_dir(topic_name: str, article: dict, instructions: str = "") -> Path:
    """创建选题目录并保存触发文章和指令"""
    base_dir = WECHAT_DIR / "公众号选题"
    topic_dir = base_dir / f"{TODAY}|{topic_name}"
    materials_dir = topic_dir / "素材"
    materials_dir.mkdir(parents=True, exist_ok=True)

    # 保存原文
    trigger_path = materials_dir / "trigger_article.md"
    trigger_path.write_text(
        f"# 触发文章\n\n来源: {article['source']}\n获取时间: {datetime.now().isoformat()}\n\n---\n\n{article['content']}",
        encoding="utf-8"
    )

    # 保存用户指令
    if instructions:
        instr_path = materials_dir / "user_instructions.md"
        instr_path.write_text(
            f"# 用户指令\n\n{instructions}\n",
            encoding="utf-8"
        )

    log(f"Topic dir: {topic_dir}")
    return topic_dir


def run_deep_research(topic_dir: Path):
    """调用 deep_research.py"""
    deep_research = SCRIPT_DIR / "write_engine" / "deep_research.py"

    # 读取用户指令作为额外 context
    instr_file = topic_dir / "素材" / "user_instructions.md"
    extra_context = ""
    if instr_file.exists():
        extra_context = instr_file.read_text(encoding="utf-8")

    log("Starting deep research...")
    proc = subprocess.run(
        [sys.executable, str(deep_research),
         "--topic-dir", str(topic_dir)],
        timeout=1200,
    )

    deep_file = topic_dir / "素材" / "deep_research.md"
    if deep_file.exists():
        log("Deep research complete")
    else:
        log("WARNING: Deep research may have failed")


def run_write_engine(topic_dir: Path, persona: str = "大史", series: str = ""):
    """调用 engine.py"""
    engine = SCRIPT_DIR / "write_engine" / "engine.py"

    cmd = [
        sys.executable, str(engine),
        "--topic-dir", str(topic_dir),
        "--persona", persona,
    ]
    if series:
        cmd.extend(["--series", series])

    log(f"Starting write engine (persona: {persona})...")
    proc = subprocess.run(cmd, timeout=3600)

    article = topic_dir / "article.md"
    if article.exists() and article.stat().st_size > 0:
        chars = article.stat().st_size
        log(f"Article complete: {chars} bytes")
        return True
    else:
        log("WARNING: Writing may have failed")
        return False


def notify(title: str, message: str):
    """macOS 通知"""
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], timeout=5)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="新闻反应管道 — 链接到草稿")
    parser.add_argument("--url", required=True, help="文章 URL")
    parser.add_argument("--instructions", "-i", default="", help="写作指令")
    parser.add_argument("--persona", "-p", default="大史", help="人设 (大史/章北海)")
    parser.add_argument("--series", "-s", default="独立篇", help="系列名")
    parser.add_argument("--topic", "-t", default="", help="自定义选题名（不指定则自动提取）")
    parser.add_argument("--dry-run", action="store_true", help="只创建选题+获取原文")
    parser.add_argument("--skip-research", action="store_true", help="跳过深度调研")
    args = parser.parse_args()

    log("=" * 50)
    log("新闻反应管道启动")
    log(f"URL: {args.url}")
    log(f"人设: {args.persona}")
    log("=" * 50)

    # Step 1: 获取文章
    log("\n--- Step 1: 获取文章 ---")
    article = fetch_article(args.url)
    if not article["content"]:
        log("ERROR: 无法获取文章内容")
        devlog({
            "type": "issue",
            "context": "react.py",
            "action": f"获取失败: {args.url[:50]}",
            "result": "empty content",
        })
        sys.exit(1)

    # Step 2: 创建选题目录
    log("\n--- Step 2: 创建选题目录 ---")
    topic_name = args.topic or extract_topic_name(article, args.instructions)
    topic_dir = create_topic_dir(topic_name, article, args.instructions)

    if args.dry_run:
        log("\n=== DRY RUN ===")
        log(f"Topic: {topic_name}")
        log(f"Dir: {topic_dir}")
        log(f"Article: {article['title'][:50]}")
        log("Skipping research and writing")
        return

    # Step 3: 深度调研
    if not args.skip_research:
        log("\n--- Step 3: 深度调研 ---")
        run_deep_research(topic_dir)
    else:
        log("\n--- Step 3: 跳过深度调研 ---")

    # Step 4: 写作引擎
    log("\n--- Step 4: 写作引擎 ---")
    success = run_write_engine(topic_dir, args.persona, args.series)

    # Step 5: 通知
    if success:
        notify("降临派手记 · 反应文", f"草稿完成: {topic_name}")
        log(f"\n{'='*50}")
        log(f"DONE: {topic_name}")
        log(f"目录: {topic_dir}")
        log(f"下一步: python publish/one_click_publish.py --topic-dir '{topic_dir}'")
        log(f"{'='*50}")
    else:
        notify("降临派手记 · 反应文", f"写作失败: {topic_name}")

    devlog({
        "type": "task",
        "context": "react.py",
        "action": f"反应文: {topic_name}",
        "result": "success" if success else "failed",
        "insight": f"URL: {args.url[:50]}, persona: {args.persona}",
    })


if __name__ == "__main__":
    main()
