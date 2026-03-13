"""
Skill: 刷新征文机会数据库（自进化搜索）

4-Phase 流水线：
  Phase 1 — 搜索 (haiku + WebSearch): 读搜索方法论 → 执行 ≤5 条查询 → 原始结果
  Phase 2 — 解析 (haiku): 搜索结果 → 结构化 JSON，标记 is_new / updates_existing
  Phase 3 — 更新 (纯 Python): 新条目追加数据库，变化条目原地更新，写搜索日志
  Phase 4 — 进化 (sonnet): 分析搜索效果 → 重写搜索方法论.md

模型分层：haiku 执行搜索（便宜快），sonnet 做策略优化（贵但聪明）。
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


def _strip_brackets(s: str) -> str:
    """Strip 《》「」【】等括号，用于子串去重比较。"""
    return re.sub(r"[《》「」【】〈〉\[\]（）()\"\"'']", "", s).strip()


def _extract_venue_names(db_content: str) -> list[str]:
    """从机会数据库 Markdown 中提取所有 venue 名称。"""
    names = []
    # Match ### N. 名称 or ### N. 《名称》
    for m in re.finditer(r"###\s*\d+\.\s*(.+?)(?:\s*⭐|$)", db_content, re.MULTILINE):
        raw = m.group(1).strip()
        names.append(raw)
        names.append(_strip_brackets(raw))
    return names


def _is_duplicate(new_name: str, existing_names: list[str]) -> bool:
    """程序化去重：strip 括号后做子串匹配。"""
    clean_new = _strip_brackets(new_name).lower()
    if not clean_new:
        return False
    for existing in existing_names:
        clean_ex = _strip_brackets(existing).lower()
        if not clean_ex:
            continue
        if clean_new in clean_ex or clean_ex in clean_new:
            return True
    return False


class RefreshOpportunitiesSkill(Skill):
    name = "refresh_opportunities"
    description = "全网搜索新征文机会，增量更新数据库，搜索策略自进化"
    estimated_duration = "5min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        lit_root = Path(config["paths"]["lit_root"]).expanduser()
        opps_dir = lit_root / "投稿机会"
        db_file = opps_dir / "机会数据库.md"
        methodology_file = Path(
            config["paths"].get("search_methodology_file", str(opps_dir / "搜索方法论.md"))
        ).expanduser()
        log_file = Path(
            config["paths"].get("search_log_file", str(opps_dir / "搜索日志.jsonl"))
        ).expanduser()

        if not db_file.exists():
            return SkillResult(False, "机会数据库.md 不存在")

        db_content = db_file.read_text()
        existing_names = _extract_venue_names(db_content)

        # Load methodology (seed or evolved)
        methodology = ""
        if methodology_file.exists():
            methodology = methodology_file.read_text()

        # ── Phase 1: Search (haiku + WebSearch) ──────────────────

        phase1_prompt = f"""你是征文机会搜索 Agent。你的任务是搜索中文文学征文/投稿机会。

## 搜索方法论（遵循这个策略）

{methodology if methodology else "首次搜索，使用通用查询。"}

## 已有机会列表（避免重复搜索这些）

{chr(10).join(f"- {n}" for n in existing_names[:30])}

## 指令

1. 根据方法论生成 3-5 条高质量搜索查询
2. 对每条查询执行 WebSearch
3. 对有价值的结果用 WebFetch 获取详情

输出严格 JSON（不要 markdown 代码块）：
{{
  "queries_used": ["查询1", "查询2", ...],
  "results": [
    {{
      "title": "征文/刊物名称",
      "url": "来源URL",
      "deadline": "截止日期或'长期'",
      "genre": "体裁",
      "theme": "主题方向",
      "word_count": "字数要求",
      "submission": "投稿方式（邮箱/网站）",
      "prize": "奖项/稿费",
      "host": "主办方",
      "snippet": "关键描述摘要（50字内）"
    }},
    ...
  ]
}}

只返回与文学创作投稿相关的结果。忽略学术论文征稿。最多返回 10 条。"""

        try:
            result1 = subprocess.run(
                ["claude", "-p", phase1_prompt, "--model", "haiku",
                 "--allowedTools", "WebSearch,WebFetch",
                 "--output-format", "text"],
                capture_output=True, text=True, timeout=180, env=_clean_env(),
            )
            if result1.returncode != 0:
                return SkillResult(False, f"Phase 1 搜索失败: {result1.stderr[:300]}")

            raw1 = result1.stdout.strip()
            search_data = self._parse_json(raw1)
            if not search_data:
                return SkillResult(False, f"Phase 1 JSON 解析失败:\n{raw1[:500]}")

        except subprocess.TimeoutExpired:
            return SkillResult(False, "Phase 1 搜索超时 (>3min)")
        except Exception as e:
            return SkillResult(False, f"Phase 1 异常: {e}")

        queries_used = search_data.get("queries_used", [])
        raw_results = search_data.get("results", [])

        if not raw_results:
            # No results — still log and evolve
            self._write_log(log_file, queries_used, 0, 0, db_content)
            self._run_evolution(methodology_file, methodology, queries_used, [], db_content)
            return SkillResult(True, "搜索完成，未发现新机会。", {
                "new_found": 0, "updated": 0, "queries_used": queries_used
            })

        # ── Phase 2: Parse & Dedup (haiku) ───────────────────────

        phase2_prompt = f"""你是数据清洗 Agent。对比搜索结果和已有机会列表，标记每条是新的还是已有的更新。

