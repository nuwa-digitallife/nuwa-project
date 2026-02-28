#!/usr/bin/env python3
"""
降临派手记 · 素材深度采集

把 topic_pipeline.py 产出的浅层素材（RSS 摘要、标题列表）升级为写作级素材：
- 多路 web search（中+英），覆盖不同视角
- 一手源追溯（论文、官方博客、GitHub）
- 交叉验证关键数据点
- 输出结构化素材库到选题目录

在 run_pipeline.sh 中位于 Phase 1（选题推荐）和 Phase 2（多Agent写作）之间。
也可独立使用：手动选题后直接跑素材采集。

使用：
  python deep_research.py --topic-dir wechat/公众号选题/2026-02-25|xxx
  python deep_research.py --topic-dir ... --topic "Anthropic蒸馏门调查"
  python deep_research.py --topic-dir ... --effort medium --model sonnet
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # nuwa-project/
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
CONFIG_FILE = Path(__file__).resolve().parent.parent / "topic_config.yaml"

# 默认值（被 topic_config.yaml models.deep_research 覆盖）
DEFAULT_MODEL = "opus"
DEFAULT_EFFORT = "high"
DEFAULT_TOOLS = "WebSearch,WebFetch,Read"
DEFAULT_TIMEOUT = 900


def _load_model_config():
    global DEFAULT_MODEL, DEFAULT_EFFORT, DEFAULT_TOOLS, DEFAULT_TIMEOUT
    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        dr = config.get("models", {}).get("deep_research", {})
        if dr.get("model"):
            DEFAULT_MODEL = dr["model"]
        if dr.get("effort"):
            DEFAULT_EFFORT = dr["effort"]
        if dr.get("tools"):
            DEFAULT_TOOLS = dr["tools"]
        if dr.get("timeout"):
            DEFAULT_TIMEOUT = dr["timeout"]
    except Exception:
        pass


_load_model_config()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("deep_research")


def load_existing_materials(topic_dir: Path) -> str:
    """读取选题目录下已有的浅层素材（topic_pipeline.py 产出的）。"""
    result = []
    for md_file in sorted(topic_dir.rglob("*.md")):
        # 跳过输出文件
        if md_file.name.startswith("article") or md_file.name in (
            "poll.md", "publish_guide.md", "review_report.md",
            "factcheck_report.md", "research_materials.md",
        ):
            continue
        content = md_file.read_text(encoding="utf-8")
        if content.strip():
            result.append(f"--- {md_file.relative_to(topic_dir)} ---\n{content}")
    return "\n\n".join(result) if result else ""


def infer_topic_from_dir(topic_dir: Path) -> str:
    """从目录名推断选题主题。格式：YYYY-MM-DD|主题名"""
    name = topic_dir.name
    if "|" in name:
        return name.split("|", 1)[1]
    return name


def build_research_prompt(topic: str, existing_materials: str) -> str:
    """构造深度采集的 prompt。"""
    return f"""你是降临派手记的素材采集系统。你的任务是为一篇公众号深度分析文章采集高质量素材。

## 选题
{topic}

## 已有浅层素材（RSS 摘要等）
{existing_materials if existing_materials else "（无已有素材，从零开始搜索）"}

## 采集要求

### 搜索策略
1. **中文搜索**（3-5 轮）：用不同角度的关键词搜索
   - 事件本身：发生了什么、谁说了什么
   - 行业分析：36氪/虎嗅/量子位/机器之心等媒体怎么看
   - 社区讨论：知乎/V2EX/即刻上的争议观点
2. **英文搜索**（3-5 轮）：
   - 一手源：官方博客、论文（arXiv）、GitHub
   - 权威媒体：TechCrunch/The Verge/Bloomberg/Reuters
   - 社区：Hacker News/Reddit 上的讨论
3. **数据搜索**（1-3 轮）：
   - 融资数据、营收数据、市场份额
   - 产品参数、技术指标
   - 时间线和关键日期

### 一手源追溯原则
- 看到"据报道某公司做了X" → 搜该公司官方公告
- 看到"某论文提出了Y" → 搜 arXiv 原文
- 看到"某人说了Z" → 搜原始采访/推文
- **不以媒体二手信息为最终素材**——媒体报道用来发现线索，一手源才是素材

