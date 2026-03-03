"""热点检测 + 信号生成

规则驱动，不用 LLM：
- URL 聚合：多个 KOL 分享同一链接 → 强信号
- 关键词聚合：@mentions、#hashtags、产品名跨 handle 统计
- 互动加权：likes/retweets 高的权重更大
"""
import json
import logging
import os
import re
from collections import defaultdict
from datetime import datetime

import config

logger = logging.getLogger("analyzer")


def load_today_tweets(date_str: str | None = None) -> list[dict]:
    """加载当天所有推文"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    jsonl_path = os.path.join(config.TWEETS_DIR, f"{date_str}.jsonl")
    if not os.path.exists(jsonl_path):
        logger.warning("未找到当天推文文件: %s", jsonl_path)
        return []
    tweets = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tweets.append(json.loads(line))
    return tweets


def _engagement_score(metrics: dict) -> float:
    """计算互动分数"""
    return (
        metrics.get("likes", 0)
        + metrics.get("retweets", 0) * 2
        + metrics.get("replies", 0) * 1.5
    )


def _extract_keywords(text: str) -> list[str]:
    """提取 @mentions、#hashtags 和潜在产品名"""
    keywords = []
    # @mentions
    keywords.extend(re.findall(r"@(\w+)", text))
    # #hashtags
    keywords.extend(re.findall(r"#(\w+)", text))
    # 大写开头的连续词（可能是产品名/项目名）
    keywords.extend(re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)?)\b", text))
    return [k.lower() for k in keywords]


def detect_hot_topics(tweets: list[dict]) -> list[dict]:
    """检测热点话题

    策略：
    1. URL 聚合 — 多个 handle 分享同一 URL
    2. 关键词聚合 — 跨 handle 出现的关键词
    """
    if not tweets:
        return []

    # ── URL 聚合 ──
    url_map: dict[str, dict] = defaultdict(lambda: {
        "handles": set(),
        "tweet_urls": [],
        "total_engagement": 0,
    })

    for t in tweets:
        for link in t.get("links", []):
            # 跳过 twitter 自身链接
            if "x.com" in link or "twitter.com" in link:
                continue
            # 标准化 URL（去掉 trailing slash 和 query params 的常见追踪参数）
            clean_url = link.split("?utm_")[0].rstrip("/")
            entry = url_map[clean_url]
            entry["handles"].add(t["handle"])
            entry["tweet_urls"].append(t["url"])
            entry["total_engagement"] += _engagement_score(t.get("metrics", {}))

    # ── 关键词聚合 ──
    keyword_map: dict[str, dict] = defaultdict(lambda: {
        "handles": set(),
        "tweet_urls": [],
        "total_engagement": 0,
        "source_urls": [],
    })

    for t in tweets:
        keywords = _extract_keywords(t.get("text", ""))
        for kw in set(keywords):  # 同一推文去重
            entry = keyword_map[kw]
            entry["handles"].add(t["handle"])
            entry["tweet_urls"].append(t["url"])
            entry["total_engagement"] += _engagement_score(t.get("metrics", {}))
            entry["source_urls"].extend(t.get("links", []))

    # ── 合并成热点 ──
    hot_topics = []
    seen_handles_combo = set()  # 避免 URL 和关键词产生完全重复的话题

    # URL 热点（优先级最高）
    for url, data in url_map.items():
        if len(data["handles"]) >= config.HOT_TOPIC_MIN_HANDLES:
            handles_key = frozenset(data["handles"])
            seen_handles_combo.add(handles_key)
            hot_topics.append({
                "topic": url,
                "type": "shared_url",
                "score": len(data["handles"]) * 2 + int(data["total_engagement"] * config.ENGAGEMENT_WEIGHT),
                "handles": sorted(data["handles"]),
                "source_urls": [url],
                "tweet_urls": data["tweet_urls"],
                "total_engagement": int(data["total_engagement"]),
                "suggested_angle": "hot_take",
            })

    # 关键词热点
    for kw, data in keyword_map.items():
        if len(data["handles"]) >= config.HOT_TOPIC_MIN_HANDLES:
            handles_key = frozenset(data["handles"])
            if handles_key in seen_handles_combo:
                continue  # 跳过与 URL 热点重复的
            # 过滤太泛的关键词
            if len(kw) < 3 or kw in {"the", "and", "for", "this", "that", "with"}:
                continue
            hot_topics.append({
                "topic": kw,
                "type": "keyword_cluster",
                "score": len(data["handles"]) + int(data["total_engagement"] * config.ENGAGEMENT_WEIGHT),
                "handles": sorted(data["handles"]),
                "source_urls": list(set(data["source_urls"]))[:5],
                "tweet_urls": data["tweet_urls"],
                "total_engagement": int(data["total_engagement"]),
                "suggested_angle": "explainer" if len(data["handles"]) >= 5 else "hot_take",
            })

    # 按 score 降序
    hot_topics.sort(key=lambda x: x["score"], reverse=True)
    return hot_topics


def analyze(date_str: str | None = None) -> dict:
    """完整分析流程，输出信号文件

    Returns:
        信号 dict
    """
    tweets = load_today_tweets(date_str)
    hot_topics = detect_hot_topics(tweets)

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    signal = {
        "generated_at": datetime.now().isoformat(),
        "date": date_str,
        "hot_topics": hot_topics,
        "stats": {
            "total_tweets_today": len(tweets),
            "unique_handles": len(set(t["handle"] for t in tweets)),
            "hot_topics_flagged": len(hot_topics),
        },
    }

    # 写入信号文件
    os.makedirs(config.SIGNALS_DIR, exist_ok=True)
    signal_path = os.path.join(config.SIGNALS_DIR, f"{date_str}.json")
    with open(signal_path, "w", encoding="utf-8") as f:
        json.dump(signal, f, ensure_ascii=False, indent=2)
    logger.info("信号已写入 %s", signal_path)

    return signal


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Twitter 热点检测")
    parser.add_argument("--date", help="分析指定日期 (YYYY-MM-DD)，默认今天")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    signal = analyze(date_str=args.date)

    print(f"\n=== 热点检测结果 ({signal['date']}) ===")
    print(f"推文总数: {signal['stats']['total_tweets_today']}")
    print(f"涉及 KOL: {signal['stats']['unique_handles']}")
    print(f"热点话题: {signal['stats']['hot_topics_flagged']}")

    if signal["hot_topics"]:
        print("\n热点:")
        for i, topic in enumerate(signal["hot_topics"], 1):
            print(f"  {i}. [{topic['type']}] {topic['topic']}")
            print(f"     score={topic['score']} handles={topic['handles']}")
    else:
        print("\n未检测到热点话题")


if __name__ == "__main__":
    main()
