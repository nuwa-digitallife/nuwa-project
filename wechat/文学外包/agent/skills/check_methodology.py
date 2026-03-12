"""
Skill: 方法论合规检查
读取文学方法论 → 对比当前稿件 → 出具合规报告

Uses Brain (claude -p) to compare manuscript against methodology rules.
"""

import asyncio
import subprocess
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class CheckMethodologySkill(Skill):
    name = "check_methodology"
    description = "对比终稿与文学方法论，出具合规报告（金线/6C/陈言/AI败相）"
    estimated_duration = "3min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        work_dir = params.get("work_dir", "")
        if not work_dir:
            return SkillResult(False, "需要 work_dir 参数")

        work_path = Path(work_dir).expanduser()

        # Find the manuscript file
        manuscript = None
        for name in ("final.md", "article_v1.md", "draft.md"):
            candidate = work_path / name
            if candidate.exists():
                manuscript = candidate
                break

        if not manuscript:
            return SkillResult(False, f"在 {work_dir} 中找不到稿件文件")

        manuscript_text = manuscript.read_text()[:8000]

        # Load methodology
        methodology_path = Path(config["paths"]["methodology_file"]).expanduser()
        if not methodology_path.exists():
            return SkillResult(False, f"方法论文件不存在: {methodology_path}")

        methodology = methodology_path.read_text()[:6000]

        # Build review prompt
        prompt = f"""你是一个严格的文学编辑。请对以下稿件进行方法论合规检查。

## 文学方法论（标准）

{methodology}

## 待检查稿件

{manuscript_text}

## 检查清单

请逐项检查并输出报告：

1. **金线贯穿**：核心意象是否从头到尾贯穿？有没有断裂处？
2. **6C 检查**：Concise/Clear/Complete/Consistent/Correct/Colorful 逐项评分（1-5）
3. **陈言务去**：列出所有违反"陈言务去"清单的表达（引用原文）
4. **AI六大败相**：匀质感/安全洞察/对称强迫症/情感宣告/万能连接词/没有冒犯性
5. **总体评级**：通过 / 小修 / 大修 / 重写

格式要求：每项用一行摘要，发现问题的列出具体位置和建议修改。"""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "haiku", "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=120,
                env=_clean_env(),
            )
            if result.returncode == 0:
                report = result.stdout.strip()
                return SkillResult(
                    True,
                    f"方法论合规检查完成\n\n{report}",
                    {"report": report, "manuscript": str(manuscript)},
                )
            else:
                return SkillResult(
                    False,
                    f"合规检查失败: {result.stderr[:300]}",
                )
        except subprocess.TimeoutExpired:
            return SkillResult(False, "合规检查超时（>2min）")
        except Exception as e:
            return SkillResult(False, f"合规检查异常: {e}")