### 交叉验证
- 关键数字（金额、日期、参数）至少找 2 个独立来源
- 发现来源之间有冲突时，标注冲突点

## 输出格式

输出一个结构化的素材报告，直接作为写作Agent的输入：

# 素材报告：{topic}
采集时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}

## 核心事实（已验证）
（每条事实标注 1-2 个信源URL）

## 关键人物/公司
（涉及的主要人物和公司，每个附带关键数据点）

## 时间线
（关键事件按时间排序，精确到天）

## 多方观点
（不同立场的观点汇总：官方/支持方/反对方/中立分析）

## 数据表
（关键数字汇总：金额/参数/市场数据等，每个标注信源）

## 争议点和未解问题
（有分歧的事实、未经验证的传言、值得深挖的线索）

## 一手源清单
（论文/官方博客/GitHub/原始采访等一手源URL列表）

## 潜在配图素材
（截图/数据图/对比图的建议，标注来源URL）
"""


def run_research(topic_dir: Path, topic: str = None, model: str = DEFAULT_MODEL,
                 effort: str = DEFAULT_EFFORT) -> bool:
    """执行深度素材采集。"""
    topic_dir = Path(topic_dir).resolve()
    if not topic_dir.exists():
        log.error(f"选题目录不存在: {topic_dir}")
        return False

    # 推断主题
    if not topic:
        topic = infer_topic_from_dir(topic_dir)
    log.info(f"深度采集启动: {topic}")
    log.info(f"  目录: {topic_dir}")
    log.info(f"  模型: {model}, effort: {effort}")

    # 读取已有素材
    existing = load_existing_materials(topic_dir)
    if existing:
        log.info(f"  已有浅层素材: {len(existing)} chars")
    else:
        log.info("  无已有素材，从零搜索")

    # 构造 prompt
    prompt = build_research_prompt(topic, existing)
    log.info(f"  Prompt 长度: {len(prompt)} chars")

    # 调用 claude -p（带限流重试）
    from engine import run_claude_with_retry

    cmd = [
        "claude", "-p",
        "--model", model,
        "--allowedTools", DEFAULT_TOOLS,
        "--effort", effort,
        "--no-session-persistence",
    ]

    log.info("  调用 claude -p 开始深度搜索...")
    result = run_claude_with_retry(cmd, prompt, DEFAULT_TIMEOUT, logger=log)

    if result is None:
        return False

    if result.returncode != 0:
        log.error(f"  失败 (exit={result.returncode})")
        log.error(f"  stderr: {result.stderr[:500]}")
        return False

    output = result.stdout.strip()
    if not output:
        log.error("  无输出")
        return False

    # 保存素材报告
    materials_dir = topic_dir / "素材"
    materials_dir.mkdir(exist_ok=True)

    output_path = materials_dir / "deep_research.md"
    output_path.write_text(output, encoding="utf-8")
    log.info(f"  ✅ 素材报告已保存: {output_path} ({len(output)} chars)")

    # 统计素材质量指标
    url_count = output.count("http")
    section_count = output.count("## ")
    log.info(f"  URL 数量: {url_count}, 章节数: {section_count}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="降临派手记 · 素材深度采集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 对已有选题目录做深度采集
  python deep_research.py --topic-dir wechat/公众号选题/2026-02-25|Anthropic蒸馏门

  # 手动指定选题主题
  python deep_research.py --topic-dir /tmp/test_topic --topic "中美AI竞争2026"

  # 快速测试（sonnet + medium effort）
  python deep_research.py --topic-dir ... --model sonnet --effort medium
        """,
    )
    parser.add_argument("--topic-dir", required=True, help="选题目录路径")
    parser.add_argument("--topic", default=None, help="选题主题（不指定则从目录名推断）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default=DEFAULT_EFFORT,
                        help=f"推理 effort 级别 (默认: {DEFAULT_EFFORT})")

    args = parser.parse_args()
    success = run_research(
        topic_dir=args.topic_dir,
        topic=args.topic,
        model=args.model,
        effort=args.effort,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
