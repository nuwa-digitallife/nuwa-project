#!/usr/bin/env python3
"""
降临派手记 · 配图自动采集

处理文章中的 [配图：描述] 标记，自动采集/生成三类配图：
  1. 实物/场景图 — web search 下载（英文关键词，官方PR > 媒体 > 第三方）
  2. 数据图/信息图 — matplotlib 自制（PingFang HK，深色主题 #0a0e1a）
  3. AI生成图 — Gemini API (gen_image.py)，深空科技风

三类优先级：真实截图/新闻 > 自制数据图 > AI生成

内容方法论 140-157 行定义了配图规范，本模块是其自动化实现。

使用：
  python image_collector.py --topic-dir wechat/公众号选题/2026-02-25|xxx
  python image_collector.py --topic-dir ... --model sonnet --effort medium
"""

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # nuwa-project/
GEN_IMAGE_PATH = Path(__file__).resolve().parent / "gen_image.py"
CONFIG_FILE = Path(__file__).resolve().parent.parent / "topic_config.yaml"

# 默认值（被 topic_config.yaml models.image_collector 覆盖）
DEFAULT_MODEL = "opus"
DEFAULT_EFFORT = "high"
DEFAULT_TOOLS = "WebSearch,WebFetch,Bash,Read"
DEFAULT_TIMEOUT = 600


def _load_model_config():
    global DEFAULT_MODEL, DEFAULT_EFFORT, DEFAULT_TOOLS, DEFAULT_TIMEOUT
    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        ic = config.get("models", {}).get("image_collector", {})
        if ic.get("model"):
            DEFAULT_MODEL = ic["model"]
        if ic.get("effort"):
            DEFAULT_EFFORT = ic["effort"]
        if ic.get("tools"):
            DEFAULT_TOOLS = ic["tools"]
        if ic.get("timeout"):
            DEFAULT_TIMEOUT = ic["timeout"]
    except Exception:
        pass


_load_model_config()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("image_collector")


# ── 标记解析 ──────────────────────────────────────────

def parse_image_markers(article_text: str) -> list[dict]:
    """
    解析文章中的 [配图：描述] 标记。

    Returns:
        list of dicts: {"index": int, "description": str, "position": str}
        position 是标记周围的上下文（前后各 2 行）
    """
    markers = []
    lines = article_text.split("\n")

    for i, line in enumerate(lines):
        # 匹配 [配图：xxx] 或 [配图:xxx]
        matches = re.findall(r'\[配图[：:]\s*(.+?)\]', line)
        for desc in matches:
            # 提取上下文（前后各2行）
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context = "\n".join(lines[start:end])

            markers.append({
                "index": len(markers),
                "description": desc.strip(),
                "position": context,
            })

    log.info(f"解析到 {len(markers)} 个配图标记")
    for m in markers:
        log.info(f"  [{m['index']}] {m['description'][:60]}")

    return markers


# ── 类型分类 ──────────────────────────────────────────

# 关键词集合用于分类
_SCREENSHOT_KEYWORDS = {
    "产品", "公司", "人物", "推特", "tweet", "博客", "blog", "新闻",
    "发布会", "截图", "界面", "logo", "照片", "photo", "现场",
    "机器人", "robot", "硬件", "设备", "工厂", "实验室", "演示",
    "demo", "官网", "发布", "launch", "CES", "展会",
}
_CHART_KEYWORDS = {
    "时间线", "timeline", "对比", "comparison", "数据", "data",
    "趋势", "trend", "流程", "flow", "图表", "chart", "表格",
    "融资", "营收", "市场", "份额", "增长", "下降", "统计",
    "柱状图", "折线图", "饼图", "散点图", "热力图",
    "股价", "市值", "估值", "K线",
}


