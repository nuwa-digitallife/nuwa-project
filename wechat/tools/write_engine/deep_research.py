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
from __future__ import annotations

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
DEFAULT_SEARCH_MODEL = "haiku"
DEFAULT_EFFORT = "high"
DEFAULT_SEARCH_EFFORT = "medium"
DEFAULT_TOOLS = "WebSearch,WebFetch,Read"
DEFAULT_TIMEOUT = 600
DEFAULT_MAX_ROUNDS = 5
DEFAULT_MIN_NEW_ENTITIES = 2


def _load_model_config():
    global DEFAULT_MODEL, DEFAULT_SEARCH_MODEL, DEFAULT_EFFORT, DEFAULT_SEARCH_EFFORT
    global DEFAULT_TOOLS, DEFAULT_TIMEOUT, DEFAULT_MAX_ROUNDS, DEFAULT_MIN_NEW_ENTITIES
    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        dr = config.get("models", {}).get("deep_research", {})
        if dr.get("model"):
            DEFAULT_MODEL = dr["model"]
        if dr.get("search_model"):
            DEFAULT_SEARCH_MODEL = dr["search_model"]
        if dr.get("effort"):
            DEFAULT_EFFORT = dr["effort"]
        if dr.get("search_effort"):
            DEFAULT_SEARCH_EFFORT = dr["search_effort"]
        if dr.get("tools"):
            DEFAULT_TOOLS = dr["tools"]
        if dr.get("timeout"):
            DEFAULT_TIMEOUT = dr["timeout"]
        if dr.get("max_rounds"):
            DEFAULT_MAX_ROUNDS = dr["max_rounds"]
        if dr.get("min_new_entities"):
            DEFAULT_MIN_NEW_ENTITIES = dr["min_new_entities"]
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

### ⛔ 覆盖审计（必做，不可跳过）
搜索完成后，**在输出素材报告之前**，必须执行以下三步自检：

**Step A — 权威基准对照**：
1. 搜索 "[选题] 综述/overview/comprehensive guide" 和 "[topic] key players/timeline/analysis"
2. 找到 2-3 篇该话题的权威综合分析（权威媒体长文、行业报告、学术综述）
3. 对比它们覆盖的实体（人物/公司/事件/技术/地理区域）与你已采集的素材
4. 列出差异清单：哪些它们提到而你没有？

**Step B — 对抗性自查**：
1. 问自己："如果这个领域的专家看我的素材清单，他会说我漏了什么？"
2. 识别相邻术语/概念（例：搜"世界模型"后应扩展搜"spatial intelligence"、"3D generation"等），确保不因术语差异遗漏重要内容
3. 对 Step A 和 Step B 发现的每个缺口，执行至少一轮针对性补充搜索

**Step C — 时效性核查**：
1. 列出素材中所有关键实体（公司/产品/人物/技术）
2. 对每个实体搜索 "[实体名] latest 2026" 和 "[实体名] 最新进展"
3. 对比搜索结果与已采集素材：产品是否有新版本？公司是否有新融资/新动态？人物是否有新动向？
4. 发现过期信息 → **直接用最新数据替换旧数据**，不保留过期条目
5. 在审计记录中标注替换内容，例："`Genie 2 → Genie 3 (2025-08发布)，已替换`"

只有确认三步审计全部通过（无重大缺口、无过期信息），才能输出最终素材报告。在素材报告末尾附上「覆盖审计记录」：列出对照了哪些权威来源、发现了哪些缺口、如何补充、哪些数据做了时效性更新。

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


def build_followup_prompt(topic: str, accumulated_summary: str,
                          entity_list: set, round_num: int) -> str:
    """构造后续轮次的检索 prompt——基于已有实体发现新线索。"""
    entities_str = "、".join(sorted(entity_list))
    return f"""你是降临派手记的素材采集系统，正在执行第 {round_num} 轮迭代检索。

## 选题
{topic}

## 已有素材摘要（前几轮已采集）
{accumulated_summary[:10000]}

## 已发现的实体清单
{entities_str}

## 本轮任务

**不要重复搜索已有内容。** 你的任务是发现上面素材中 **提到但未深入** 的线索：

1. **关联实体挖掘**：已有实体提到的合作方、竞争对手、上下游公司/技术，逐一搜索
2. **相邻领域扩展**：与选题直接相关但尚未覆盖的技术方向、政策动态、市场数据
3. **反方观点**：搜索对已有观点的反驳、质疑、替代解释
4. **一手源追溯**：已有素材中引用的但未直接访问的论文/官方博客/GitHub
5. **最新动态**：对已有实体搜索 "latest 2026" / "最新进展"

### 搜索策略
- 中英文各 2-3 轮搜索，使用上面实体清单派生的关键词
- 找到新信息后追溯一手源
- 关键数字交叉验证

## 输出格式

### 新发现素材
（只输出本轮新发现的内容，不重复已有素材）

每条素材标注信源 URL。

### 新发现实体
（列出本轮新发现的公司/人物/产品/技术名称，每行一个，格式：`- 实体名`）
"""


