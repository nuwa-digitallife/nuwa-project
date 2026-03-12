"""
Skills registry.
Each skill wraps an existing CLI tool as an async-callable action.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agent.skills")


class SkillResult:
    def __init__(self, success: bool, message: str, data: dict = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
        }


def _clean_env() -> dict:
    """Get env dict that allows nested claude -p calls."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


class Skill:
    """Base class for all skills."""
    name: str = "base"
    description: str = ""
    estimated_duration: str = "unknown"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        raise NotImplementedError

    def describe(self) -> str:
        return f"- **{self.name}**: {self.description} (~{self.estimated_duration})"


class SkillRegistry:
    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_descriptions(self) -> str:
        return "\n".join(s.describe() for s in self.skills.values())

    def available_skills(self) -> list[str]:
        return list(self.skills.keys())


# --- Concrete Skills ---


class NotifySkill(Skill):
    name = "notify"
    description = "发送 Telegram 消息给用户"
    estimated_duration = "<1s"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        # Gateway handles actual sending; this just returns the message
        message = params.get("message", "")
        buttons = params.get("buttons", [])
        return SkillResult(
            success=True,
            message=f"通知已排队: {message[:50]}...",
            data={"message": message, "buttons": buttons, "type": "telegram"},
        )


class ReactSkill(Skill):
    name = "react"
    description = "从 URL 出发：抓取文章→调研（不写作，等用户确认）"
    estimated_duration = "15min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        url = params.get("url", "")
        persona = params.get("persona", "大史")
        series = params.get("series", "独立篇")
        instructions = params.get("instructions", "")

        if not url:
            return SkillResult(False, "缺少 url 参数")

        tools_dir = Path(config["paths"]["tools_dir"]).expanduser()
        cmd = [
            sys.executable, str(tools_dir / "react.py"),
            "--url", url,
            "--persona", persona,
            "--series", series,
            "--research-only",  # 只调研，不写作
        ]
        if instructions:
            cmd.extend(["--instructions", instructions])

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
                # Find the topic dir and read research summary
                summary = self._read_research_summary(config, stdout.decode())
                return SkillResult(True, summary or f"调研完成: {url[:50]}",
                                   {"stdout": stdout.decode()[-500:]})
            else:
                return SkillResult(False, f"React 失败 (code={proc.returncode})",
                                   {"stderr": stderr.decode()[-500:]})
        except Exception as e:
            return SkillResult(False, f"React 异常: {e}")

    def _read_research_summary(self, config: dict, stdout: str) -> str:
        """Read deep_research.md and return a brief summary."""
        import glob
        topics_dir = Path(config["paths"]["topics_dir"]).expanduser()
        # Find most recent topic dir
        dirs = sorted(topics_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
        for d in dirs[:3]:
            research = d / "素材" / "deep_research.md"
            if research.exists():
                content = research.read_text()[:2000]
                trigger = d / "素材" / "trigger_article.md"
                title = ""
                if trigger.exists():
                    first_line = trigger.read_text().split("\n")[0]
                    title = first_line.replace("#", "").strip()
                topic_dir_str = str(d)
                return (
                    f"调研完成\n\n"
                    f"选题: {d.name}\n"
                    f"原文: {title}\n"
                    f"目录: {topic_dir_str}\n\n"
                    f"--- 调研摘要 ---\n{content[:1500]}"
                )
        return ""


class SelectTopicSkill(Skill):
    name = "select_topic"
    description = "自动搜索素材并推荐选题"
    estimated_duration = "5min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        tools_dir = Path(config["paths"]["tools_dir"]).expanduser()
        cmd = [sys.executable, str(tools_dir / "topic_pipeline.py")]

        topic = params.get("topic")
        if topic:
            cmd.extend(["--topic", topic])
        if params.get("search_only"):
            cmd.append("--search-only")

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
                return SkillResult(True, "选题推荐完成",
                                   {"stdout": stdout.decode()[-1000:]})
            else:
                return SkillResult(False, f"选题失败 (code={proc.returncode})",
                                   {"stderr": stderr.decode()[-500:]})
        except Exception as e:
            return SkillResult(False, f"选题异常: {e}")


class WriteSkill(Skill):
    name = "write"
    description = "多Agent写作引擎（Pass 1→4.5）"
    estimated_duration = "45min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        topic_dir = params.get("topic_dir", "")
        persona = params.get("persona", "大史")
        series = params.get("series")

        if not topic_dir:
            return SkillResult(False, "缺少 topic_dir 参数")

        tools_dir = Path(config["paths"]["tools_dir"]).expanduser()
        cmd = [
            sys.executable, str(tools_dir / "write_engine" / "engine.py"),
            "--topic-dir", topic_dir,
            "--persona", persona,
        ]
        if series:
            cmd.extend(["--series", series])
        if params.get("start_pass"):
            cmd.extend(["--pass", str(params["start_pass"])])

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
                return SkillResult(True, f"写作完成: {topic_dir}",
                                   {"stdout": stdout.decode()[-500:]})
            else:
                return SkillResult(False, f"写作失败 (code={proc.returncode})",
                                   {"stderr": stderr.decode()[-500:]})
        except Exception as e:
            return SkillResult(False, f"写作异常: {e}")


class PublishSkill(Skill):
    name = "publish"
    description = "一键发布到微信公众号（需要 GUI 环境）"
    estimated_duration = "5min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        topic_dir = params.get("topic_dir", "")
        if not topic_dir:
            return SkillResult(False, "缺少 topic_dir 参数")

        tools_dir = Path(config["paths"]["tools_dir"]).expanduser()
        cmd = [
            sys.executable, str(tools_dir / "publish" / "one_click_publish.py"),
            "--topic-dir", topic_dir,
        ]
        if params.get("dry_run"):
            cmd.append("--dry-run")

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
                return SkillResult(True, f"发布完成: {topic_dir}",
                                   {"stdout": stdout.decode()[-500:]})
            else:
                return SkillResult(False, f"发布失败 (code={proc.returncode})",
                                   {"stderr": stderr.decode()[-500:]})
        except Exception as e:
            return SkillResult(False, f"发布异常: {e}")


class IdleSkill(Skill):
    name = "idle"
    description = "无事可做，等待下一个心跳"
    estimated_duration = "0s"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        return SkillResult(True, "空闲中")


def create_default_registry() -> SkillRegistry:
    """Create registry with all built-in skills."""
    registry = SkillRegistry()
    registry.register(NotifySkill())
    registry.register(ReactSkill())
    registry.register(SelectTopicSkill())
    registry.register(WriteSkill())
    registry.register(PublishSkill())
    registry.register(IdleSkill())
    return registry
