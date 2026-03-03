#!/usr/bin/env python3
"""
批量拉取指定公众号最近 20 篇文章的标题+摘要+链接，输出 JSON。
用法: source ~/venv/automation/bin/activate && python scripts/fetch_account_articles.py
"""
import json
import sys
import time
from pathlib import Path

# 复用 auto_import 的基础设施
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "knowledgebase" / "wx-article-cron"))
from auto_import import get_auth_key, search_account, _api_get, EXPORTER_BASE

TARGET_ACCOUNTS = [
    "探索AGI",
    "InfoQ",
    "量子位",
    "财经杂志",
    "AI信息Gap",
    "馒头商学",
    "机器之心",
    "虎嗅APP",
    "AI前线",
    "51CTO技术栈",
    "孔某人的低维认知",
]

def fetch_recent_articles(auth_key: str, fakeid: str, count: int = 20) -> list[dict]:
    """拉取最近 count 篇文章的标题、摘要、链接、时间"""
    url = f"{EXPORTER_BASE}/api/web/mp/appmsgpublish"
    headers = {"X-Auth-Key": auth_key}
    articles = []
    begin = 0
    size = 10

    while len(articles) < count:
        params = {"id": fakeid, "begin": begin, "size": size}
        try:
            r = _api_get(url, params=params, headers=headers, timeout=15)
            data = r.json()
        except Exception as e:
            print(f"    page {begin // size + 1} 失败: {e}", file=sys.stderr)
            break

        publish_page_raw = data.get("publish_page", "")
        if not publish_page_raw:
            break

        try:
            publish_page = json.loads(publish_page_raw) if isinstance(publish_page_raw, str) else publish_page_raw
        except json.JSONDecodeError:
            break

        publish_list = publish_page.get("publish_list", [])
        if not publish_list:
            break

        for batch in publish_list:
            pub_info_raw = batch.get("publish_info", "")
            try:
                pub_info = json.loads(pub_info_raw) if isinstance(pub_info_raw, str) else pub_info_raw
            except (json.JSONDecodeError, TypeError):
                continue

            for item in pub_info.get("appmsgex", []):
                articles.append({
                    "title": item.get("title", ""),
                    "digest": item.get("digest", ""),
                    "link": item.get("link", ""),
                    "create_time": item.get("create_time", 0),
                })
                if len(articles) >= count:
                    break
            if len(articles) >= count:
                break

        begin += size
        time.sleep(1.5)

    return articles[:count]


def main():
    auth_key = get_auth_key()
    print(f"Auth key 获取成功", file=sys.stderr)

    result = {}
    for name in TARGET_ACCOUNTS:
        print(f"搜索: {name}...", file=sys.stderr)
        account = search_account(auth_key, name)
        if not account:
            print(f"  未找到: {name}", file=sys.stderr)
            result[name] = {"error": "未找到", "articles": []}
            time.sleep(1.5)
            continue

        print(f"  找到: {account['nickname']} (fakeid={account['fakeid']})", file=sys.stderr)
        time.sleep(1.5)

        articles = fetch_recent_articles(auth_key, account["fakeid"], count=20)
        print(f"  拉取到 {len(articles)} 篇文章", file=sys.stderr)
        result[account["nickname"]] = {
            "fakeid": account["fakeid"],
            "articles": articles,
        }
        time.sleep(1.5)

    # 输出 JSON
    output_path = Path(__file__).resolve().parent.parent / "wechat" / "account_analysis_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n输出到: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
