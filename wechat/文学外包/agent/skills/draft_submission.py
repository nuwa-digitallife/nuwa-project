"""
Skill: 生成投稿邮件草稿
包装 tools/draft_email.py → Gmail 草稿箱
"""

import asyncio
import sys
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class DraftSubmissionSkill(Skill):
    name = "draft_submission"
    description = "生成投稿邮件草稿并存入 Gmail 草稿箱"
    estimated_duration = "1min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        work_dir = params.get("work_dir", "")
        venues = params.get("venues", "")
        identity = params.get("identity", "")
        dry_run = params.get("dry_run", False)

        if not work_dir:
            return SkillResult(False, "需要 work_dir 参数")
        if not venues:
            return SkillResult(False, "需要 venues 参数（刊物名，逗号分隔）")

        lit_root = Path(config["paths"]["lit_root"]).expanduser()
        tools_dir = lit_root / "tools"
        cmd = [
            sys.executable, str(tools_dir / "draft_email.py"),
            "--work-dir", work_dir,
            "--venues", venues,
        ]
        if identity:
            cmd.extend(["--identity", identity])
        if dry_run:
            cmd.append("--dry-run")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(lit_root),
                env=_clean_env(),
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode()
                mode = "预览" if dry_run else "草稿已存入 Gmail"
                return SkillResult(
                    True,
                    f"投稿{mode}\n目标刊物: {venues}\n\n{output[-1000:]}",
                    {"stdout": output[-500:]},
                )
            else:
                return SkillResult(
                    False,
                    f"投稿草稿失败 (code={proc.returncode})",
                    {"stderr": stderr.decode()[-500:]},
                )
        except Exception as e:
            return SkillResult(False, f"投稿草稿异常: {e}")