def extract_entities(text: str) -> set:
    """调用 haiku 从素材文本中提取实体名（公司/人物/产品/技术）。"""
    from engine import run_claude_with_retry

    prompt = f"""从以下文本中提取所有关键实体（公司名、人物名、产品名、技术名、模型名）。

要求：
- 每行一个实体，格式：`- 实体名`
- 只输出实体列表，不要其他内容
- 合并重复（如 "OpenAI" 和 "Open AI" 只保留 "OpenAI"）
- 忽略过于泛化的词（如 "AI"、"机器学习"）

文本：
{text[:12000]}"""

    cmd = [
        "claude", "-p",
        "--model", DEFAULT_SEARCH_MODEL,
        "--effort", "low",
        "--no-session-persistence",
    ]
    result = run_claude_with_retry(cmd, prompt, timeout=120, max_retries=2, logger=log)
    if result is None or result.returncode != 0 or not result.stdout.strip():
        # fallback: 简单正则提取（不依赖 LLM）
        log.warning("  实体提取 LLM 失败，使用 fallback")
        return set()

    entities = set()
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            entity = line[2:].strip().strip("`").strip("*")
            if entity and len(entity) > 1:
                entities.add(entity)
    log.info(f"  提取到 {len(entities)} 个实体")
    return entities


def merge_materials(rounds: list, topic: str) -> str:
    """调用 haiku 将多轮素材合并去重，输出统一格式的素材报告。"""
    from engine import run_claude_with_retry

    combined = "\n\n---\n\n".join(
        f"## 第 {i+1} 轮素材\n{text}" for i, text in enumerate(rounds)
    )
    # 如果总量不大，直接拼接即可，不需要 LLM 去重
    if len(combined) < 20000:
        return combined

    prompt = f"""将以下多轮采集的素材合并为一份统一的素材报告。

要求：
1. 去除重复内容（同一事实只保留信源最权威的版本）
2. 保留所有 URL 信源
3. 按以下结构组织：核心事实、关键人物/公司、时间线、多方观点、数据表、争议点、一手源清单、潜在配图素材
4. 标注哪些内容是后续轮次补充发现的（用 [Round N 补充] 标记）

## 选题：{topic}

{combined[:30000]}"""

    cmd = [
        "claude", "-p",
        "--model", DEFAULT_SEARCH_MODEL,
        "--effort", "medium",
        "--no-session-persistence",
    ]
    result = run_claude_with_retry(cmd, prompt, timeout=300, max_retries=2, logger=log)
    if result is None or result.returncode != 0 or not result.stdout.strip():
        log.warning("  素材合并 LLM 失败，使用简单拼接")
        return combined
    log.info(f"  素材合并完成 ({len(result.stdout.strip())} chars)")
    return result.stdout.strip()


def build_audit_prompt(topic: str, materials: str) -> str:
    """构造独立审计 prompt——代码强制的第二步验证。"""
    return f"""你是一个素材审计员。你的唯一任务是核查以下素材报告的**覆盖完整性**和**时效性**。

## 选题
{topic}

## 待审计素材
{materials[:15000]}

## 审计步骤（必须全部执行）

### Step 1 — 提取关键实体
从素材中提取所有关键实体（公司、产品、人物、技术、模型名称）。列出清单。

### Step 2 — 覆盖检查
搜索 "[选题] overview/综述 2026" 和 "[topic] key players/主要公司"。
找到 2-3 篇权威综合分析，对比它们提到的实体与素材清单。
**列出素材中缺失的重要实体。**

### Step 3 — 时效性检查
对素材中每个关键实体，搜索 "[实体名] latest news 2026" 或 "[实体名] 最新"。
检查：
- 产品是否有新版本？（如 Genie 2 → Genie 3）
- 公司是否有新融资、新估值？
- 人物是否有新动向？
- 数据是否有更新？

**列出所有过期信息，标注旧值和新值。**

## 输出格式

# 审计报告：{topic}

## 关键实体清单
（从素材中提取的实体列表）

## 覆盖检查结果
✅ 已覆盖：...
⚠️ 需要补充：...（列出缺失实体及理由）

## 时效性检查结果
✅ 最新：...（实体名 + 确认信息）
⚠️ 需要更新：...（实体名 + 旧值 → 新值 + 信源URL）

## 审计结论
PASS / FAIL（FAIL = 有任何"⚠️ 需要补充"或"⚠️ 需要更新"）
"""


