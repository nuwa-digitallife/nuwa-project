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
                        works_list.append(
                            f"{meta.get('title', d.name)} ({meta.get('genre', '?')}, "
                            f"~{meta.get('char_count', '?')}字, "
                            f"状态: {meta.get('status', '?')})"
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

输出匹配报告，按优先级排序。每条包含：
1. 机会名称 + 刊物
2. 匹配度（高/中/低）+ 理由
3. 建议行动（直接投现有作品 / 需要新写 / 跳过）
4. 如果需要新写，建议选题方向

只推荐匹配度为"中"或"高"的机会。已投稿的不重复推荐。"""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "haiku", "--output-format", "text"],
                capture_output=True, text=True, timeout=120, env=_clean_env(),
            )
            if result.returncode == 0:
                report = result.stdout.strip()
                return SkillResult(True, f"机会扫描完成\n\n{report}",
                                   {"report": report})
            else:
                return SkillResult(False, f"扫描失败: {result.stderr[:300]}")
        except subprocess.TimeoutExpired:
            return SkillResult(False, "机会扫描超时（>2min）")
        except Exception as e:
            return SkillResult(False, f"扫描异常: {e}")
