"""Twitter List 页面抓取 + 推文解析

用 Playwright persistent_context 管理登录态，解析 DOM 提取推文数据。
"""
import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

import config

logger = logging.getLogger("scraper")


# ── 索引管理 ──────────────────────────────────────────────

def load_index(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_index(path: str, index: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ── DOM 解析 ──────────────────────────────────────────────

def _extract_handle(tweet_el) -> str:
    """从推文元素中提取作者 handle"""
    links = tweet_el.query_selector_all(config.SELECTORS["user_link"])
    for link in links:
        href = link.get_attribute("href") or ""
        # 匹配 /@handle 或 /handle 格式，排除 /i/ /hashtag/ 等
        m = re.match(r"^/([A-Za-z0-9_]{1,15})$", href)
        if m:
            return m.group(1)
    return ""


def _extract_display_name(tweet_el) -> str:
    """提取显示名（第一个 user link 的文本）"""
    links = tweet_el.query_selector_all(config.SELECTORS["user_link"])
    for link in links:
        href = link.get_attribute("href") or ""
        if re.match(r"^/[A-Za-z0-9_]{1,15}$", href):
            text = link.inner_text().strip()
            if text:
                return text
    return ""


def _extract_tweet_id(tweet_el) -> str:
    """从 /status/ID 链接提取 tweet_id"""
    links = tweet_el.query_selector_all(config.SELECTORS["status_link"])
    for link in links:
        href = link.get_attribute("href") or ""
        m = re.search(r"/status/(\d+)", href)
        if m:
            return m.group(1)
    return ""


def _extract_text(tweet_el) -> str:
    """提取推文正文"""
    text_el = tweet_el.query_selector(config.SELECTORS["tweet_text"])
    if text_el:
        return text_el.inner_text().strip()
    return ""


def _extract_time(tweet_el) -> str:
    """提取时间戳（ISO 格式）"""
    time_el = tweet_el.query_selector(config.SELECTORS["time"])
    if time_el:
        return time_el.get_attribute("datetime") or ""
    return ""


def _extract_links(text: str) -> list[str]:
    """从推文文本中提取 URL"""
    return re.findall(r"https?://[^\s]+", text)


def _extract_metric(tweet_el, testid: str) -> int:
    """提取互动指标数值"""
    el = tweet_el.query_selector(f'[data-testid="{testid}"]')
    if not el:
        return 0
    aria = el.get_attribute("aria-label") or ""
    # aria-label 通常是 "123 replies" 或 "1,234 Likes"
    m = re.search(r"([\d,]+)", aria)
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


def _is_retweet(tweet_el) -> bool:
    """检测是否是转推（推文上方有 "XX reposted" 提示）"""
    # 转推通常有 social context 提示
    outer_html = tweet_el.evaluate("el => el.innerHTML")
    return "reposted" in outer_html.lower()[:500]


def parse_tweet(tweet_el) -> dict | None:
    """解析单条推文 DOM 元素，返回结构化数据"""
    tweet_id = _extract_tweet_id(tweet_el)
    if not tweet_id:
        return None

    handle = _extract_handle(tweet_el)
    text = _extract_text(tweet_el)
    if not handle or not text:
        return None

    return {
        "tweet_id": tweet_id,
        "handle": handle,
        "display_name": _extract_display_name(tweet_el),
        "text": text,
        "posted_at": _extract_time(tweet_el),
        "url": f"https://x.com/{handle}/status/{tweet_id}",
        "links": _extract_links(text),
        "is_retweet": _is_retweet(tweet_el),
        "metrics": {
            "replies": _extract_metric(tweet_el, "reply"),
            "retweets": _extract_metric(tweet_el, "retweet"),
            "likes": _extract_metric(tweet_el, "like"),
        },
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


# ── 抓取主流程 ───────────────────────────────────────────

def scrape(headless: bool = True, dry_run: bool = False) -> list[dict]:
    """抓取 Twitter List 页面，返回新推文列表。

    Args:
        headless: 是否无头模式（首次登录时设为 False）
        dry_run: True 时只抓取不保存
    Returns:
        新抓到的推文列表
    """
    os.makedirs(config.AUTH_DIR, exist_ok=True)
    os.makedirs(config.TWEETS_DIR, exist_ok=True)

    index = load_index(config.INDEX_FILE)
    new_tweets = []

    with sync_playwright() as p:
        # persistent_context 复用登录态
        context = p.chromium.launch_persistent_context(
            user_data_dir=config.AUTH_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        logger.info("打开 List 页面: %s", config.LIST_URL)
        try:
            page.goto(config.LIST_URL, timeout=config.PAGE_TIMEOUT_MS)
        except PwTimeout:
            logger.error("页面加载超时 (%d ms)", config.PAGE_TIMEOUT_MS)
            context.close()
            return []

        # 检测是否需要登录
        if not headless:
            logger.info("有头模式：请在浏览器中登录 Twitter，登录完成后按 Enter 继续...")
            input("按 Enter 继续...")
            # 登录后重新导航到 List 页面
            page.goto(config.LIST_URL, timeout=config.PAGE_TIMEOUT_MS)

        # 等待推文加载
        try:
            page.wait_for_selector(
                config.SELECTORS["tweet"],
                timeout=config.TWEET_WAIT_TIMEOUT_MS,
            )
        except PwTimeout:
            # 可能是登录态过期
            current_url = page.url
            logger.error(
                "等待推文超时，可能需要重新登录。当前 URL: %s", current_url
            )
            if "login" in current_url.lower():
                logger.error("检测到登录页面，请运行 --login 重新登录")
            context.close()
            return []

        # 滚动加载更多推文
        for i in range(config.SCROLL_COUNT):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(config.SCROLL_DELAY_MS)
            logger.info("滚动 %d/%d", i + 1, config.SCROLL_COUNT)

        # 解析所有推文
        tweet_elements = page.query_selector_all(config.SELECTORS["tweet"])
        logger.info("找到 %d 个推文元素", len(tweet_elements))

        for el in tweet_elements:
            try:
                tweet = parse_tweet(el)
            except Exception as e:
                logger.warning("解析推文失败: %s", e)
                continue

            if not tweet:
                continue

            # 去重
            if tweet["tweet_id"] in index:
                continue

            new_tweets.append(tweet)
            index[tweet["tweet_id"]] = {
                "handle": tweet["handle"],
                "posted_at": tweet["posted_at"],
                "scraped_at": tweet["scraped_at"],
            }

        context.close()

    logger.info("新推文: %d 条", len(new_tweets))

    if dry_run:
        logger.info("dry-run 模式，不保存")
        return new_tweets

    # 追加到当天 JSONL
    if new_tweets:
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl_path = os.path.join(config.TWEETS_DIR, f"{today}.jsonl")
        with open(jsonl_path, "a", encoding="utf-8") as f:
            for t in new_tweets:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        logger.info("已写入 %s", jsonl_path)

        save_index(config.INDEX_FILE, index)
        logger.info("索引已更新 (%d 条)", len(index))

    return new_tweets


# ── CLI ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Twitter List 抓取器")
    parser.add_argument("--login", action="store_true", help="有头浏览器模式，用于首次登录")
    parser.add_argument("--dry-run", action="store_true", help="只抓取不保存")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    headless = not args.login
    tweets = scrape(headless=headless, dry_run=args.dry_run)

    if tweets:
        print(f"\n抓到 {len(tweets)} 条新推文:")
        for t in tweets[:5]:
            print(f"  @{t['handle']}: {t['text'][:80]}...")
        if len(tweets) > 5:
            print(f"  ... 还有 {len(tweets) - 5} 条")
    else:
        print("没有新推文")


if __name__ == "__main__":
    main()
