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
from collections import deque
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
    """Extended Brain with intent-aware context injection.

    Intent classification (keyword match, no LLM call):
      writing    — 需要方法论 + 纠正记录 + 稿件状态
      opportunity — 需要稿件状态（机会相关）
      general    — 最小上下文：公理 + 信号 + 技能列表
    """

    # Intent → keywords mapping (checked in order, first match wins)
    INTENT_KEYWORDS = {
        "writing": ["写", "改稿", "金线", "压缩", "展开", "初稿", "终稿",
                     "重写", "修改稿", "方法论", "6C", "陈言"],
        "opportunity": ["机会", "投稿", "征文", "刊物", "数据库", "机会库",
                         "投什么", "征稿", "首发", "一稿多投"],
        "intervene": ["修改", "改一下", "更新下", "加上", "删掉", "改代码",
                       "把", "改成", "标记为", "设为", "改下"],
        "general": [],
    }

    def __init__(self, config: dict, axioms_path: str,
                 methodology_path: str = "", corrections_path: str = ""):
        super().__init__(config, axioms_path)
        self.methodology_path = Path(methodology_path).expanduser() if methodology_path else None
        self.corrections_path = Path(corrections_path).expanduser() if corrections_path else None
        self.methodology_chars = config.get("brain", {}).get("methodology_summary_chars", 3000)

    def _load_methodology_summary(self) -> str:
        """Load a condensed version of the methodology for Brain context."""
        if not self.methodology_path or not self.methodology_path.exists():
            return ""
        content = self.methodology_path.read_text()
        return content[:self.methodology_chars]

    def _load_recent_corrections(self, n: int = 5) -> str:
        """Load recent user corrections for Brain context."""
        if not self.corrections_path or not self.corrections_path.exists():
            return ""
        records = []
        with open(self.corrections_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        if not records:
            return ""
        recent = records[-n:]
        lines = []
        for r in recent:
            ms = r.get("manuscript_id", "?")
            correction = r.get("correction", "")
            learned = r.get("agent_learned", "")
            lines.append(f"- [{ms}] {correction}")
            if learned:
                lines.append(f"  学到: {learned}")
        return "\n".join(lines)

    def _build_prompt(self, state_summary: str, memory_summary: str,
                      signals: list[dict], skills_desc: str,
                      intent: str = "general",
                      chat_history: str = "") -> str:
        """Intent-aware prompt: only inject context the intent actually needs."""
        signals_md = "\n".join(
            f"- [{s.get('type', '?')}] {s.get('content', '')}"
            for s in signals
        ) if signals else "无新信号。"

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # ── Always included (minimal core) ───────────────────
        sections = [
            f"# 身份\n文学编辑 Agent。{now}",
            f"# 公理\n{self.axioms}",
        ]

        # ── Conversation history (always include if available) ──
        if chat_history:
            sections.append(f"# 最近对话\n{chat_history}")

        sections.append(f"# 新信号\n{signals_md}")

        # ── Conditionally included by intent ─────────────────
        if intent == "writing":
            methodology = self._load_methodology_summary()
            if methodology:
                sections.append(f"# 文学方法论（摘要）\n{methodology}")
            corrections = self._load_recent_corrections()
            if corrections:
                sections.append(f"# 用户纠正\n{corrections}")
            sections.append(f"# 稿件状态\n{state_summary}")
            sections.append(f"# 行动路径\n{memory_summary}")
        elif intent == "opportunity":
            sections.append(f"# 稿件状态\n{state_summary}")
        elif intent == "intervene":
            sections.append(f"# 稿件状态\n{state_summary}")
        # "general": no extra context — axioms + signal + skills is enough

        sections.append(f"# 可用技能\n{skills_desc}")
        sections.append(
            "# 指令\n"
            "根据信号决定下一步。输出严格 JSON（不要 markdown 代码块）：\n"
            f'{{"skill": "技能名", "params": {{}}, "reason": "一句话", "priority": 0}}\n'
            "无事可做则 skill=idle。\n"
            "注意：awaiting 非空时不催促；用户消息优先处理。"
        )

        return "\n\n".join(sections)


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

        # Conversation history (recent N turns for context)
        self._chat_history: deque[dict] = deque(maxlen=20)

        # Background tasks
        self.running_tasks: dict[str, RunningTask] = {}
        self._task_counter = 0
        self._pending_matches: list[dict] = []  # scan_opportunities results
        self._heartbeat_count = 0
        self._inbox_check_interval = 15  # check inbox every 15 heartbeats (~30min at 2min interval)

        # Register status callback
        self.gateway.status_callback = self._build_status_message

    # ========== Conversation History ==========

    async def _reply(self, chat_id: int, text: str, buttons=None):
        """Send a reply and record it to conversation history."""
        self._record_chat("agent", text)
        await self.gateway.send_message(chat_id, text, buttons)

    def _record_chat(self, role: str, content: str):
        """Record a message to conversation history."""
        self._chat_history.append({
            "role": role,
            "content": content[:500],  # truncate very long messages
            "time": datetime.now().strftime("%H:%M"),
        })

    def _chat_history_text(self) -> str:
        """Format recent conversation history for Brain/skill context."""
        if not self._chat_history:
            return ""
        lines = []
        for msg in self._chat_history:
            prefix = "用户" if msg["role"] == "user" else "Agent"
            lines.append(f"[{msg['time']}] {prefix}: {msg['content']}")
        return "\n".join(lines)

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

    async def _restart(self, chat_id: int = None):
        """Graceful restart: write .restart marker, then exit main loop.
        run.sh detects the marker and relaunches the process."""
        if chat_id:
            await self.gateway.send_message(chat_id, "代码已更新，正在重启...")
        restart_marker = AGENT_DIR / ".restart"
        restart_marker.write_text(datetime.now().isoformat())
        logger.info("Restart marker written, shutting down for restart")
        self.running = False  # main_loop exits → stop() → run.sh detects .restart

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
                self._heartbeat_count += 1
                # Periodic inbox check
                if self._heartbeat_count % self._inbox_check_interval == 0:
                    await self._periodic_inbox_check()
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

    async def _periodic_inbox_check(self):
        """Periodically check inbox for venue replies. Notify only if new mail found."""
        skill = self.skills.get("check_inbox")
        if not skill:
            return
        try:
            result = await asyncio.wait_for(
                skill.execute({}, self.config), timeout=30
            )
            if result.success and result.data and result.data.get("new_count", 0) > 0:
                chat_id = self.config["telegram"].get("user_id")
                if chat_id:
                    await self._reply(int(chat_id), f"📬 {result.message}")
                logger.info("Inbox check: %d new emails", result.data["new_count"])
        except Exception as e:
            logger.debug("Periodic inbox check error: %s", e)

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

        # Record to conversation history
        self._record_chat("user", text)

        # Quick status check
        if any(kw in text for kw in ["进度", "状态", "怎么样了", "到哪了", "投稿状态"]):
            msg = self._build_status_message()
            if chat_id:
                await self.gateway.send_message(chat_id, msg)
            return

        # Check inbox trigger
        if any(kw in text for kw in ["查邮件", "有回复吗", "邮件", "收件箱",
                                      "check inbox", "回信"]):
            action = BrainAction(
                skill="check_inbox",
                params={},
                reason="用户请求检查收件箱",
                priority=1,
            )
            await self._spawn_background_task(action, chat_id)
            return

        # Scan opportunities trigger
        if any(kw in text for kw in ["扫描", "有什么可以投", "有什么可以写",
                                      "下一篇", "找机会", "看看机会", "投什么"]):
            action = BrainAction(
                skill="scan_opportunities",
                params={},
                reason="用户请求扫描投稿机会",
                priority=1,
            )
            await self._spawn_background_task(action, chat_id)
            return

        # Refresh opportunities trigger (web search for new opportunities)
        if any(kw in text for kw in ["更新机会", "刷新", "搜索新机会",
                                      "找新征文", "搜新的"]):
            action = BrainAction(
                skill="refresh_opportunities",
                params={},
                reason="用户请求搜索新征文机会",
                priority=1,
            )
            await self._spawn_background_task(action, chat_id)
            return

        # Check for correction pattern: "纠正: ..." or "修改: ..."
        if self._is_correction(text):
            await self._record_correction(text, chat_id)
            return

        # Check for result report: "采用" or "拒稿"
        if self._is_result_report(text):
            await self._handle_result(text, chat_id)
            return

        # Intervene trigger: user wants to modify files
        intervene_keywords = ["修改", "改一下", "更新下", "加上", "删掉",
                              "改代码", "改成", "标记为", "设为", "改下"]
        if any(kw in text for kw in intervene_keywords):
            # Include recent chat history so sonnet understands context
            history = self._chat_history_text()
            instruction = f"{text}\n\n## 最近对话上下文\n{history}" if history else text
            action = BrainAction(
                skill="intervene",
                params={"instruction": instruction},
                reason=f"用户请求修改: {text[:60]}",
                priority=1,
            )
            await self._spawn_background_task(action, chat_id)
            return

        # Let Brain decide (with conversation history for context)
        action = self.brain.think(
            state_summary=self.state.status_summary(),
            memory_summary=self.memory.recent_paths_markdown(3),
            signals=[signal],
            skills_desc=self.skills.list_descriptions(),
            chat_history=self._chat_history_text(),
        )
        logger.info("Brain决策: %s — %s", action.skill, action.reason)

        if action.skill == "idle":
            if chat_id:
                await self._reply(chat_id, action.reason)
        elif action.skill == "notify":
            msg = action.params.get("message", action.reason)
            if chat_id:
                await self._reply(chat_id, msg)
        else:
            # If Brain chose intervene, ensure instruction includes user text + context
            if action.skill == "intervene":
                history = self._chat_history_text()
                instruction = action.params.get("instruction", text)
                if history and "对话上下文" not in instruction:
                    instruction = f"{instruction}\n\n## 最近对话上下文\n{history}"
                action.params["instruction"] = instruction
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

        elif callback == "scan_after_refresh":
            action = BrainAction(
                skill="scan_opportunities",
                params={},
                reason="刷新后自动扫描匹配",
                priority=1,
            )
            await self._spawn_background_task(action, chat_id)

        elif callback.startswith("pick_opp:"):
            opp_id = callback.split(":", 1)[1]
            await self._handle_pick_opportunity(opp_id, chat_id)

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

    # ========== Opportunity → Manuscript Creation ==========

    async def _handle_pick_opportunity(self, opp_id: str, chat_id: int = None):
        """User picked an opportunity from scan results. Create manuscript and start flow."""
        matches = getattr(self, "_pending_matches", [])
        match = next((m for m in matches if m.get("id") == opp_id), None)

        if not match:
            if chat_id:
                await self.gateway.send_message(chat_id, f"未找到机会: {opp_id}")
            return

        venue = match.get("venue", "")
        genre = match.get("genre", "散文")
        theme = match.get("theme", "")
        action_type = match.get("action", "new_write")
        topic = match.get("topic_suggestion", theme)
        word_count = match.get("word_count", "2500")
        email = match.get("email", "")

        if action_type == "direct_submit":
            # Already have a work — find it and go to submission
            active = self.state.get_active()
            # Try to find existing work matching this venue
            if chat_id:
                await self.gateway.send_message(
                    chat_id,
                    f"准备直接投稿到 {venue}\n"
                    f"主题: {theme}\n\n"
                    f"我来生成投稿邮件草稿。"
                )
            # Find the work — for now use the first existing work
            lit_root = Path(self.config["paths"]["works_dir"]).expanduser()
            work_dirs = [d for d in lit_root.iterdir() if d.is_dir() and not d.name.startswith(".")] if lit_root.exists() else []
            if work_dirs:
                ms_id = opp_id
                ms = Manuscript(
                    id=ms_id, title=work_dirs[0].name, venue=venue,
                    genre=genre, work_dir=str(work_dirs[0]),
                    opportunity=theme, word_count=word_count,
                )
                self.state.add_manuscript(ms)
                self.state.update_status(ms_id, ManuscriptStatus.SUBMISSION_READY)
                self.state.update_field(ms_id, submission_email=email)
                action = BrainAction(
                    skill="draft_submission",
                    params={"work_dir": str(work_dirs[0]), "venues": venue},
                    reason=f"直接投稿: {work_dirs[0].name} → {venue}",
                    priority=1,
                )
                await self._spawn_background_task(action, chat_id, manuscript_id=ms_id)
            else:
                if chat_id:
                    await self.gateway.send_message(chat_id, "没有找到已完成的作品，需要先写一篇。")
        else:
            # New write — create manuscript, start gathering
            ms_id = opp_id
            ms = Manuscript(
                id=ms_id, title=topic or theme, venue=venue,
                genre=genre, opportunity=theme, word_count=word_count,
            )
            self.state.add_manuscript(ms)
            self.state.update_field(ms_id, submission_email=email)
            self.state.update_status(ms_id, ManuscriptStatus.TOPIC_PROPOSED)

            if chat_id:
                await self.gateway.send_message(
                    chat_id,
                    f"选题已创建:\n\n"
                    f"目标: {venue}\n"
                    f"主题: {theme}\n"
                    f"体裁: {genre}\n"
                    f"建议选题: {topic}\n"
                    f"字数: ~{word_count}字\n\n"
                    f"确认开始？",
                    buttons=[[
                        {"text": "开始采集素材", "callback": f"confirm_topic:{ms_id}"},
                        {"text": "换一个", "callback": "hold"},
                    ]],
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

            if action.skill == "intervene":
                restart_needed = result.data.get("restart_needed", False)
                await self._reply(chat_id, text)
                if restart_needed:
                    await self._restart(chat_id)
                return

            if action.skill == "scan_opportunities":
                matches = result.data.get("matches", []) if result.data else []
                if matches:
                    # Store matches for later pickup
                    self._pending_matches = matches
                    # Build buttons for each match
                    buttons = []
                    for m in matches[:4]:  # Telegram max 4 buttons per row
                        action_label = "直接投" if m.get("action") == "direct_submit" else "写"
                        buttons.append({
                            "text": f"{action_label}: {m.get('venue', '?')[:12]}",
                            "callback": f"pick_opp:{m.get('id', 'unknown')}",
                        })
                    btn_rows = [[b] for b in buttons]  # One button per row for readability
                    await self.gateway.send_message(chat_id, text, btn_rows)
                else:
                    await self.gateway.send_message(chat_id, text)
                return

            if action.skill == "refresh_opportunities":
                new_found = result.data.get("new_found", 0) if result.data else 0
                updated = result.data.get("updated", 0) if result.data else 0
                buttons = []
                if new_found > 0 or updated > 0:
                    buttons.append([
                        {"text": "扫描匹配", "callback": "scan_after_refresh"},
                        {"text": "先看看", "callback": "hold"},
                    ])
                await self.gateway.send_message(chat_id, text, buttons if buttons else None)
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
            await self._reply(chat_id, f"失败: {action.skill}\n{err_msg}")

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

        # Last search date
        search_log = Path(
            self.config["paths"].get("search_log_file", "")
        ).expanduser()
        if search_log.exists():
            last_line = ""
            for line in open(search_log):
                if line.strip():
                    last_line = line.strip()
            if last_line:
                try:
                    last_search = json.loads(last_line)
                    ts = last_search.get("timestamp", "")[:10]
                    days_ago = (datetime.now() - datetime.fromisoformat(
                        last_search["timestamp"])).days
                    stale = " ⚠️ 超过7天未搜索" if days_ago > 7 else ""
                    lines.append(f"上次搜索: {ts} ({days_ago}天前){stale}")
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass

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