def build_patch_prompt(topic: str, materials: str, audit: str) -> str:
    """根据审计结果构造补充采集 prompt。"""
    return f"""你是素材补充采集员。审计发现以下素材有缺口或过期信息，你需要补充。

## 选题
{topic}

## 审计报告（重点关注 ⚠️ 标记的条目）
{audit}

## 原始素材
{materials[:15000]}

## 任务
1. 对审计报告中每个 "⚠️ 需要补充" 的实体，搜索并采集相关素材
2. 对审计报告中每个 "⚠️ 需要更新" 的实体，搜索最新数据替换旧数据
3. 将补充内容合并到原始素材中，输出完整的更新版素材报告

## 输出
输出**完整的更新后素材报告**（不是增量，是替换原始报告的完整版本）。
在末尾附上「审计更新记录」：列出补充了什么、更新了什么。
"""


def run_audit(topic: str, materials: str, model: str = DEFAULT_MODEL) -> str | None:
    """运行独立审计 agent，返回审计报告文本。"""
    from engine import run_claude_with_retry

    prompt = build_audit_prompt(topic, materials)
    cmd = [
        "claude", "-p",
        "--model", model,
        "--allowedTools", DEFAULT_TOOLS,
        "--effort", "medium",  # 审计不需要 high effort
        "--no-session-persistence",
    ]
    log.info("  调用审计 agent...")
    result = run_claude_with_retry(cmd, prompt, DEFAULT_TIMEOUT, logger=log)
    if result is None or result.returncode != 0:
        log.error("  审计 agent 失败")
        return None
    output = result.stdout.strip()
    if not output:
        log.error("  审计 agent 无输出")
        return None
    log.info(f"  审计完成 ({len(output)} chars)")
    return output


def run_patch(topic: str, materials: str, audit: str,
              model: str = DEFAULT_MODEL) -> str | None:
    """根据审计结果补充采集，返回更新后的完整素材。"""
    from engine import run_claude_with_retry

    prompt = build_patch_prompt(topic, materials, audit)
    cmd = [
        "claude", "-p",
        "--model", model,
        "--allowedTools", DEFAULT_TOOLS,
        "--effort", "high",
        "--no-session-persistence",
    ]
    log.info("  调用补充采集 agent...")
    result = run_claude_with_retry(cmd, prompt, DEFAULT_TIMEOUT, logger=log)
    if result is None or result.returncode != 0:
        log.error("  补充采集 agent 失败")
        return None
    output = result.stdout.strip()
    if not output:
        log.error("  补充采集 agent 无输出")
        return None
    log.info(f"  补充采集完成 ({len(output)} chars)")
    return output


def _run_search_round(topic: str, prompt: str, round_num: int,
                      model: str = DEFAULT_SEARCH_MODEL,
                      effort: str = DEFAULT_SEARCH_EFFORT) -> str | None:
    """执行单轮搜索，返回素材文本。"""
    from engine import run_claude_with_retry

    cmd = [
        "claude", "-p",
        "--model", model,
        "--allowedTools", DEFAULT_TOOLS,
        "--effort", effort,
        "--no-session-persistence",
    ]
    log.info(f"  [Round {round_num}] 调用 {model} 搜索...")
    result = run_claude_with_retry(cmd, prompt, DEFAULT_TIMEOUT, logger=log)
    if result is None or result.returncode != 0:
        log.error(f"  [Round {round_num}] 搜索失败")
        if result and result.stderr:
            log.error(f"  stderr: {result.stderr[:300]}")
        return None
    output = result.stdout.strip()
    if not output:
        log.error(f"  [Round {round_num}] 无输出")
        return None
    log.info(f"  [Round {round_num}] 完成 ({len(output)} chars)")
    return output


