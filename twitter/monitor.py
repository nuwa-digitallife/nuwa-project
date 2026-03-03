"""调度入口：scrape → analyze，支持 CLI 参数和日志。

用法:
    python monitor.py                 # 正常运行（抓取 + 分析）
    python monitor.py --login         # 首次登录（有头浏览器）
    python monitor.py --dry-run       # 只抓不存
    python monitor.py --scrape-only   # 只抓不分析
"""
import argparse
import logging
import os
import sys
from datetime import datetime

import config
from scraper import scrape
from analyzer import analyze


def setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(config.LOG_DIR, f"{today}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Twitter 采集调度器")
    parser.add_argument("--login", action="store_true", help="有头浏览器模式，用于首次登录")
    parser.add_argument("--dry-run", action="store_true", help="只抓取不保存")
    parser.add_argument("--scrape-only", action="store_true", help="只抓取不分析")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("monitor")

    start = datetime.now()
    logger.info("=== 开始采集 ===")

    # ── Step 1: Scrape ──
    headless = not args.login
    try:
        new_tweets = scrape(headless=headless, dry_run=args.dry_run)
        logger.info("抓取完成: %d 条新推文", len(new_tweets))
    except Exception as e:
        logger.exception("抓取失败: %s", e)
        sys.exit(1)

    # ── Step 2: Analyze ──
    if not args.scrape_only and not args.dry_run:
        try:
            signal = analyze()
            logger.info(
                "分析完成: %d 热点, %d 推文",
                signal["stats"]["hot_topics_flagged"],
                signal["stats"]["total_tweets_today"],
            )
        except Exception as e:
            logger.exception("分析失败: %s", e)
            # 分析失败不 exit，数据已保存

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("=== 完成 (%.1f秒) ===", elapsed)


if __name__ == "__main__":
    main()
