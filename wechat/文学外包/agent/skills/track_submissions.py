"""
Skill: 投稿状态跟踪
包装 lit_status.py
"""

import asyncio
import sys
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class TrackSubmissionsSkill(Skill):
    name = "track_submissions"
    description = "查看所有投稿状态汇总"
    estimated_duration = "<1s"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        lit_root = Path(config["paths"]["lit_root"]).expanduser()

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, str(lit_root / "lit_status.py"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(lit_root),
                env=_clean_env(),
            )
            stdout, stderr = await proc.communicate()

            output = stdout.decode()
            return SkillResult(True, output or "暂无投稿记录。", {"stdout": output})
        except Exception as e:
            return SkillResult(False, f"状态查询异常: {e}")