## 已有机会列表

{chr(10).join(f"- {n}" for n in existing_names[:30])}

## 搜索结果

{json.dumps(raw_results, ensure_ascii=False, indent=2)[:4000]}

## 指令

对每条搜索结果，判断：
- is_new: true（数据库中没有这个刊物/大赛）或 false（已存在，可能是信息更新）
- updates_existing: 如果 is_new=false，是否有新信息（如截止日期变化、新一届比赛）
- existing_name: 如果 is_new=false，对应的已有名称

输出严格 JSON 数组（不要 markdown 代码块），每个元素：
{{
  "title": "名称",
  "url": "URL",
  "deadline": "截止日期或长期",
  "genre": "体裁",
  "theme": "主题",
  "word_count": "字数",
  "submission": "投稿方式",
  "prize": "奖项/稿费",
  "host": "主办方",
  "snippet": "摘要",
  "is_new": true/false,
  "updates_existing": false,
  "existing_name": ""
}}"""

        try:
            result2 = subprocess.run(
                ["claude", "-p", phase2_prompt, "--model", "haiku",
                 "--output-format", "text"],
                capture_output=True, text=True, timeout=120, env=_clean_env(),
            )
            if result2.returncode != 0:
                return SkillResult(False, f"Phase 2 解析失败: {result2.stderr[:300]}")

            parsed_results = self._parse_json(result2.stdout.strip())
            if not isinstance(parsed_results, list):
                # Try to extract array from dict
                if isinstance(parsed_results, dict):
                    parsed_results = parsed_results.get("results", [])
                if not isinstance(parsed_results, list):
                    parsed_results = raw_results  # Fallback to raw

        except subprocess.TimeoutExpired:
            return SkillResult(False, "Phase 2 解析超时")
        except Exception as e:
            parsed_results = raw_results  # Fallback

        # ── Phase 3: Update DB (pure Python) ─────────────────────

        # Programmatic dedup fallback: recheck is_new with substring matching
        new_entries = []
        updated_entries = []
        for item in parsed_results:
            title = item.get("title", "")
            if not title:
                continue

            # Override LLM dedup with programmatic check
            if _is_duplicate(title, existing_names):
                item["is_new"] = False
                if item.get("updates_existing"):
                    updated_entries.append(item)
            elif item.get("is_new", True):
                new_entries.append(item)

        # Append new entries to database
        if new_entries:
            next_num = self._get_next_entry_number(db_content)
            additions = []
            for entry in new_entries:
                additions.append(self._format_db_entry(entry, next_num))
                next_num += 1
            # Insert before "## 优先行动排序" or append at end
            insert_marker = "## 优先行动排序"
            if insert_marker in db_content:
                insert_text = "\n".join(additions) + "\n\n"
                db_content = db_content.replace(
                    insert_marker, insert_text + insert_marker
                )
            else:
                db_content += "\n\n" + "\n".join(additions)

            db_file.write_text(db_content)

        # Update existing entries (only deadline changes for now)
        for entry in updated_entries:
            # Simple: log the update, don't auto-modify existing entries
            pass

        # Write search log
        total_after = len(_extract_venue_names(db_content)) // 2  # /2 because we store raw+clean
        self._write_log(log_file, queries_used, len(new_entries), len(updated_entries), db_content)

        # ── Phase 4: Evolve methodology (sonnet) ─────────────────

        self._run_evolution(
            methodology_file, methodology, queries_used,
            parsed_results, db_content
        )

        # Build summary
        summary_lines = [f"机会数据库已更新"]
        summary_lines.append(f"新发现: {len(new_entries)} 条")
        if updated_entries:
            summary_lines.append(f"更新: {len(updated_entries)} 条")
        summary_lines.append(f"搜索查询: {len(queries_used)} 条")

        if new_entries:
            summary_lines.append("\n新机会：")
            for e in new_entries:
                summary_lines.append(f"  - {e.get('title', '?')}")

        return SkillResult(True, "\n".join(summary_lines), {
            "new_found": len(new_entries),
            "updated": len(updated_entries),
            "queries_used": queries_used,
            "new_entries": [e.get("title", "") for e in new_entries],
        })

    # ── Helpers ───────────────────────────────────────────────

    def _parse_json(self, text: str):
        """Parse JSON from LLM output, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object or array
            for start_char, end_char in [("{", "}"), ("[", "]")]:
                start = text.find(start_char)
                end = text.rfind(end_char) + 1
                if start >= 0 and end > start:
                    try:
                        return json.loads(text[start:end])
                    except json.JSONDecodeError:
                        continue
            return None

    def _get_next_entry_number(self, db_content: str) -> int:
        """Find the highest entry number in the DB and return next."""
        nums = [int(m.group(1)) for m in re.finditer(r"###\s*(\d+)\.", db_content)]
        return max(nums) + 1 if nums else 1

    def _format_db_entry(self, entry: dict, num: int) -> str:
        """Format a new entry as Markdown table matching existing DB format."""
        title = entry.get("title", "未知")
        deadline = entry.get("deadline", "待确认")
        genre = entry.get("genre", "待确认")
        word_count = entry.get("word_count", "待确认")
        submission = entry.get("submission", "待确认")
        prize = entry.get("prize", "待确认")
        host = entry.get("host", "待确认")
        theme = entry.get("theme", "")
        url = entry.get("url", "")
        snippet = entry.get("snippet", "")

        lines = [
            f"### {num}. {title}（自动发现）",
            "",
            "| 项 | 值 |",
            "|---|---|",
        ]
        if host:
            lines.append(f"| **主办** | {host} |")
        if deadline and deadline != "长期":
            lines.append(f"| **截止** | {deadline} |")
        lines.append(f"| **体裁** | {genre} |")
        if theme:
            lines.append(f"| **主题** | {theme} |")
        if word_count and word_count != "待确认":
            lines.append(f"| **字数** | {word_count} |")
        if prize and prize != "待确认":
            lines.append(f"| **奖项** | {prize} |")
        lines.append(f"| **投稿方式** | {submission} |")
        lines.append(f"| **素材匹配** | 🟡 待评估 |")
        lines.append(f"| **状态** | 待评估（自动发现） |")
        if url:
            lines.append(f"| **来源** | [{title}]({url}) |")
        if snippet:
            lines.append(f"| **备注** | {snippet} |")
        lines.append("")

        return "\n".join(lines)

    def _write_log(self, log_file: Path, queries: list, new_found: int,
                   updated: int, db_content: str):
        """Append search log entry."""
        log_file.parent.mkdir(parents=True, exist_ok=True)
        total = len([m for m in re.finditer(r"###\s*\d+\.", db_content)])
        record = {
            "timestamp": datetime.now().isoformat(),
            "queries_used": queries,
            "new_found": new_found,
            "updated": updated,
            "total_after": total,
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _run_evolution(self, methodology_file: Path, old_methodology: str,
                       queries: list, results: list, db_content: str):
        """Phase 4: Use sonnet to rewrite search methodology."""
        new_count = sum(1 for r in results if r.get("is_new"))
        total_results = len(results)

        evolution_prompt = f"""你是搜索策略优化 Agent。分析本次搜索的效果，重写搜索方法论文件。

## 本次搜索数据

- 查询数: {len(queries)}
- 查询: {json.dumps(queries, ensure_ascii=False)}
- 搜索结果总数: {total_results}
- 新发现数: {new_count}
- 日期: {datetime.now().strftime('%Y-%m-%d')}

## 当前方法论

{old_methodology if old_methodology else "（首次搜索，无历史方法论）"}

## 现有数据库概况

数据库共有 {len([m for m in re.finditer(r'### [0-9]+.', db_content)])} 条机会。
涵盖：征文大赛、文学期刊、网络平台、报纸副刊。

## 指令

请输出完整的新版搜索方法论（Markdown 格式），包含以下章节：

# 搜索方法论

## 上次搜索
（日期、新发现数、查询次数）

## 有效搜索查询（按产出排序）
（列出所有查过的查询，标注每条的产出）

## 有效搜索网站
（发现过结果的网站域名）

## 搜索策略
### 时效性比赛
### 长期期刊
### 地域匹配
### 网络平台

## 搜索禁区
（浪费 quota 的查询类型）

## 经验笔记
（本次搜索的经验教训）

重要：
- 保留历史有效查询
- 删除已证明无效的查询
- 根据本次结果新增发现的有效网站
- 如果某个查询产出为0，移入搜索禁区
- 方法论越跑越精，不要每次推倒重来"""

        try:
            result = subprocess.run(
                ["claude", "-p", evolution_prompt, "--model", "sonnet",
                 "--output-format", "text"],
                capture_output=True, text=True, timeout=120, env=_clean_env(),
            )
            if result.returncode == 0 and result.stdout.strip():
                methodology_file.parent.mkdir(parents=True, exist_ok=True)
                methodology_file.write_text(result.stdout.strip())
        except Exception:
            pass  # Evolution failure is non-fatal
