"""
Skill: 扫描征文机会
读取机会数据库 + 已有素材/作品 → 输出匹配报告

不联网（数据库是本地 Markdown），纯文本匹配 + LLM 判断。
"""

import subprocess
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class ScanOpportunitiesSkill(Skill):
    name = "scan_opportunities"
    description = "扫描投稿机会数据库，匹配现有素材和作品，推荐可投目标"
    estimated_duration = "3min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        keyword = params.get("keyword", "")  # 可选：按关键词过滤
        genre = params.get("genre", "")      # 可选：按体裁过滤

        lit_root = Path(config["paths"]["lit_root"]).expanduser()

        # Load opportunity database
        opps_file = lit_root / "投稿机会" / "机会数据库.md"
        if not opps_file.exists():
            return SkillResult(False, "机会数据库不存在")
        opps_content = opps_file.read_text()

        # Load available materials
        materials_dir = Path(config["paths"]["materials_dir"]).expanduser()
        materials_list = []
        if materials_dir.exists():
            for d in materials_dir.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    materials_list.append(d.name)
        materials_str = ", ".join(materials_list) if materials_list else "暂无素材"

        # Load existing works
        works_dir = Path(config["paths"]["works_dir"]).expanduser()
        works_list = []
        if works_dir.exists():
            for d in works_dir.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    meta_file = d / "meta.json"
                    if meta_file.exists():
                        import json
                        meta = json.loads(meta_file.read_text())
                        allowed = meta.get('allowed_platforms', [])
                        allowed_str = f", 只投: {'、'.join(allowed)}" if allowed else ""
                        works_list.append(
                            f"{meta.get('title', d.name)} ({meta.get('genre', '?')}, "
                            f"~{meta.get('char_count', '?')}字, "
                            f"状态: {meta.get('status', '?')}{allowed_str})"
                        )
                    else:
                        works_list.append(d.name)
        works_str = "\n".join(f"  - {w}" for w in works_list) if works_list else "暂无作品"

        # Load submissions to know what's already submitted
        submissions_file = lit_root / "已投稿" / "submissions.jsonl"
        submitted = []
        if submissions_file.exists():
            import json
            for line in submissions_file.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    submitted.append(f"{r['work']} → {r['venue']} ({r['status']})")
        submitted_str = "\n".join(f"  - {s}" for s in submitted) if submitted else "暂无投稿"

        # Build prompt for LLM matching
        filter_hint = ""
        if keyword:
            filter_hint += f"\n重点关注包含「{keyword}」的机会。"
        if genre:
            filter_hint += f"\n只看体裁为「{genre}」的机会。"

        prompt = f"""你是文学编辑 Agent。请分析以下投稿机会数据库，结合现有素材和作品，推荐最值得投的目标。

## 现有素材域
{materials_str}

## 现有作品
{works_str}

## 已投稿记录
{submitted_str}

## 投稿机会数据库
{opps_content[:6000]}
{filter_hint}

## 要求

输出严格 JSON 数组（不要 markdown 代码块），每个元素：
{{
  "id": "简短ID如 hongdou、jiaxianghao",
  "venue": "刊物/大赛名",
  "theme": "主题方向",
  "genre": "散文/小说/非虚构",
  "match": "高/中",
  "reason": "一句话匹配理由",
  "action": "direct_submit/new_write/skip",
  "topic_suggestion": "如需新写，建议选题方向（一句话）",
  "word_count": "建议字数如 2500",
  "email": "投稿邮箱"
}}

只输出匹配度"高"或"中"的。已投稿的不重复推荐。最多5条。
重要：作品信息中标注了"只投: XX"的，只能推荐给该平台，不得推荐给其他任何平台。"""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "sonnet", "--output-format", "text"],
                capture_output=True, text=True, timeout=120, env=_clean_env(),
            )
            if result.returncode != 0:
                return SkillResult(False, f"扫描失败: {result.stderr[:300]}")

            raw = result.stdout.strip()
            # Parse JSON array from LLM output
            import json
            text = raw
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            text = text.strip()

            try:
                matches = json.loads(text)
            except json.JSONDecodeError:
                # Try extracting JSON array from LLM output
                start = text.find("[")
                end = text.rfind("]") + 1
                if start >= 0 and end > start:
                    try:
                        matches = json.loads(text[start:end])
                    except json.JSONDecodeError:
                        # Fallback: return raw text
                        return SkillResult(True, f"机会扫描完成（非结构化）\n\n{raw}",
                                           {"report": raw, "matches": []})
                else:
                    # Fallback: return raw text
                    return SkillResult(True, f"机会扫描完成（非结构化）\n\n{raw}",
                                       {"report": raw, "matches": []})

            # Build human-readable summary
            lines = ["机会扫描完成，推荐如下：\n"]
            for i, m in enumerate(matches, 1):
                action_label = {"direct_submit": "直接投", "new_write": "需新写", "skip": "跳过"}.get(m.get("action", ""), "?")
                lines.append(
                    f"{i}. [{m.get('match','?')}] {m.get('venue','?')}\n"
                    f"   主题: {m.get('theme','?')} | {m.get('genre','?')} | {action_label}\n"
                    f"   {m.get('reason','')}"
                )
                if m.get("topic_suggestion"):
                    lines.append(f"   建议选题: {m['topic_suggestion']}")
                lines.append("")

            summary = "\n".join(lines)
            return SkillResult(True, summary, {"matches": matches, "report": summary})

        except subprocess.TimeoutExpired:
            return SkillResult(False, "机会扫描超时（>2min）")
        except Exception as e:
            return SkillResult(False, f"扫描异常: {e}")