def classify_image_type(description: str) -> str:
    """
    将配图描述分类为三种类型之一。

    Returns:
        "screenshot" | "chart" | "ai_generated"
    """
    desc_lower = description.lower()

    # 检查数据图关键词（优先，因为数据图更明确）
    chart_hits = sum(1 for kw in _CHART_KEYWORDS if kw in desc_lower)
    if chart_hits >= 1:
        return "chart"

    # 检查实物/场景图关键词
    screenshot_hits = sum(1 for kw in _SCREENSHOT_KEYWORDS if kw in desc_lower)
    if screenshot_hits >= 1:
        return "screenshot"

    # 默认：AI生成（氛围图/抽象图）
    return "ai_generated"


# ── claude -p prompt 构造 ────────────────────────────

def build_image_prompt(markers: list[dict], article_text: str) -> str:
    """
    为 claude -p 调用构造 prompt。

    指导 agent 完成实物图搜索下载和数据图生成。
    AI生成图不在此 prompt 中处理（由 gen_image.py 单独调用）。
    """
    # 只取文章前 3000 字作为上下文（节省 token）
    article_context = article_text[:3000]
    if len(article_text) > 3000:
        article_context += "\n\n... (文章后续省略) ..."

    # 分类标记
    screenshot_markers = []
    chart_markers = []
    for m in markers:
        img_type = classify_image_type(m["description"])
        if img_type == "screenshot":
            screenshot_markers.append(m)
        elif img_type == "chart":
            chart_markers.append(m)

    if not screenshot_markers and not chart_markers:
        return ""

    # 构造任务列表
    tasks = []

    if screenshot_markers:
        tasks.append("## 任务A：实物/场景图搜索下载\n")
        tasks.append("对以下每个配图位置，搜索并下载合适的图片：\n")
        for m in screenshot_markers:
            tasks.append(f"### 配图 {m['index']}: {m['description']}")
            tasks.append(f"上下文：\n```\n{m['position']}\n```\n")
        tasks.append("""
搜索规则：
- 用 **英文产品名 + 场景** 搜索（如 "Atlas CES 2026 humanoid"），英文关键词效果更好
- 优先级：官方PR图 > 权威媒体报道配图 > 第三方照片
- 每个位置下载 3-5 张候选图
- 用 WebSearch 搜索图片，用 WebFetch 获取高清图片页面，用 curl/wget 下载
- **绝不使用带个人作者署名/水印的图片**（如 "作者：某某"、"摄影：某某"），优先用机构媒体图/企业PR图

下载后检查：
- 用 `sips -g pixelWidth -g pixelHeight <file>` 检查尺寸，宽度必须 >= 800px
- 小于 800px 的删除，换一张
- 最终用 `sips -Z 1800 <file>` 压缩到 1800px 以内
""")

    if chart_markers:
        tasks.append("## 任务B：数据图/信息图生成\n")
        tasks.append("对以下每个配图位置，用 matplotlib 生成数据图：\n")
        for m in chart_markers:
            tasks.append(f"### 配图 {m['index']}: {m['description']}")
            tasks.append(f"上下文：\n```\n{m['position']}\n```\n")
        tasks.append("""
生成规则：
- 使用 matplotlib + PingFang HK 字体
- **深色主题**：背景 #0a0e1a，文字 #e0e0e0，强调色 cyan/teal
- 金融数据用 yfinance 下载历史数据并绘图（**不要截图网站的live chart**）
- 图表要干净、信息密度高、排版紧凑
- 保存为 PNG，300 DPI
- 用 `sips -Z 1800 <file>` 压缩到 1800px 以内

matplotlib 深色主题模板：
```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = ['PingFang HK', 'sans-serif']

fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0a0e1a')
ax.set_facecolor('#0a0e1a')
ax.tick_params(colors='#e0e0e0')
ax.spines['bottom'].set_color('#333')
ax.spines['left'].set_color('#333')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.xaxis.label.set_color('#e0e0e0')
ax.yaxis.label.set_color('#e0e0e0')
ax.title.set_color('#e0e0e0')
# ... 绑定数据 ...
plt.tight_layout()
plt.savefig('output.png', dpi=300, facecolor='#0a0e1a')
```
""")

    task_text = "\n".join(tasks)

    return f"""你是配图采集系统。根据文章内容和配图标记，搜索下载实物图或生成数据图。

## 文章背景（节选）
{article_context}

{task_text}

## 输出要求

所有图片保存到 `{{IMAGES_DIR}}/` 目录，文件名格式：`img_{{序号}}_{{简短英文描述}}.png`
例如：img_0_atlas_robot_ces.png, img_1_funding_timeline.png

完成后，列出所有已保存的图片文件及其对应的配图标记序号。

格式：
```
===IMAGE_MANIFEST===
img_0_xxx.png -> 配图0: 描述
img_1_xxx.png -> 配图1: 描述
...
===END_MANIFEST===
```
"""


