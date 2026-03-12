"""
Skill: 展开写作 (Pass 1-3)
金线 → 初稿 → 自检 → 终稿 + DOCX
"""

import asyncio
import sys
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class WriteManuscriptSkill(Skill):
    name = "write_manuscript"
    description = "展开写作：金线→初稿→自检→终稿（lit_write.py Pass 1-3）"
    estimated_duration = "30min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        work_dir = params.get("work_dir", "")
        start_pass = params.get("start_pass", 1)
        venue = params.get("venue", "")
        genre = params.get("genre", "散文")
        word_count = params.get("word_count", "")

        if not work_dir:
            return SkillResult(False, "需要 work_dir 参数（作品目录）")

        lit_root = Path(config["paths"]["lit_root"]).expanduser()
        cmd = [
            sys.executable, str(lit_root / "lit_write.py"),
            "--work-dir", work_dir,
            "--pass", str(start_pass),
        ]
        if venue:
            cmd.extend(["--venue", venue])
        if genre:
            cmd.extend(["--genre", genre])
        if word_count:
            cmd.extend(["--word-count", str(word_count)])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path(config["paths"]["project_root"]).expanduser()),
                env=_clean_env(),
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                summary = self._read_final(work_dir)
                msg = summary or f"写作完成: {work_dir}"
                return SkillResult(True, msg, {"stdout": stdout.decode()[-500:]})
            else:
                return SkillResult(
                    False,
                    f"写作失败 (code={proc.returncode})",
                    {"stderr": stderr.decode()[-500:]},
                )
        except Exception as e:
            return SkillResult(False, f"写作异常: {e}")

    def _read_final(self, work_dir: str) -> str:
        """Read final.md summary."""
        work_path = Path(work_dir).expanduser()
        final = work_path / "final.md"
        if final.exists():
            content = final.read_text()
            # Extract first 200 chars as preview
            preview = content[:200].strip()
            char_count = len(content)
            return (
                f"终稿完成: {work_path.name}\n"
                f"字数: ~{char_count}\n"
                f"预览: {preview}..."
            )
        return ""
