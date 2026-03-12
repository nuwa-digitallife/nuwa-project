#!/usr/bin/env python3
"""
投稿状态汇总工具

读取 submissions.jsonl，打印汇总。

用法：
  python lit_status.py
"""

import json
from datetime import datetime
from pathlib import Path

SUBMISSIONS_FILE = Path(__file__).resolve().parent / "已投稿" / "submissions.jsonl"


def main():
    if not SUBMISSIONS_FILE.exists() or SUBMISSIONS_FILE.stat().st_size == 0:
        print("== 文学外包投稿状态 ==")
        print("暂无投稿记录。")
        return

    records = []
    for line in SUBMISSIONS_FILE.read_text().splitlines():
        if line.strip():
            records.append(json.loads(line))

    if not records:
        print("== 文学外包投稿状态 ==")
        print("暂无投稿记录。")
        return

    # 统计
    total = len(records)
    by_status = {}
    for r in records:
        s = r.get("status", "未知")
        by_status[s] = by_status.get(s, 0) + 1

    waiting = [r for r in records if r["status"] in ("已投", "草稿")]
    adopted = by_status.get("采用", 0)
    rejected = by_status.get("拒稿", 0)

    print("== 文学外包投稿状态 ==")
    print(f"总记录: {total} | 等待中: {len(waiting)} | 已采用: {adopted} | 已拒稿: {rejected}")

    status_display = " | ".join(f"{k}: {v}" for k, v in sorted(by_status.items()))
    print(f"详细: {status_display}")

    if waiting:
        print("\n等待结果：")
        now = datetime.now()
        for r in waiting:
            ts = datetime.fromisoformat(r["timestamp"])
            days = (now - ts).days
            print(f"  {r['id']} {r['work']} → {r['venue']}（{r['status']}，{days}天）")

    # 按作品汇总
    works = {}
    for r in records:
        w = r["work"]
        if w not in works:
            works[w] = []
        works[w].append(r)

    if len(works) > 1:
        print("\n按作品：")
        for w, rs in works.items():
            statuses = ", ".join(f"{r['venue']}({r['status']})" for r in rs)
            print(f"  {w}: {statuses}")


if __name__ == "__main__":
    main()
