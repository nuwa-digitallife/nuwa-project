#!/usr/bin/env python3
"""
降临派手记 · 自动选题流水线

Phase 1: 素材搜集
  - 中文源：exporter API → 关注公众号最近 N 天文章 → 按偏好关键词匹配
  - 英文源：Google News RSS → 按偏好关键词搜索

Phase 2: 选题推荐
  - 按 heat/timeliness/uniqueness/depth 加权打分
  - 输出 top-N 选题 + 素材摘要

使用：
  source ~/venv/automation/bin/activate
  python topic_pipeline.py                     # 默认：搜素材 + 推荐选题
  python topic_pipeline.py --search-only       # 只搜素材，不推荐
  python topic_pipeline.py --dry-run           # 不写文件，只打印结果
  python topic_pipeline.py --topic "世界模型"   # 手动指定选题搜索
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少 pyyaml: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

from material_collector import (
    check_exporter,
    collect_cn_materials,
    collect_en_materials,
    fetch_account_articles,
    get_auth_key,
    get_followed_accounts,
    match_article_to_topics,
    search_account,
    API_DELAY,
)
from topic_recommender import (
    recommend_topics,
    save_materials,
    save_recommendation_report,
)

# ── 路径配置 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # nuwa-project/
WECHAT_DIR = SCRIPT_DIR.parent           # wechat/
CONFIG_FILE = SCRIPT_DIR / "topic_config.yaml"
LOG_DIR = PROJECT_ROOT / "logs"
DEVLOG_FILE = LOG_DIR / "devlog.jsonl"

# ── 日志 ──────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def devlog(entry: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now().isoformat()
    entry["project"] = "wechat-pipeline"
    with open(DEVLOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── 配置加载 ──────────────────────────────────────────────
def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 手动选题搜索 ──────────────────────────────────────────
def manual_topic_search(topic: str, config: dict):
    """手动指定选题，搜索中英文素材"""
    log(f"手动选题: {topic}")

    manual_topic = {
        "name": topic,
        "keywords_cn": [topic],
        "keywords_en": [topic],
        "priority": 0,
    }

    # 搜索中文
    cn_articles = {}
    if check_exporter():
        try:
            auth_key = get_auth_key()
            lookback_days = config["search"]["lookback_days"]
            cutoff_ts = int((datetime.now() - timedelta(days=lookback_days)).timestamp())
            followed = get_followed_accounts()

            matched = []
            for name in followed:
                account = search_account(auth_key, name)
                time.sleep(API_DELAY)
                if not account:
                    continue

                articles = fetch_account_articles(auth_key, account["fakeid"], cutoff_ts)
                for a in articles:
                    a["nickname"] = account["nickname"]
                    a["source_type"] = "wechat"
                    if match_article_to_topics(a, [manual_topic]):
                        matched.append(a)
                time.sleep(API_DELAY)

            cn_articles[topic] = matched[:config["search"]["max_articles_per_topic"]]
            log(f"  中文匹配: {len(cn_articles[topic])} 篇")
        except Exception as e:
            log(f"  中文搜索失败: {e}")

    # 搜索英文
    from material_collector import search_google_news_rss
    en_results = search_google_news_rss(topic, max_results=config["search"]["max_articles_per_topic"])
    en_articles = {topic: en_results}
    log(f"  英文匹配: {len(en_results)} 篇")

    # 保存
    auth_key = None
    try:
        auth_key = get_auth_key()
    except Exception:
        pass
    save_materials(topic, cn_articles.get(topic, []), en_articles.get(topic, []),
                   config, PROJECT_ROOT, auth_key)


# ── 主流程 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="降临派手记 · 自动选题流水线")
    parser.add_argument("--search-only", action="store_true", help="只搜素材，不推荐")
    parser.add_argument("--dry-run", action="store_true", help="不写文件，只打印")
    parser.add_argument("--topic", "-t", type=str, help="手动指定选题搜索")
    parser.add_argument("--cn-only", action="store_true", help="只搜中文源")
    parser.add_argument("--en-only", action="store_true", help="只搜英文源")
    parser.add_argument("--num-topics", "-n", type=int, help="推荐选题数量（覆盖配置文件）")
    args = parser.parse_args()

    config = load_config()
    log("=" * 50)
    log("降临派手记 · 选题流水线启动")
    log("=" * 50)

    # 手动选题
    if args.topic:
        manual_topic_search(args.topic, config)
        return

    # 自动模式
    cn_materials = {}
    en_materials = {}

    if not args.en_only:
        cn_materials = collect_cn_materials(config)

    if not args.cn_only:
        en_materials = collect_en_materials(config)

    if not cn_materials and not en_materials:
        log("⚠ 没有搜集到任何素材")
        devlog({
            "type": "issue",
            "context": "选题流水线",
            "action": "搜索返回空",
            "result": f"cn={bool(cn_materials)}, en={bool(en_materials)}",
            "insight": "检查 exporter 是否运行 + 网络是否可达",
        })
        return

    if args.dry_run:
        log("\n[DRY RUN] 素材概览:")
        for name in set(list(cn_materials.keys()) + list(en_materials.keys())):
            cn = cn_materials.get(name, [])
            en = en_materials.get(name, [])
            log(f"  {name}: {len(cn)} 中文 + {len(en)} 英文")
        return

    # 保存素材
    auth_key = None
    try:
        auth_key = get_auth_key()
    except Exception:
        pass

    all_topic_names = set(list(cn_materials.keys()) + list(en_materials.keys()))
    for topic_name in all_topic_names:
        cn = cn_materials.get(topic_name, [])
        en = en_materials.get(topic_name, [])
        save_materials(topic_name, cn, en, config, PROJECT_ROOT, auth_key)

    # 推荐选题
    if not args.search_only:
        # --num-topics 覆盖配置文件
        if args.num_topics:
            config.setdefault("recommendation", {})["num_topics"] = args.num_topics
        recommendations = recommend_topics(cn_materials, en_materials, config, WECHAT_DIR)
        report_path = save_recommendation_report(recommendations, config, PROJECT_ROOT)

        log("\n" + "=" * 50)
        log("选题推荐结果:")
        log("=" * 50)
        for i, rec in enumerate(recommendations, 1):
            log(f"  {i}. [{rec['score']}] {rec['name']} ({rec['cn_count']}中+{rec['en_count']}英)")

        devlog({
            "type": "task",
            "context": "选题流水线",
            "action": f"自动推荐 {len(recommendations)} 个选题",
            "result": ", ".join(r["name"] for r in recommendations),
        })


if __name__ == "__main__":
    main()
