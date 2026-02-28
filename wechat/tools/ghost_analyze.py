#!/usr/bin/env python3
"""
幽灵分析器 — 能力缺口分析 Demo

给定一个事件，分析：
1. 信息传播时间轴（最早报道 → 传播路径 → 各方回应）
2. 现有监控能力是否能捕获
3. 缺口在哪里
4. 生成能力提案

使用:
  python ghost_analyze.py --event "Anthropic CEO 因五角大楼安全问题与特朗普公开争执"
  python ghost_analyze.py --event "..." --output-dir /tmp/ghost_demo
  python ghost_analyze.py --event "..." --verbose
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # nuwa-project/
CONFIG_FILE = SCRIPT_DIR / "topic_config.yaml"
PROMPTS_DIR = SCRIPT_DIR / "write_engine" / "prompts"
LOG_DIR = PROJECT_ROOT / "logs"
DEVLOG_FILE = LOG_DIR / "devlog.jsonl"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def devlog(entry: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now().isoformat()
    entry["project"] = "ghost"
    with open(DEVLOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_current_capabilities() -> dict:
    """加载当前监控能力配置"""
    capabilities = {
        "auto_topics": [],
        "cn_sources": [],
        "en_domains": [],
        "special_sources": [],
    }

    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 偏好话题
        for topic in config.get("auto_topics", []):
            capabilities["auto_topics"].append({
                "name": topic["name"],
                "keywords_cn": topic.get("keywords_cn", []),
                "keywords_en": topic.get("keywords_en", []),
            })
            if "special_sources" in topic:
                capabilities["special_sources"].extend(topic["special_sources"])

        # 英文域名
        capabilities["en_domains"] = config.get("search", {}).get("en_domains", [])

    except Exception as e:
        log(f"WARNING: 加载配置失败: {e}")

    # 中文源（公众号列表）
    try:
        import requests
        resp = requests.get("http://localhost:3000/api/public/v1/followed-accounts", timeout=5)
        if resp.status_code == 200:
            accounts = resp.json()
            capabilities["cn_sources"] = [a.get("name", "") for a in accounts if a.get("name")]
    except Exception:
        log("WARNING: 无法获取公众号列表（exporter 未运行？）")

    return capabilities


def run_event_trace(event: str, output_dir: Path) -> str:
    """Step 1: 事件溯源 — 搜索时间线"""
    log("Step 1: 事件溯源...")

    prompt_file = PROMPTS_DIR / "ghost_gap_analysis.md"
    if prompt_file.exists():
        base_prompt = prompt_file.read_text(encoding="utf-8")
    else:
        base_prompt = ""

    prompt = f"""{base_prompt}

# 任务：事件溯源

请对以下事件进行详细的信息溯源分析：

**事件**: {event}

## 要求

1. **时间线追溯**：
   - 最早的信息源是什么？（社交媒体帖子？新闻稿？内部爆料？）
   - 精确到小时的传播时间线
   - 各个信息节点：谁最先报道？谁跟进？

2. **传播路径**：
   - 一手源 → 二手源 → 中文媒体 的传播链
   - 每个节点的时间延迟

3. **各方回应**：
   - 事件相关方的官方回应
   - 关键人物的立场

请用结构化格式输出，包含具体URL和时间戳。
"""

    proc = subprocess.run(
        ["claude", "-p", prompt, "--allowedTools", "WebSearch,WebFetch"],
        capture_output=True, text=True, timeout=600,
    )

    trace = proc.stdout.strip() if proc.returncode == 0 else f"溯源失败: {proc.stderr[:200]}"

    trace_file = output_dir / "01_event_trace.md"
    trace_file.write_text(f"# 事件溯源\n\n事件: {event}\n分析时间: {datetime.now().isoformat()}\n\n---\n\n{trace}", encoding="utf-8")
    log(f"Trace saved: {trace_file}")
    return trace


def run_capability_check(event: str, trace: str, capabilities: dict, output_dir: Path) -> str:
    """Step 2: 对照现有监控能力"""
    log("Step 2: 能力对照...")

    cap_summary = json.dumps(capabilities, ensure_ascii=False, indent=2)

    prompt = f"""# 任务：监控能力对照分析

## 事件
{event}

## 事件溯源结果
{trace[:3000]}

## 当前监控能力
```json
{cap_summary}
```

## 要求

对照事件溯源结果和当前监控能力，逐项分析：

1. **理论覆盖**：
   - 哪些信息源在我们的监控范围内？
   - 这些源理论上能在事件发生后多久捕获？

