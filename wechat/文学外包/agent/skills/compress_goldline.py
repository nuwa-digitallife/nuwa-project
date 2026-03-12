"""
Skill: 金线压缩 (Pass 0)
素材 → 核心意象 + 洞察 + 金线
"""

import asyncio
import sys
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class CompressGoldlineSkill(Skill):
    name = "compress_goldline"
    description = "金线压缩：从素材提取核心意象和洞察（lit_write.py Pass 0）"
    estimated_duration = "5min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        materials_dir = params.get("materials_dir", "")
        venue = params.get("venue", "")
        genre = params.get("genre", "散文")
        work_dir = params.get("work_dir", "")
        word_count = params.get("word_count", "")

        if not materials_dir and not work_dir:
            return SkillResult(False, "需要 materials_dir 或 work_dir 参数")

        lit_root = Path(config["paths"]["lit_root"]).expanduser()
        cmd = [sys.executable, str(lit_root / "lit_write.py"), "--pass", "0"]

        if materials_dir:
            cmd.extend(["--materials-dir", materials_dir])
        if venue:
            cmd.extend(["--venue", venue])
        if genre:
            cmd.extend(["--genre", genre])
        if work_dir:
            cmd.extend(["--work-dir", work_dir])
        if word_count:
            cmd.extend(["--word-count", str(word_count)])

        # Non-interactive mode: skip the confirmation prompt
        cmd.append("--no-confirm")

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
                output = stdout.decode()
                # Try to read the goldline file
                goldline_content = self._read_goldline(config, work_dir, materials_dir)
                msg = goldline_content or f"金线压缩完成\n\n{output[-1500:]}"
                return SkillResult(True, msg, {"stdout": output[-500:]})
            else:
                return SkillResult(
                    False,
                    f"金线压缩失败 (code={proc.returncode})",
                    {"stderr": stderr.decode()[-500:]},
                )
        except Exception as e:
            return SkillResult(False, f"金线压缩异常: {e}")

    def _read_goldline(self, config: dict, work_dir: str, materials_dir: str) -> str:
        """Try to read goldline.md from the work directory."""
        if work_dir:
            goldline = Path(work_dir).expanduser() / "goldline.md"
            if goldline.exists():
                return goldline.read_text()[:2000]

        # If we only had materials_dir, look for the most recent work_dir
        works_dir = Path(config["paths"]["works_dir"]).expanduser()
        if works_dir.exists():
            dirs = sorted(works_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
            for d in dirs[:3]:
                goldline = d / "goldline.md"
                if goldline.exists():
                    return goldline.read_text()[:2000]
        return ""
