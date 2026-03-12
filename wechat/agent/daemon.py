#!/usr/bin/env python3
"""
Agent PM Daemon — 女娲第一个数字生命
Main event loop: perceive → think → act → observe → learn

Architecture: 主循环永远不阻塞。长时间技能作为后台 task 运行。
用户随时可以发消息、查状态、下新指令。

Usage:
    python daemon.py                    # 正常启动
    python daemon.py --test-telegram    # 测试 Telegram 连接
    python daemon.py --dry-run          # 不实际执行技能
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

# Add project root to path
AGENT_DIR = Path(__file__).parent
PROJECT_ROOT = AGENT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from wechat.agent.brain import Brain, BrainAction
from wechat.agent.gateway import TelegramGateway, Signal
from wechat.agent.memory import MemoryManager
from wechat.agent.state import StateManager, Article, ArticleStatus
from wechat.agent.skills import create_default_registry, SkillResult

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agent.daemon")


@dataclass
class RunningTask:
    """A skill running in background."""
    task_id: str
    skill_name: str
    action: BrainAction
    asyncio_task: asyncio.Task
    chat_id: Optional[int] = None
    started: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentPM:
    """The Agent PM — a persistent digital life for the WeChat content project."""

    def __init__(self, config_path: str, dry_run: bool = False):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.dry_run = dry_run

        # Core components
        self.gateway = TelegramGateway(self.config)
        self.brain = Brain(self.config, str(AGENT_DIR / "axioms.md"))
        self.state = StateManager(self.config["paths"]["state_file"])
        self.memory = MemoryManager(
            paths_file=self.config["paths"]["paths_file"],
            experience_file=str(
                Path(self.config["paths"]["wechat_root"]).expanduser()
                / "experience.jsonl"
            ),
        )
        self.skills = create_default_registry()

        # Runtime state
        self.heartbeat_interval = self.config.get("budget", {}).get(
            "heartbeat_interval", 60
        )
        self.running = False
        self.skill_count_today = 0
        self.skill_limit = self.config.get("budget", {}).get("daily_skill_limit", 10)
        self._last_date = datetime.now().date()

        # Background tasks
        self.running_tasks: dict[str, RunningTask] = {}
        self._task_counter = 0

        # Register status callback so /status responds instantly
        self.gateway.status_callback = self._build_status_message

    async def start(self):
        logger.info("=" * 50)
        logger.info("Agent PM 启动")
        logger.info("=" * 50)

        await self.gateway.start()
        self.running = True
        await self.gateway.send_notification("女娲在线 ✓\n准备就绪，等待指令。")

        try:
            await self._main_loop()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        # Cancel running tasks
        for rt in self.running_tasks.values():
            rt.asyncio_task.cancel()
        await self.gateway.send_notification("女娲下线。")
        await self.gateway.stop()
        logger.info("Agent PM 已停止")

    # ========== Main Loop (never blocks) ==========

    async def _main_loop(self):
        """Event-driven loop. Waits for signals, dispatches instantly."""
        while self.running:
            # Reset daily counters
            today = datetime.now().date()
            if today != self._last_date:
                self.skill_count_today = 0
                self._last_date = today

            # Wait for next signal (or timeout for heartbeat)
            signal = await self.gateway.get_next_signal(
                timeout=self.heartbeat_interval
            )

            if signal is None:
                # Heartbeat: no signal, check completed tasks
                self._reap_completed_tasks()
                continue

            # Drain any additional signals with short timeout
            signals = [signal.to_dict()]
            try:
                while True:
                    extra = await asyncio.wait_for(
                        self.gateway.signal_queue.get(), timeout=0.3
                    )
                    signals.append(extra.to_dict())
            except asyncio.TimeoutError:
                pass

            # Process signals (fast — never blocks)
            await self._process_signals(signals)

    async def _process_signals(self, signals: list[dict]):
        """Process signals. Fast actions inline, slow actions in background."""
        for s in signals:
            if s["type"] == "user_url":
                await self._handle_url_signal(s)
            elif s["type"] == "user_command" and s["content"] == "status":
                await self._handle_status(s)
            elif s["type"] == "callback":
                await self._handle_callback_signal(s)
            elif s["type"] == "user_message":
                await self._handle_message_signal(s)

    # ========== Signal Handlers ==========

    async def _handle_url_signal(self, signal: dict):
        """User sent URL(s). Spawn react as background task."""
        urls = signal["data"].get("urls", [signal["content"]])
        instructions = signal["data"].get("instructions", "")
        chat_id = signal["data"].get("chat_id")

        action = BrainAction(
            skill="react",
            params={
                "url": urls[0],
                "urls": urls,
                "instructions": instructions,
                "persona": "大史",
            },
            reason=f"用户发送了{len(urls)}个链接: {urls[0][:50]}",
            priority=1,
        )
        logger.info("Brain决策: %s — %s", action.skill, action.reason)
        await self._spawn_background_task(action, chat_id)

    async def _handle_status(self, signal: dict):
        """User asked for status. Reply immediately."""
        chat_id = signal["data"].get("chat_id")
        msg = self._build_status_message()
        if chat_id:
            await self.gateway.send_message(chat_id, msg)

    async def _handle_callback_signal(self, signal: dict):
        """User clicked a button."""
        callback = signal["content"]
        chat_id = signal["data"].get("chat_id")

        if callback == "approve_write":
            awaiting = self.state.get_awaiting_user()
            if awaiting:
                art = awaiting[-1]
                self.state.update_status(art.id, ArticleStatus.WRITING)
                action = BrainAction(
                    skill="write",
                    params={
                        "topic_dir": art.topic_dir,
                        "persona": art.persona,
                        "series": art.series,
                    },
                    reason=f"用户确认写作: {art.id}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id)
            else:
                await self.gateway.send_message(chat_id, "没有待确认的文章。")

        elif callback == "approve_publish":
            awaiting = self.state.get_by_status(ArticleStatus.APPROVED)
            if awaiting:
                art = awaiting[-1]
                self.state.update_status(art.id, ArticleStatus.PUBLISHING)
                action = BrainAction(
                    skill="publish",
                    params={"topic_dir": art.topic_dir},
                    reason=f"用户确认发布: {art.id}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id)
            else:
                await self.gateway.send_message(chat_id, "没有待发布的文章。")

        elif callback == "hold":
            await self.gateway.send_message(chat_id, "好的，有需要随时告诉我。")

        else:
            logger.warning("未知回调: %s", callback)

    async def _handle_message_signal(self, signal: dict):
        """User sent plain text. Use Brain to decide."""
        chat_id = signal["data"].get("chat_id")
        text = signal["content"]

        # Check if asking about running tasks
        if any(kw in text for kw in ["进度", "状态", "怎么样了", "到哪了"]):
            msg = self._build_status_message()
            await self.gateway.send_message(chat_id, msg)
            return

        # Let Brain decide
        action = self.brain.think(
            state_summary=self.state.status_summary(),
            memory_summary=self.memory.recent_paths_markdown(3),
            signals=[signal],
            skills_desc=self.skills.list_descriptions(),
        )
        logger.info("Brain决策: %s — %s", action.skill, action.reason)

        if action.skill == "idle":
            await self.gateway.send_message(chat_id, action.reason)
        elif action.skill == "notify":
            msg = action.params.get("message", "")
            await self.gateway.send_message(chat_id, msg)
        elif action.skill in ("react", "write", "select_topic", "publish"):
            await self._spawn_background_task(action, chat_id)
        else:
            await self.gateway.send_message(chat_id, f"收到: {text[:50]}")

    # ========== Background Task Management ==========

    async def _spawn_background_task(self, action: BrainAction, chat_id: int = None):
        """Spawn a skill as background asyncio.Task. Main loop stays free."""
        if self.dry_run:
            logger.info("[DRY RUN] Would execute: %s(%s)", action.skill, action.params)
            if chat_id:
                await self.gateway.send_message(
                    chat_id, f"[dry-run] 跳过: {action.skill}"
                )
            return

        # Budget check
        if self.skill_count_today >= self.skill_limit:
            msg = f"今日技能调用已达上限 ({self.skill_limit})。"
            logger.warning(msg)
            if chat_id:
                await self.gateway.send_message(chat_id, msg)
            return

        skill = self.skills.get(action.skill)
        if not skill:
            if chat_id:
                await self.gateway.send_message(chat_id, f"未知技能: {action.skill}")
            return

        self.skill_count_today += 1
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"

        # Notify user
        if chat_id:
            await self.gateway.send_message(
                chat_id,
                f"🔄 开始: {skill.description}\n任务ID: {task_id}\n\n"
                f"你可以继续发消息，我在后台处理。发 /status 查看进度。"
            )

        # Track memory path
        self.memory.start_path(f"{action.skill}: {action.reason}")

        # Spawn as background task
        async_task = asyncio.create_task(
            self._run_skill_task(task_id, action, skill, chat_id)
        )
        self.running_tasks[task_id] = RunningTask(
            task_id=task_id,
            skill_name=action.skill,
            action=action,
            asyncio_task=async_task,
            chat_id=chat_id,
        )
        logger.info("后台任务启动: %s (%s)", task_id, action.skill)

    async def _run_skill_task(self, task_id: str, action: BrainAction,
                               skill, chat_id: int = None):
        """Execute skill in background, notify on completion."""
        try:
            result = await asyncio.wait_for(
                skill.execute(action.params, self.config),
                timeout=3600,
            )
        except asyncio.TimeoutError:
            result = SkillResult(False, f"{action.skill} 超时 (>1h)")
        except asyncio.CancelledError:
            result = SkillResult(False, f"{action.skill} 被取消")
        except Exception as e:
            result = SkillResult(False, f"{action.skill} 异常: {e}")

        # Observe & learn
        if self.memory.current_path:
            self.memory.current_path.add_step(
                step=action.skill,
                result="✓" if result.success else f"✗ {result.message[:80]}",
            )
        outcome = {"success": result.success, "message": result.message[:100]}
        compression = f"{action.skill}失败: {result.message[:80]}" if not result.success else ""
        self.memory.finish_path(outcome=outcome, compression=compression)

        if result.success:
            logger.info("任务完成: %s (%s) — %s", task_id, action.skill, result.message[:80])
        else:
            logger.warning("任务失败: %s (%s) — %s", task_id, action.skill, result.message[:80])

        # Notify user
        target_chat = chat_id or self.config["telegram"].get("user_id")
        if target_chat:
            if result.success:
                # Telegram limit 4096 chars
                msg = result.message[:3500]
                text = f"✅ {action.skill} 完成\n\n{msg}"
                if action.skill == "react":
                    text += "\n\n要我继续写作吗？"
                    buttons = [[
                        {"text": "确认写作", "callback": "approve_write"},
                        {"text": "先看看", "callback": "hold"},
                    ]]
                    await self.gateway.send_message(int(target_chat), text, buttons)
                else:
                    await self.gateway.send_message(int(target_chat), text)
            else:
                err_msg = result.message[:1000]
                await self.gateway.send_message(
                    int(target_chat), f"❌ {action.skill} 失败\n{err_msg}"
                )

        # Remove from running tasks
        self.running_tasks.pop(task_id, None)

    def _reap_completed_tasks(self):
        """Clean up finished tasks."""
        done = [tid for tid, rt in self.running_tasks.items() if rt.asyncio_task.done()]
        for tid in done:
            self.running_tasks.pop(tid, None)

    # ========== Status ==========

    def _build_status_message(self) -> str:
        lines = []

        # Running tasks
        if self.running_tasks:
            lines.append("⚡ 正在执行的任务：\n")
            for rt in self.running_tasks.values():
                elapsed = (datetime.now() - datetime.fromisoformat(rt.started)).seconds
                mins = elapsed // 60
                lines.append(f"  🔄 {rt.task_id}: {rt.skill_name} (已运行 {mins}分钟)")
            lines.append("")

        # Article states
        active = self.state.get_active()
        if active:
            lines.append("📊 文章状态：\n")
            for a in active:
                emoji = {
                    "IDEA": "💡", "RESEARCHING": "🔍", "OUTLINE_READY": "📋",
                    "WRITING": "✍️", "DRAFT_READY": "📝", "APPROVED": "✅",
                    "PUBLISHING": "📤", "PUBLISHED": "🎉",
                }.get(a.status.value, "📄")
                wait = " ⏳ 等待确认" if a.awaiting == "user_review" else ""
                lines.append(f"  {emoji} {a.id} — {a.status.value}{wait}")
            lines.append("")

        if not self.running_tasks and not active:
            lines.append("💤 当前无任务。发个链接或关键词给我。")
            lines.append("")

        lines.append(f"🧠 今日推理: {self.brain.think_count}/{self.brain.think_limit}")
        lines.append(f"⚡ 今日技能: {self.skill_count_today}/{self.skill_limit}")
        return "\n".join(lines)

    def _extract_chat_id(self, signals: list[dict]) -> int | None:
        for s in signals:
            cid = s.get("data", {}).get("chat_id")
            if cid:
                return int(cid)
        return None


async def test_telegram(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    from telegram import Bot
    bot = Bot(token=config["telegram"]["bot_token"])
    me = await bot.get_me()
    logger.info("Bot 连接成功: @%s (%s)", me.username, me.first_name)

    user_id = config["telegram"].get("user_id")
    if user_id:
        await bot.send_message(chat_id=user_id, text="女娲在线 ✓")
        logger.info("测试消息已发送给 user_id=%s", user_id)
    else:
        logger.warning("未配置 user_id，无法发送测试消息。")
        logger.info("请在 Telegram 搜索 @userinfobot 获取你的 ID，然后填入 config.yaml")


def main():
    parser = argparse.ArgumentParser(description="Agent PM — 女娲第一个数字生命")
    parser.add_argument("--config", default=str(AGENT_DIR / "config.yaml"),
                        help="配置文件路径")
    parser.add_argument("--test-telegram", action="store_true",
                        help="测试 Telegram 连接")
    parser.add_argument("--dry-run", action="store_true",
                        help="不实际执行技能")
    args = parser.parse_args()

    if args.test_telegram:
        asyncio.run(test_telegram(args.config))
    else:
        agent = AgentPM(args.config, dry_run=args.dry_run)
        asyncio.run(agent.start())


if __name__ == "__main__":
    main()
