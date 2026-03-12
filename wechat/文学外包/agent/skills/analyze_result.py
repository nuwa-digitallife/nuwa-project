"""
Skill: 分析投稿结果
采用/拒稿 → 压缩经验 → 更新刊物偏好画像

输入：manuscript_id + result (采用/拒稿)
输出：经验压缩 + 方法论改进提案（如有）
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class AnalyzeResultSkill(Skill):
    name = "analyze_result"
    description = "分析投稿结果（采用/拒稿），压缩经验，提出方法论改进提案"
    estimated_duration = "5min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        manuscript_id = params.get("manuscript_id", "")
        result_type = params.get("result", "")  # 采用 or 拒稿
        feedback = params.get("feedback", "")    # 编辑反馈（如有）

        if not manuscript_id or not result_type:
            return SkillResult(False, "需要 manuscript_id 和 result 参数")

        lit_root = Path(config["paths"]["lit_root"]).expanduser()

        # Load manuscript state
        state_file = Path(config["paths"]["state_file"]).expanduser()
        manuscript_info = self._load_manuscript(state_file, manuscript_id)

        # Load the manuscript text
        manuscript_text = ""
        if manuscript_info and manuscript_info.get("work_dir"):
            work_dir = Path(manuscript_info["work_dir"]).expanduser()
            for name in ("final.md", "article_v1.md"):
                f = work_dir / name
                if f.exists():
                    manuscript_text = f.read_text()[:3000]
                    break

        # Load corrections history
        corrections_file = Path(config["paths"]["corrections_file"]).expanduser()
        corrections = self._load_corrections(corrections_file, manuscript_id)

        # Load methodology summary
        methodology_file = Path(config["paths"]["methodology_file"]).expanduser()
        methodology = ""
        if methodology_file.exists():
            methodology = methodology_file.read_text()[:2000]

        # Build analysis prompt
        prompt = f"""你是文学编辑 Agent 的经验分析模块。

## 投稿结果
稿件：{manuscript_id}
标题：{manuscript_info.get('title', '未知') if manuscript_info else '未知'}
目标刊物：{manuscript_info.get('venue', '未知') if manuscript_info else '未知'}
体裁：{manuscript_info.get('genre', '未知') if manuscript_info else '未知'}
结果：{result_type}
{'编辑反馈：' + feedback if feedback else '无编辑反馈'}

## 稿件摘要（前3000字）
{manuscript_text[:3000] if manuscript_text else '（稿件内容不可用）'}

## 该稿件的用户纠正记录
{corrections if corrections else '无纠正记录'}

## 当前文学方法论（摘要）
{methodology[:2000]}

## 要求

请分析此次投稿结果，输出：

1. **原因分析**：为什么被采用/拒稿？从金线质量、语言、体裁匹配、刊物偏好等角度分析
2. **经验压缩**：一句话总结这次经验（存入路径记忆）
3. **刊物画像更新**：这次结果揭示了该刊物什么偏好？
4. **方法论提案**：是否需要更新文学方法论？如果是，具体改什么？（如：给陈言清单加词、调整6C权重、新增写作铁律等）
5. **下一步建议**：接下来应该怎么做？（换刊物重投 / 修改后重投 / 写新稿 / 其他）

输出格式：
===ANALYSIS===
（原因分析）

===COMPRESSION===
（一句话经验压缩）

===VENUE_PROFILE===
（刊物画像更新）

===METHODOLOGY_PROPOSAL===
（方法论改进提案，如果没有写"无需修改"）

===NEXT_ACTION===
（下一步建议）"""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "haiku", "--output-format", "text"],
                capture_output=True, text=True, timeout=120, env=_clean_env(),
            )
            if result.returncode != 0:
                return SkillResult(False, f"结果分析失败: {result.stderr[:300]}")

            output = result.stdout.strip()

            # Save analysis to work dir
            if manuscript_info and manuscript_info.get("work_dir"):
                work_dir = Path(manuscript_info["work_dir"]).expanduser()
                if work_dir.exists():
                    analysis_file = work_dir / f"result_analysis_{result_type}.md"
                    analysis_file.write_text(
                        f"# 投稿结果分析\n\n"
                        f"结果：{result_type}\n"
                        f"分析时间：{datetime.now().isoformat()}\n\n"
                        f"---\n\n{output}"
                    )

            # Extract compression for memory
            compression = ""
            if "===COMPRESSION===" in output:
                parts = output.split("===COMPRESSION===")
                if len(parts) > 1:
                    next_section = parts[1].split("===")[0] if "===" in parts[1] else parts[1]
                    compression = next_section.strip()

            return SkillResult(
                True,
                f"结果分析完成 ({manuscript_id}: {result_type})\n\n{output[:2000]}",
                {"compression": compression, "full_analysis": output},
            )
        except subprocess.TimeoutExpired:
            return SkillResult(False, "结果分析超时（>2min）")
        except Exception as e:
            return SkillResult(False, f"结果分析异常: {e}")

    def _load_manuscript(self, state_file: Path, manuscript_id: str) -> dict:
        if not state_file.exists():
            return {}
        for line in state_file.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                if d.get("id") == manuscript_id:
                    return d
        return {}

    def _load_corrections(self, corrections_file: Path, manuscript_id: str) -> str:
        if not corrections_file.exists():
            return ""
        lines = []
        for line in corrections_file.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("manuscript_id") == manuscript_id:
                    lines.append(f"- {r.get('correction', '')}")
        return "\n".join(lines)
