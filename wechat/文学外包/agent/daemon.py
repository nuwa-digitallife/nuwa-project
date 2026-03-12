#!/usr/bin/env python3
"""
Editor Agent Daemon — 女娲第二个数字生命

文学编辑 Agent：从征文机会到终稿投递的全生命周期管理。
复用 Agent PM 的基础设施（Brain/Gateway/Memory），换 DNA/Skills/State。

Architecture: 主循环永远不阻塞。长时间技能作为后台 task 运行。

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

# ── Path setup ────────────────────────────────────────────
AGENT_DIR = Path(__file__).resolve().parent
LIT_ROOT = AGENT_DIR.parent
PROJECT_ROOT = LIT_ROOT.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from wechat.agent.brain import Brain, BrainAction
from wechat.agent.gateway import TelegramGateway, Signal
from wechat.agent.memory import MemoryManager
from wechat.agent.skills import SkillResult
from wechat.文学外包.agent.state import ManuscriptStateManager, Manuscript, ManuscriptStatus
from wechat.文学外包.agent.skills import create_editor_registry

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("editor.daemon")


@dataclass
class RunningTask:
    """A skill running in background."""
    task_id: str
    skill_name: str
    action: BrainAction
    asyncio_task: asyncio.Task
    manuscript_id: Optional[str] = None
    chat_id: Optional[int] = None
    started: str = field(default_factory=lambda: datetime.now().isoformat())


class EditorBrain(Brain):
    """Extended Brain that injects methodology + corrections into prompt."""

    def __init__(self, config: dict, axioms_path: str,
                 methodology_path: str = "", corrections_path: str = ""):
        super().__init__(config, axioms_path)
        self.methodology_path = Path(methodology_path).expanduser() if methodology_path else None
        self.corrections_path = Path(corrections_path).expanduser() if corrections_path else None
        self.methodology_chars = config.get("brain", {}).get("methodology_summary_chars", 3000)

    def _load_methodology_summary(self) -> str:
        """Load a condensed version of the methodology for Brain context."""
        if not self.methodology_path or not self.methodology_path.exists():
            return "方法论文件未找到。"
        content = self.methodology_path.read_text()
        # Take first N chars as summary (covers core principles)
        return content[:self.methodology_chars]

    def _load_recent_corrections(self, n: int = 10) -> str:
        """Load recent user corrections for Brain context."""
        if not self.corrections_path or not self.corrections_path.exists():
            return "暂无纠正记录。"
        records = []
        with open(self.corrections_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        if not records:
            return "暂无纠正记录。"
        recent = records[-n:]
        lines = []
        for r in recent:
            ms = r.get("manuscript_id", "?")
            correction = r.get("correction", "")
            learned = r.get("agent_learned", "")
            lines.append(f"- [{ms}] 纠正: {correction}")
            if learned:
                lines.append(f"  学到: {learned}")
        return "\n".join(lines)

    def _build_prompt(self, state_summary: str, memory_summary: str,
                      signals: list[dict], skills_desc: str) -> str:
        """Override to inject methodology + corrections."""
        signals_md = "\n".join(
            f"- [{s.get('type', '?')}] {s.get('content', '')}"
            for s in signals
        ) if signals else "无新信号。"

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        methodology = self._load_methodology_summary()
        corrections = self._load_recent_corrections()

        return f"""# 你的身份

你是文学编辑 Agent，负责从选题到投稿的全流程管理。当前时间：{now}

# 你的公理

{self.axioms}

# 文学方法论（你的圣经，摘要）

{methodology}

# 最近的用户纠正（你必须学习这些）

{corrections}

# 当前稿件状态

{state_summary}

# 最近行动路径

{memory_summary}

# 新信号

{signals_md}

# 可用技能

{skills_desc}

# 指令

根据上述信息，决定你的下一步行动。

输出严格 JSON（不要 markdown 代码块）：
{{"skill": "技能名", "params": {{}}, "reason": "一句话理由", "priority": 0}}