2. **实际缺口**：
   - 最早的一手源是什么？我们能捕获吗？
   - 如果不能，差在哪里？（缺少哪类信源？）
   - 从一手源到我们能捕获的最早源之间，延迟多久？

3. **关键词覆盖**：
   - 现有关键词能匹配这个事件吗？
   - 需要补充什么关键词？

输出结构化分析，用表格对比「能力」vs「需求」。
"""

    proc = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=300,
    )

    check = proc.stdout.strip() if proc.returncode == 0 else "能力对照失败"

    check_file = output_dir / "02_capability_check.md"
    check_file.write_text(f"# 能力对照分析\n\n---\n\n{check}", encoding="utf-8")
    log(f"Check saved: {check_file}")
    return check


def run_gap_proposal(event: str, trace: str, check: str, output_dir: Path) -> str:
    """Step 3: 生成能力提案"""
    log("Step 3: 生成能力提案...")

    prompt = f"""# 任务：能力缺口提案

基于以下分析，生成具体的能力提案：

## 事件
{event}

## 能力对照结果
{check[:3000]}

## 要求

为每个识别出的缺口，生成一个具体的能力提案。格式：

```markdown
# 能力提案: {{名称}}

## 缺口描述
{{一句话描述缺什么}}

## 方案
- 实现方式: {{具体技术方案}}
- 文件名: {{建议的 Python 文件名}}
- 关键配置: {{需要的 API key / 配置}}

## 监控目标
- 关键人物: {{需要关注的人/账号}}
- 关键词: {{新增的搜索关键词}}
- 数据源: {{具体的数据源 URL/API}}

## 预期效果
- 延迟改善: {{从 X 小时 → Y 小时/分钟}}
- 覆盖范围: {{新增覆盖的事件类型}}

## 实施难度
- 难度: {{低/中/高}}
- 依赖: {{需要的外部服务/API}}
- 预计工时: {{大致工时}}
```

每个提案独立，可以直接作为开发任务。
"""

    proc = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=300,
    )

    proposal = proc.stdout.strip() if proc.returncode == 0 else "提案生成失败"

    proposal_file = output_dir / "03_gap_proposals.md"
    proposal_file.write_text(f"# 能力缺口提案\n\n事件: {event}\n生成时间: {datetime.now().isoformat()}\n\n---\n\n{proposal}", encoding="utf-8")
    log(f"Proposals saved: {proposal_file}")
    return proposal


def generate_summary(event: str, output_dir: Path):
    """生成汇总报告"""
    log("Generating summary...")

    files = sorted(output_dir.glob("*.md"))
    summary_parts = [f"# Ghost 分析报告\n\n**事件**: {event}\n**分析时间**: {datetime.now().isoformat()}\n"]

    for f in files:
        if f.name != "summary.md":
            summary_parts.append(f"\n---\n\n")
            summary_parts.append(f.read_text(encoding="utf-8"))

    summary = "\n".join(summary_parts)
    summary_file = output_dir / "summary.md"
    summary_file.write_text(summary, encoding="utf-8")
    log(f"Summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description="幽灵分析器 — 能力缺口分析")
    parser.add_argument("--event", "-e", required=True, help="事件描述")
    parser.add_argument("--output-dir", "-o", default="", help="输出目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--trace-only", action="store_true", help="只做事件溯源")
    args = parser.parse_args()

    # 输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        safe_name = args.event[:30].replace(" ", "_").replace("/", "_")
        output_dir = PROJECT_ROOT / "logs" / "ghost" / f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("Ghost 能力缺口分析器")
    log(f"事件: {args.event}")
    log(f"输出: {output_dir}")
    log("=" * 60)

    # Step 1: 事件溯源
    trace = run_event_trace(args.event, output_dir)

    if args.trace_only:
        log("Done (trace only)")
        return

    # Step 2: 对照能力
    capabilities = load_current_capabilities()
    check = run_capability_check(args.event, trace, capabilities, output_dir)

    # Step 3: 能力提案
    proposal = run_gap_proposal(args.event, trace, check, output_dir)

    # Summary
    generate_summary(args.event, output_dir)

    log(f"\n{'='*60}")
    log("Ghost 分析完成")
    log(f"输出目录: {output_dir}")
    log(f"{'='*60}")

    devlog({
        "type": "task",
        "context": "ghost_analyze.py",
        "action": f"能力缺口分析: {args.event[:40]}",
        "result": f"3 reports generated → {output_dir}",
    })


if __name__ == "__main__":
    main()