def run_research(topic_dir: Path, topic: str = None, model: str = DEFAULT_MODEL,
                 effort: str = DEFAULT_EFFORT, max_rounds: int = DEFAULT_MAX_ROUNDS,
                 min_new_entities: int = DEFAULT_MIN_NEW_ENTITIES) -> bool:
    """执行深度素材采集（迭代收敛搜索）。"""
    topic_dir = Path(topic_dir).resolve()
    if not topic_dir.exists():
        log.error(f"选题目录不存在: {topic_dir}")
        return False

    # 推断主题
    if not topic:
        topic = infer_topic_from_dir(topic_dir)
    log.info(f"深度采集启动: {topic}")
    log.info(f"  目录: {topic_dir}")
    log.info(f"  搜索模型: {DEFAULT_SEARCH_MODEL}, 审计模型: {model}")
    log.info(f"  最大轮数: {max_rounds}, 收敛阈值: {min_new_entities} 新实体")

    # 读取已有素材
    existing = load_existing_materials(topic_dir)
    if existing:
        log.info(f"  已有浅层素材: {len(existing)} chars")
    else:
        log.info("  无已有素材，从零搜索")

    # ── Round 1: 初始广搜 ──
    prompt = build_research_prompt(topic, existing)
    log.info(f"  Round 1 prompt: {len(prompt)} chars")

    materials = _run_search_round(topic, prompt, round_num=1,
                                  model=DEFAULT_SEARCH_MODEL,
                                  effort=DEFAULT_SEARCH_EFFORT)
    if not materials:
        return False

    all_rounds = [materials]
    entities = extract_entities(materials)
    log.info(f"  [Round 1] 实体: {len(entities)} 个")

    # ── Iterative rounds: 基于实体清单继续深挖 ──
    for round_num in range(2, max_rounds + 1):
        followup_prompt = build_followup_prompt(
            topic, materials, entities, round_num
        )
        new_materials = _run_search_round(
            topic, followup_prompt, round_num=round_num,
            model=DEFAULT_SEARCH_MODEL, effort=DEFAULT_SEARCH_EFFORT
        )
        if not new_materials:
            log.info(f"  [Round {round_num}] 搜索失败，停止迭代")
            break

        new_entities = extract_entities(new_materials)
        added = new_entities - entities

        # 备用判断：新增材料长度 < 上一轮的 10%
        length_ratio = len(new_materials) / max(len(all_rounds[-1]), 1)
        log.info(f"  [Round {round_num}] 新增 {len(added)} 个实体, "
                 f"内容比例 {length_ratio:.1%}")

        if len(added) < min_new_entities:
            log.info(f"  [Round {round_num}] 新增实体不足 {min_new_entities}，收敛退出")
            # 仍然保留本轮内容（可能有价值的补充）
            if new_materials.strip():
                all_rounds.append(new_materials)
            break

        log.info(f"  [Round {round_num}] 新实体: {sorted(added)}")
        entities |= new_entities
        all_rounds.append(new_materials)
        # 更新累积素材供下一轮使用
        materials = merge_materials(all_rounds, topic)

    log.info(f"  迭代搜索完成: {len(all_rounds)} 轮, {len(entities)} 个实体")

    # ── 合并所有轮次素材 ──
    if len(all_rounds) > 1:
        output = merge_materials(all_rounds, topic)
    else:
        output = all_rounds[0]

    # ── 独立验证步骤：覆盖+时效性核查（用 opus） ──
    log.info("  开始独立验证（覆盖+时效性核查）...")
    audit_result = run_audit(topic, output, model=model)
    if audit_result:
        audit_path = topic_dir / "素材" / "audit_report.md"
        topic_dir.joinpath("素材").mkdir(exist_ok=True)
        audit_path.write_text(audit_result, encoding="utf-8")
        log.info(f"  审计报告已保存: {audit_path}")

        # 检查是否有需要更新的内容
        if "⚠️ 需要更新" in audit_result or "⚠️ 需要补充" in audit_result:
            log.warning("  审计发现过期或缺失内容，执行补充采集...")
            patched = run_patch(topic, output, audit_result, model=model)
            if patched:
                output = patched
                log.info("  ✅ 素材已根据审计结果更新")
            else:
                log.warning("  补充采集失败，使用原始素材（审计报告已保存供人工检查）")
    else:
        log.warning("  审计步骤失败，素材将保存但标记为未审计")

    # 保存素材报告
    materials_dir = topic_dir / "素材"
    materials_dir.mkdir(exist_ok=True)

    output_path = materials_dir / "deep_research.md"
    output_path.write_text(output, encoding="utf-8")
    log.info(f"  ✅ 素材报告已保存: {output_path} ({len(output)} chars)")

    # 保存实体清单（便于调试和复盘）
    entity_path = materials_dir / "entity_list.txt"
    entity_path.write_text("\n".join(sorted(entities)), encoding="utf-8")
    log.info(f"  实体清单已保存: {entity_path} ({len(entities)} 个)")

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

  # 限制迭代轮数
  python deep_research.py --topic-dir ... --max-rounds 3
        """,
    )
    parser.add_argument("--topic-dir", required=True, help="选题目录路径")
    parser.add_argument("--topic", default=None, help="选题主题（不指定则从目录名推断）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"审计模型 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--effort", choices=["low", "medium", "high"], default=DEFAULT_EFFORT,
                        help=f"审计 effort 级别 (默认: {DEFAULT_EFFORT})")
    parser.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS,
                        help=f"最大迭代轮数 (默认: {DEFAULT_MAX_ROUNDS})")
    parser.add_argument("--min-new-entities", type=int, default=DEFAULT_MIN_NEW_ENTITIES,
                        help=f"收敛阈值 (默认: {DEFAULT_MIN_NEW_ENTITIES})")

    args = parser.parse_args()
    success = run_research(
        topic_dir=args.topic_dir,
        topic=args.topic,
        model=args.model,
        effort=args.effort,
        max_rounds=args.max_rounds,
        min_new_entities=args.min_new_entities,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
