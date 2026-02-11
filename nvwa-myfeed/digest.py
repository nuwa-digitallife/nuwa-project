#!/usr/bin/env python3
"""推特AI大V每日摘要生成器

抓取AI领域KOL的每日推文，用Claude生成中文摘要。
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_HANDLES = [
    "elonmusk",        # Elon Musk
    "demaborsa",       # Demis Hassabis
    "DarioAmodei",     # Dario Amodei
    "ylecun",          # Yann LeCun
    "DrJimFan",        # Jim Fan (NVIDIA)
    "AndrewYNg",       # Andrew Ng
    "sama",            # Sam Altman
    "GaryMarcus",      # Gary Marcus
    "fchollet",        # François Chollet (Keras)
    "hardmaru",        # David Ha
    "ClementDelangue", # Clement Delangue (HuggingFace)
    "JeffDean",        # Jeff Dean (Google)
    "svpino",          # Santiago Valdarrama
    "kaborosx",        # Andrej Karpathy
    "EMostaque",       # Emad Mostaque (Stability AI)
]

XAI_API_URL = "https://api.x.ai/v1/responses"
GROK_MODEL = "grok-4-1-fast"


def fetch_tweets_for_handle(handle: str, from_date: str, to_date: str, api_key: str) -> dict:
    """用 Grok x_search 抓取单个账号的推文。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROK_MODEL,
        "tools": [
            {
                "type": "x_search",
                "allowed_x_handles": [handle],
                "from_date": from_date,
                "to_date": to_date,
            }
        ],
        "input": [
            {
                "role": "user",
                "content": (
                    f"List ALL tweets posted by @{handle} in the given time range. "
                    "For each tweet, include:\n"
                    "1. The full original text\n"
                    "2. The posting time\n"
                    "3. The tweet URL\n"
                    "If there are no tweets, say 'No tweets found'."
                ),
            }
        ],
    }
    resp = requests.post(XAI_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def extract_grok_text(response: dict) -> str:
    """从 Grok API 响应中提取文本内容。"""
    # The response format follows OpenAI-compatible structure
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        pass
    # Try alternative response format
    try:
        output = response.get("output", [])
        texts = []
        for item in output:
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "text":
                        texts.append(content["text"])
        if texts:
            return "\n".join(texts)
    except (KeyError, TypeError):
        pass
    return json.dumps(response, ensure_ascii=False)


def fetch_all_tweets(handles: list[str], api_key: str) -> dict[str, str]:
    """抓取所有账号的推文，返回 {handle: 推文文本}。"""
    now = datetime.now(timezone.utc)
    to_date = now.strftime("%Y-%m-%d")
    from_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    results = {}
    for handle in handles:
        print(f"  抓取 @{handle} ...", end=" ", flush=True)
        try:
            resp = fetch_tweets_for_handle(handle, from_date, to_date, api_key)
            text = extract_grok_text(resp)
            results[handle] = text
            print("OK")
        except requests.RequestException as e:
            print(f"失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"    响应: {e.response.text[:500]}")
            results[handle] = f"[抓取失败: {e}]"
    return results


def generate_summary(tweets_by_handle: dict[str, str]) -> str:
    """用本地 Claude Code 生成中文摘要。"""
    # 组装推文内容
    parts = []
    for handle, text in tweets_by_handle.items():
        parts.append(f"=== @{handle} ===\n{text}")
    all_tweets = "\n\n".join(parts)

    prompt = """你是一个AI领域的资深分析师。以下是多个AI领域KOL今天的推文原文。

请你完成以下任务：
1. 过滤掉与AI/技术无关的内容（如个人生活、政治等）
2. 生成一份中文摘要报告

输出格式（使用Markdown）：

## 今日一句话

（用一句话总结今天AI圈最值得关注的动态）

## 重要事件

（按重要程度排序，每条包含：简要中文描述 + 原推链接。如果推文中包含URL则附上）

- **事件标题**：描述内容。([来源](推文URL))

## 值得关注的信号

（1-3条你认为值得深入跟踪的趋势或信号，简要说明原因）

注意：
- 如果某个KOL今天没有AI相关推文，跳过即可，不需要提及
- 保留关键英文术语，不强行翻译（如 transformer, RLHF, agent 等）
- 如果所有推文都没有AI相关内容，直接说"今天没有值得关注的AI动态"

--- 以下是今天各AI KOL的推文 ---

""" + all_tweets

    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"Claude Code 调用失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def extract_one_liner(summary: str) -> str:
    """从摘要中提取'今日一句话'内容。"""
    lines = summary.split("\n")
    for i, line in enumerate(lines):
        if "今日一句话" in line:
            # 取该标题之后的第一个非空行
            for next_line in lines[i + 1:]:
                stripped = next_line.strip()
                if stripped:
                    return stripped
    return ""


def write_output(summary: str, output_dir: str) -> str:
    """写入 markdown 文件（含 YAML frontmatter），返回文件路径。"""
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    filepath = os.path.join(output_dir, f"{today}.md")

    one_liner = extract_one_liner(summary)

    header = f"""---
title: "AI 推特日报 {today}"
date: "{today}"
generated: "{now_str}"
summary: "{one_liner}"
---

# AI 推特日报 {today}

> 自动生成于 {now_str}
> 数据来源：xAI Grok x_search → Claude 摘要

---

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + summary + "\n")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="推特AI大V每日摘要生成器")
    parser.add_argument(
        "--handles",
        nargs="+",
        default=DEFAULT_HANDLES,
        help="要抓取的推特账号列表（不含@）",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
        help="输出目录（默认: ./output/）",
    )
    args = parser.parse_args()

    xai_key = os.environ.get("XAI_API_KEY")

    if not xai_key:
        print("错误: 请设置 XAI_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)

    print(f"[1/3] 抓取推文 ({len(args.handles)} 个账号)...")
    tweets = fetch_all_tweets(args.handles, xai_key)

    print("[2/3] 用 Claude Code 生成摘要...")
    summary = generate_summary(tweets)

    print("[3/3] 写入文件...")
    filepath = write_output(summary, args.output_dir)

    print(f"\n完成! 摘要已保存到: {filepath}")


if __name__ == "__main__":
    main()