如果当前没有需要处理的事项，输出：
{{"skill": "idle", "params": {{}}, "reason": "原因", "priority": 0}}

注意：
- 如果有稿件等待用户确认（awaiting 非空），不要催促，等用户回复
- 如果有新的用户消息，优先处理
- 所有写作决策必须可追溯到文学方法论
- 如果你的判断偏离方法论，用 notify 技能告知用户
- priority: 0=普通, 1=高（用户主动发消息）, 2=紧急
"""


class EditorAgent:
    """The Editor Agent — a persistent digital life for literary manuscript management."""

    def __init__(self, config_path: str, dry_run: bool = False):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.dry_run = dry_run

        # Core components (shared infra, different DNA)
        self.gateway = TelegramGateway(self.config)
        self.brain = EditorBrain(
            self.config,
            axioms_path=str(AGENT_DIR / "axioms.md"),
            methodology_path=self.config["paths"].get("methodology_file", ""),
            corrections_path=self.config["paths"].get("corrections_file", ""),
        )
        self.state = ManuscriptStateManager(self.config["paths"]["state_file"])
        self.memory = MemoryManager(
            paths_file=self.config["paths"]["paths_file"],
        )
        self.skills = create_editor_registry()

        # Runtime state
        self.heartbeat_interval = self.config.get("budget", {}).get(
            "heartbeat_interval", 120
        )
        self.running = False
        self.skill_count_today = 0
        self.skill_limit = self.config.get("budget", {}).get("daily_skill_limit", 8)
        self._last_date = datetime.now().date()

        # Background tasks
        self.running_tasks: dict[str, RunningTask] = {}
        self._task_counter = 0

        # Register status callback
        self.gateway.status_callback = self._build_status_message

    # ========== Lifecycle ==========

    async def start(self):
        logger.info("=" * 50)
        logger.info("Editor Agent 启动")
        logger.info("=" * 50)

        await self.gateway.start()
        self.running = True
        await self.gateway.send_notification("文学编辑在线 ✓\n准备就绪，等待指令。")

        try:
            await self._main_loop()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        for rt in self.running_tasks.values():
            rt.asyncio_task.cancel()
        await self.gateway.send_notification("文学编辑下线。")
        await self.gateway.stop()
        logger.info("Editor Agent 已停止")

    # ========== Main Loop ==========

    async def _main_loop(self):
        while self.running:
            today = datetime.now().date()
            if today != self._last_date:
                self.skill_count_today = 0
                self._last_date = today

            signal = await self.gateway.get_next_signal(
                timeout=self.heartbeat_interval
            )

            if signal is None:
                self._reap_completed_tasks()
                continue

            signals = [signal.to_dict()]
            try:
                while True:
                    extra = await asyncio.wait_for(
                        self.gateway.signal_queue.get(), timeout=0.3
                    )
                    signals.append(extra.to_dict())
            except asyncio.TimeoutError:
                pass

            await self._process_signals(signals)

    async def _process_signals(self, signals: list[dict]):
        for s in signals:
            if s["type"] == "callback":
                await self._handle_callback_signal(s)
            elif s["type"] == "user_message":
                await self._handle_message_signal(s)
            elif s["type"] == "user_url":
                await self._handle_url_signal(s)

    # ========== Signal Handlers ==========

    async def _handle_message_signal(self, signal: dict):
        """User sent plain text. Use Brain to decide."""
        chat_id = signal["data"].get("chat_id")
        text = signal["content"]

        # Quick status check
        if any(kw in text for kw in ["进度", "状态", "怎么样了", "到哪了", "投稿状态"]):
            msg = self._build_status_message()
            if chat_id:
                await self.gateway.send_message(chat_id, msg)
            return

        # Check for correction pattern: "纠正: ..." or "修改: ..."
        if self._is_correction(text):
            await self._record_correction(text, chat_id)
            return

        # Check for result report: "采用" or "拒稿"
        if self._is_result_report(text):
            await self._handle_result(text, chat_id)
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
            if chat_id:
                await self.gateway.send_message(chat_id, action.reason)
        elif action.skill == "notify":
            msg = action.params.get("message", action.reason)
            if chat_id:
                await self.gateway.send_message(chat_id, msg)
        else:
            await self._spawn_background_task(action, chat_id)

    async def _handle_callback_signal(self, signal: dict):
        """User clicked a button."""
        callback = signal["content"]
        chat_id = signal["data"].get("chat_id")

        if callback.startswith("confirm_topic:"):
            ms_id = callback.split(":", 1)[1]
            ms = self.state.get_manuscript(ms_id)
            if ms:
                self.state.update_status(ms_id, ManuscriptStatus.MATERIAL_GATHERING)
                action = BrainAction(
                    skill="gather_materials",
                    params={
                        "topic": ms.opportunity or ms.title or ms_id,
                        "venue": ms.venue,
                        "genre": ms.genre,
                        "work_title": ms.title or ms_id,
                    },
                    reason=f"用户确认选题，开始采集素材: {ms_id}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id, manuscript_id=ms_id)
            else:
                if chat_id:
                    await self.gateway.send_message(chat_id, f"稿件 {ms_id} 未找到")

        elif callback.startswith("start_goldline:"):
            ms_id = callback.split(":", 1)[1]
            ms = self.state.get_manuscript(ms_id)
            if ms:
                action = BrainAction(
                    skill="compress_goldline",
                    params={
                        "work_dir": ms.work_dir,
                        "materials_dir": ms.materials_dir or ms.work_dir,
                        "venue": ms.venue,
                        "genre": ms.genre,
                        "word_count": ms.word_count,
                    },
                    reason=f"开始金线压缩: {ms_id}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id, manuscript_id=ms_id)

        elif callback.startswith("confirm_goldline:"):
            ms_id = callback.split(":", 1)[1]
            ms = self.state.get_manuscript(ms_id)
            if ms:
                self.state.update_status(ms_id, ManuscriptStatus.WRITING)
                action = BrainAction(
                    skill="write_manuscript",
                    params={
                        "work_dir": ms.work_dir,
                        "venue": ms.venue,
                        "genre": ms.genre,
                        "word_count": ms.word_count,
                    },
                    reason=f"用户确认金线，开始写作: {ms_id}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id, manuscript_id=ms_id)

        elif callback.startswith("approve_draft:"):
            ms_id = callback.split(":", 1)[1]
            ms = self.state.get_manuscript(ms_id)
            if ms:
                self.state.update_status(ms_id, ManuscriptStatus.SUBMISSION_READY)
                if chat_id:
                    await self.gateway.send_message(
                        chat_id,
                        f"终稿已确认: {ms.title or ms_id}\n"
                        f"目标刊物: {ms.venue}\n\n"
                        f"要我生成投稿邮件草稿吗？",
                        buttons=[[
                            {"text": "生成草稿", "callback": f"draft_email:{ms_id}"},
                            {"text": "先等等", "callback": "hold"},
                        ]],
                    )

        elif callback.startswith("draft_email:"):
            ms_id = callback.split(":", 1)[1]
            ms = self.state.get_manuscript(ms_id)
            if ms:
                action = BrainAction(
                    skill="draft_submission",
                    params={
                        "work_dir": ms.work_dir,
                        "venues": ms.venue,
                    },
                    reason=f"生成投稿邮件: {ms_id}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id, manuscript_id=ms_id)

        elif callback.startswith("revise:"):
            ms_id = callback.split(":", 1)[1]
            ms = self.state.get_manuscript(ms_id)
            if ms:
                self.state.update_status(ms_id, ManuscriptStatus.REVISION)
                if chat_id:
                    await self.gateway.send_message(
                        chat_id,
                        f"请告诉我你的修改意见（直接发文字）:"
                    )

        elif callback == "hold":
            if chat_id:
                await self.gateway.send_message(chat_id, "好的，有需要随时告诉我。")

        else:
            logger.warning("未知回调: %s", callback)

    async def _handle_url_signal(self, signal: dict):
        """User sent a URL — could be reference material."""
        chat_id = signal["data"].get("chat_id")
        url = signal["content"]
        instructions = signal["data"].get("instructions", "")

        if chat_id:
            await self.gateway.send_message(
                chat_id,
                f"收到链接: {url[:60]}...\n"
                f"已记录为参考素材。需要我用这个素材写什么吗？"
            )

    # ========== Correction System (造人过程) ==========

    def _is_correction(self, text: str) -> bool:
        prefixes = ["纠正:", "纠正：", "修改:", "修改：", "不对:", "不对：", "correction:"]
        return any(text.strip().lower().startswith(p) for p in prefixes)

    async def _record_correction(self, text: str, chat_id: int = None):
        """Record user correction to corrections.jsonl."""
        # Find the most recent active manuscript
        active = self.state.get_active()
        ms_id = active[-1].id if active else "unknown"

        # Parse correction text
        correction = text.split(":", 1)[1].strip() if ":" in text else text

        record = {
            "timestamp": datetime.now().isoformat(),
            "manuscript_id": ms_id,
            "stage": active[-1].status.value if active else "unknown",
            "correction": correction,
            "agent_learned": "",  # Will be filled by Brain in future
        }

        corrections_path = Path(self.config["paths"]["corrections_file"]).expanduser()
        corrections_path.parent.mkdir(parents=True, exist_ok=True)
        with open(corrections_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info("纠正记录: %s — %s", ms_id, correction[:80])

        if chat_id:
            await self.gateway.send_message(
                chat_id,
                f"已记录纠正 ({ms_id}): {correction[:100]}\n"
                f"我会在后续写作中学习这个教训。"
            )

    # ========== Result Handling ==========

    def _is_result_report(self, text: str) -> bool:
        keywords = ["采用", "拒稿", "录用", "退稿", "accepted", "rejected"]
        return any(kw in text.lower() for kw in keywords)

    async def _handle_result(self, text: str, chat_id: int = None):
        """Handle adoption/rejection report from user."""
        # Find manuscripts in TRACKING status
        tracking = self.state.get_by_status(ManuscriptStatus.TRACKING)
        submitted = self.state.get_by_status(ManuscriptStatus.SUBMITTED)
        candidates = tracking + submitted

        if not candidates:
            if chat_id:
                await self.gateway.send_message(chat_id, "当前没有待跟踪的稿件。")
            return

        ms = candidates[-1]  # Most recent
        is_adopted = any(kw in text for kw in ["采用", "录用", "accepted"])

        self.state.update_field(ms.id, result="采用" if is_adopted else "拒稿")
        self.state.update_status(ms.id, ManuscriptStatus.RESULT_IN)

        result_emoji = "🎉" if is_adopted else "📝"
        if chat_id:
            await self.gateway.send_message(
                chat_id,
                f"{result_emoji} 已记录: {ms.title or ms.id} → {'采用' if is_adopted else '拒稿'}\n"
                f"我会分析这次结果并压缩经验。"
            )

        # Spawn analysis
        action = BrainAction(
            skill="analyze_result",
            params={
                "manuscript_id": ms.id,
                "result": "采用" if is_adopted else "拒稿",
            },
            reason=f"分析投稿结果: {ms.id} → {'采用' if is_adopted else '拒稿'}",
            priority=0,
        )
        await self._spawn_background_task(action, chat_id, manuscript_id=ms.id)

    # ========== Background Task Management ==========

    async def _spawn_background_task(self, action: BrainAction, chat_id: int = None,
                                      manuscript_id: str = None):
        if self.dry_run:
            logger.info("[DRY RUN] Would execute: %s(%s)", action.skill, action.params)
            if chat_id:
                await self.gateway.send_message(
                    chat_id, f"[dry-run] 跳过: {action.skill}"
                )
            return

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
        task_id = f"editor_task_{self._task_counter}"

        if chat_id:
            await self.gateway.send_message(
                chat_id,
                f"开始: {skill.description}\n任务ID: {task_id}\n\n"
                f"你可以继续发消息，我在后台处理。"
            )

        self.memory.start_path(f"{action.skill}: {action.reason}")

        async_task = asyncio.create_task(
            self._run_skill_task(task_id, action, skill, chat_id, manuscript_id)
        )
        self.running_tasks[task_id] = RunningTask(
            task_id=task_id,
            skill_name=action.skill,
            action=action,
            asyncio_task=async_task,
            manuscript_id=manuscript_id,
            chat_id=chat_id,
        )
        logger.info("后台任务启动: %s (%s)", task_id, action.skill)

    async def _run_skill_task(self, task_id: str, action: BrainAction,
                               skill, chat_id: int = None,
                               manuscript_id: str = None):
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

        # Memory: observe & learn
        if self.memory.current_path:
            self.memory.current_path.add_step(
                step=action.skill,
                result="✓" if result.success else f"✗ {result.message[:80]}",
            )
        outcome = {"success": result.success, "message": result.message[:100]}
        compression = f"{action.skill}失败: {result.message[:80]}" if not result.success else ""
        self.memory.finish_path(outcome=outcome, compression=compression)

        if result.success:
            logger.info("任务完成: %s (%s)", task_id, action.skill)
        else:
            logger.warning("任务失败: %s (%s) — %s", task_id, action.skill, result.message[:80])

        # Update manuscript state based on skill result
        if manuscript_id:
            self._update_manuscript_after_skill(manuscript_id, action.skill, result)

        # Notify user
        target_chat = chat_id or self.config["telegram"].get("user_id")
        if target_chat:
            await self._notify_skill_result(int(target_chat), action, result, manuscript_id)

        self.running_tasks.pop(task_id, None)

    def _update_manuscript_after_skill(self, ms_id: str, skill_name: str, result: SkillResult):
        """Transition manuscript state based on skill outcome."""
        ms = self.state.get_manuscript(ms_id)
        if not ms:
            return

        if not result.success:
            return  # Don't transition on failure

        if skill_name == "gather_materials":
            # Save work_dir if returned by skill
            work_dir = result.data.get("work_dir", "")
            if work_dir:
                self.state.update_field(ms_id, work_dir=work_dir)
            self.state.update_status(ms_id, ManuscriptStatus.MATERIAL_GATHERING)
            # Auto-proceed to goldline compression (no user wait needed)
        elif skill_name == "compress_goldline":
            self.state.update_status(ms_id, ManuscriptStatus.GOLDLINE_READY)
        elif skill_name == "write_manuscript":
            self.state.update_status(ms_id, ManuscriptStatus.DRAFT_READY)
        elif skill_name == "draft_submission":
            self.state.update_status(ms_id, ManuscriptStatus.SUBMISSION_READY)
        elif skill_name == "analyze_result":
            self.state.update_status(ms_id, ManuscriptStatus.LEARNING)

    async def _notify_skill_result(self, chat_id: int, action: BrainAction,
                                    result: SkillResult, manuscript_id: str = None):
        """Send appropriate notification based on skill result."""
        if result.success:
            msg = result.message[:3500]
            text = f"完成: {action.skill}\n\n{msg}"

            if action.skill == "scan_opportunities":
                await self.gateway.send_message(chat_id, text)
                return

            if action.skill == "gather_materials" and manuscript_id:
                text += "\n\n素材采集完成。接下来进行金线压缩？"
                buttons = [[
                    {"text": "开始压缩", "callback": f"start_goldline:{manuscript_id}"},
                    {"text": "先看素材", "callback": "hold"},
                ]]
                await self.gateway.send_message(chat_id, text, buttons)
                return

            if action.skill == "analyze_result":
                await self.gateway.send_message(chat_id, text)
                return

            if action.skill == "compress_goldline" and manuscript_id:
                text += "\n\n确认金线？"
                buttons = [[
                    {"text": "确认金线", "callback": f"confirm_goldline:{manuscript_id}"},
                    {"text": "重新压缩", "callback": f"redo_goldline:{manuscript_id}"},
                ]]
                await self.gateway.send_message(chat_id, text, buttons)

            elif action.skill == "write_manuscript" and manuscript_id:
                text += "\n\n请审阅终稿。"
                buttons = [[
                    {"text": "通过", "callback": f"approve_draft:{manuscript_id}"},
                    {"text": "需要修改", "callback": f"revise:{manuscript_id}"},
                ]]
                await self.gateway.send_message(chat_id, text, buttons)

            elif action.skill == "draft_submission":
                text += "\n\n请在 Gmail 检查草稿后发送。发送完告诉我。"
                await self.gateway.send_message(chat_id, text)

            else:
                await self.gateway.send_message(chat_id, text)
        else:
            err_msg = result.message[:1000]
            await self.gateway.send_message(
                chat_id, f"失败: {action.skill}\n{err_msg}"
            )

    def _reap_completed_tasks(self):
        done = [tid for tid, rt in self.running_tasks.items() if rt.asyncio_task.done()]
        for tid in done:
            self.running_tasks.pop(tid, None)

    # ========== Status ==========

    def _build_status_message(self) -> str:
        lines = ["文学编辑 Agent 状态", ""]

        if self.running_tasks:
            lines.append("正在执行：")
            for rt in self.running_tasks.values():
                elapsed = (datetime.now() - datetime.fromisoformat(rt.started)).seconds
                mins = elapsed // 60
                ms_info = f" [{rt.manuscript_id}]" if rt.manuscript_id else ""
                lines.append(f"  {rt.task_id}: {rt.skill_name}{ms_info} ({mins}分钟)")
            lines.append("")

        active = self.state.get_active()
        if active:
            lines.append("稿件状态：")
            for m in active:
                emoji = {
                    "OPPORTUNITY_MATCHED": "🔍",
                    "TOPIC_PROPOSED": "💡",
                    "MATERIAL_GATHERING": "📚",
                    "GOLDLINE_READY": "✨",
                    "WRITING": "✍️",
                    "DRAFT_READY": "📝",
                    "REVISION": "🔄",
                    "SUBMISSION_READY": "📧",
                    "SUBMITTED": "📮",
                    "TRACKING": "⏳",
                    "RESULT_IN": "📬",
                    "LEARNING": "🧠",
                }.get(m.status.value, "📄")
                wait = f" ← 等你" if m.awaiting else ""
                lines.append(f"  {emoji} {m.summary()}{wait}")
            lines.append("")

        if not self.running_tasks and not active:
            lines.append("当前无任务。发个指令给我。")
            lines.append("")

        lines.append(f"今日推理: {self.brain.think_count}/{self.brain.think_limit}")
        lines.append(f"今日技能: {self.skill_count_today}/{self.skill_limit}")

        # Corrections count
        corrections_path = Path(self.config["paths"]["corrections_file"]).expanduser()
        if corrections_path.exists():
            count = sum(1 for line in open(corrections_path) if line.strip())
            lines.append(f"累计纠正: {count}条")

        return "\n".join(lines)


# ========== Entry Point ==========

async def test_telegram(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    from telegram import Bot
    bot = Bot(token=config["telegram"]["bot_token"])
    me = await bot.get_me()
    logger.info("Bot 连接成功: @%s (%s)", me.username, me.first_name)

    user_id = config["telegram"].get("user_id")
    if user_id:
        await bot.send_message(chat_id=user_id, text="文学编辑在线 ✓")
        logger.info("测试消息已发送给 user_id=%s", user_id)


def main():
    parser = argparse.ArgumentParser(description="Editor Agent — 女娲第二个数字生命")
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
        agent = EditorAgent(args.config, dry_run=args.dry_run)
        asyncio.run(agent.start())


if __name__ == "__main__":
    main()