# ── AI 生成图（直接调用 gen_image.py）─────────────────

def generate_ai_image(description: str, index: int, images_dir: Path) -> bool:
    """
    调用 gen_image.py 生成单张 AI 图。

    Returns:
        是否成功
    """
    if not GEN_IMAGE_PATH.exists():
        log.warning(f"gen_image.py 不存在: {GEN_IMAGE_PATH}")
        return False

    # 构造英文 prompt（Gemini 英文效果更好）
    prompt = (
        f"Digital art for a tech article illustration. "
        f"Subject: {description}. "
        f"Style: dark space background (#0a0e1a), subtle geometric patterns, "
        f"glowing cyan/teal accents, floating particles, futuristic tech aesthetic. "
        f"NO text, NO letters, NO words. Pure visual design."
    )

    # 生成安全文件名
    safe_name = re.sub(r'[^\w\s-]', '', description[:30]).strip().replace(' ', '_')
    if not safe_name:
        safe_name = f"ai_gen"
    output_path = images_dir / f"img_{index}_{safe_name}.png"

    log.info(f"  生成AI图 [{index}]: {description[:50]}...")

    try:
        result = subprocess.run(
            [sys.executable, str(GEN_IMAGE_PATH),
             "--prompt", prompt,
             "--output", str(output_path),
             "--aspect", "16:9"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and output_path.exists():
            # 压缩到 1800px
            subprocess.run(
                ["sips", "-Z", "1800", str(output_path)],
                capture_output=True, timeout=30,
            )
            size_kb = output_path.stat().st_size // 1024
            log.info(f"  AI图已生成: {output_path.name} ({size_kb}KB)")
            return True
        else:
            log.warning(f"  AI图生成失败: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log.warning(f"  AI图生成超时 (120s)")
        return False
    except Exception as e:
        log.warning(f"  AI图生成异常: {e}")
        return False


# ── claude -p 调用（实物图+数据图）────────────────────

def run_claude_image_agent(prompt: str, images_dir: Path, model: str,
                           effort: str = "high") -> bool:
    """
    调用 claude -p 执行图片搜索下载和数据图生成。

    Returns:
        是否成功
    """
    from engine import run_claude_with_retry

    # 替换 prompt 中的 {IMAGES_DIR} 占位符
    prompt = prompt.replace("{IMAGES_DIR}", str(images_dir))

    cmd = [
        "claude", "-p",
        "--model", model,
        "--allowedTools", DEFAULT_TOOLS,
        "--effort", effort,
        "--no-session-persistence",
    ]

    log.info(f"调用 claude -p 采集实物图/数据图 (model={model}, effort={effort})")
    log.info(f"  Prompt 长度: {len(prompt)} chars ({len(prompt)//4} tokens approx)")
    log.info(f"  图片目录: {images_dir}")

    result = run_claude_with_retry(cmd, prompt, DEFAULT_TIMEOUT, logger=log)

    if result is None:
        return False
    if result.returncode != 0:
        log.error(f"claude -p 失败 (exit={result.returncode})")
        log.error(f"stderr: {result.stderr[:500]}")
        return False

    output = result.stdout.strip()
    if output:
        # 保存 agent 输出供调试
        log_path = images_dir / "_collection_log.md"
        log_path.write_text(output, encoding="utf-8")
        log.info(f"采集日志: {log_path}")

    return True


# ── 主入口 ────────────────────────────────────────────

def collect_images(article_text: str, topic_dir: Path, model: str = DEFAULT_MODEL,
                   effort: str = DEFAULT_EFFORT) -> bool:
    """
    主入口：解析文章配图标记，自动采集/生成配图。

    Called by engine.py post-processing.

    Args:
        article_text: 最终文章文本（含 [配图：xxx] 标记）
        topic_dir: 选题目录
        model: claude -p 使用的模型
        effort: 推理 effort 级别（low/medium/high）

    Returns:
        True if at least some images were collected
    """
    log.info("=" * 50)
    log.info("配图自动采集")
    log.info("=" * 50)

    # 1. 解析标记
    markers = parse_image_markers(article_text)
    if not markers:
        log.info("文章中无 [配图：...] 标记，跳过配图采集")
        return True  # 无标记不算失败

    # 2. 分类
    screenshot_markers = []
    chart_markers = []
    ai_markers = []

    for m in markers:
        img_type = classify_image_type(m["description"])
        m["type"] = img_type
        if img_type == "screenshot":
            screenshot_markers.append(m)
        elif img_type == "chart":
            chart_markers.append(m)
        else:
            ai_markers.append(m)

    log.info(f"分类结果: 实物图={len(screenshot_markers)}, 数据图={len(chart_markers)}, AI图={len(ai_markers)}")

    # 3. 创建图片目录
    images_dir = topic_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0

    # 4. 实物图 + 数据图：一次 claude -p 调用搞定
    if screenshot_markers or chart_markers:
        prompt = build_image_prompt(markers, article_text)
        if prompt:
            ok = run_claude_image_agent(prompt, images_dir, model, effort)
            if ok:
                # 统计实际下载的图片数量
                image_files = list(images_dir.glob("img_*.png")) + list(images_dir.glob("img_*.jpg"))
                log.info(f"claude -p 采集完成，图片文件: {len(image_files)}")
                success_count += len(image_files)
            else:
                log.warning("实物图/数据图采集失败")

    # 5. AI 生成图：逐个调用 gen_image.py
    for m in ai_markers:
        ok = generate_ai_image(m["description"], m["index"], images_dir)
        if ok:
            success_count += 1

    # 6. 汇总
    all_images = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    # 排除 cover.png（封面图由 engine.py 的 generate_cover_image 处理）
    content_images = [f for f in all_images if f.name != "cover.png"]

    log.info(f"配图采集完成: {len(content_images)} 张内容图")
    for f in sorted(content_images):
        size_kb = f.stat().st_size // 1024
        log.info(f"  {f.name} ({size_kb}KB)")

    return success_count > 0 or len(content_images) > 0


# ── CLI ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="降临派手记 · 配图自动采集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 对已完成的文章采集配图
  python image_collector.py --topic-dir wechat/公众号选题/2026-02-25|xxx

  # 指定模型和 effort
  python image_collector.py --topic-dir ... --model sonnet --effort medium
        """,
    )
    parser.add_argument("--topic-dir", required=True, help="选题目录路径")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default=DEFAULT_EFFORT,
                        help=f"推理 effort 级别 (默认: {DEFAULT_EFFORT})")

    args = parser.parse_args()
    topic_dir = Path(args.topic_dir).resolve()

    if not topic_dir.exists():
        log.error(f"选题目录不存在: {topic_dir}")
        sys.exit(1)

    # 读取文章文本（优先 article.md，其次 article_reviewed.md，其次 article_draft.md）
    article_text = ""
    for name in ("article.md", "article_reviewed.md", "article_factchecked.md", "article_draft.md"):
        path = topic_dir / name
        if path.exists():
            article_text = path.read_text(encoding="utf-8")
            log.info(f"读取文章: {path.name} ({len(article_text)} chars)")
            break

    if not article_text:
        log.error("未找到文章文件 (article.md / article_reviewed.md / article_draft.md)")
        sys.exit(1)

    success = collect_images(
        article_text=article_text,
        topic_dir=topic_dir,
        model=args.model,
        effort=args.effort,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
