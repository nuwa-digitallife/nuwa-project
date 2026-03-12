"""
Gateway: Telegram bot message routing.
Receives user messages, converts to signals, sends notifications.
"""

import asyncio
import logging
import re
from typing import Callable, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

logger = logging.getLogger("agent.gateway")


class Signal:
    """A signal from the outside world."""
    def __init__(self, type: str, content: str, data: dict = None):
        self.type = type      # "user_message", "user_url", "user_command", "callback", "timer"
        self.content = content
        self.data = data or {}

    def to_dict(self) -> dict:
        return {"type": self.type, "content": self.content, "data": self.data}


class TelegramGateway:
    def __init__(self, config: dict):
        self.bot_token = config["telegram"]["bot_token"]
        self.authorized_user = config["telegram"].get("user_id")
        self.signal_queue: asyncio.Queue[Signal] = asyncio.Queue()
        self.app: Optional[Application] = None
        self._response_futures: dict[str, asyncio.Future] = {}
        self.status_callback: Optional[Callable] = None  # daemon sets this

    async def start(self):
        """Initialize and start the Telegram bot."""
        self.app = (
            Application.builder()
            .token(self.bot_token)
            .build()
        )

        # Register handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(CommandHandler("help", self._handle_help))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_message
        ))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram Gateway started")

    async def stop(self):
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            logger.info("Telegram Gateway stopped")

    def _is_authorized(self, update: Update) -> bool:
        if not self.authorized_user:
            return True  # No restriction if user_id not set
        user_id = update.effective_user.id if update.effective_user else None
        return user_id == self.authorized_user

    async def _handle_start(self, update: Update, context):
        if not self._is_authorized(update):
            return
        await update.message.reply_text(
            "女娲在线 ✓\n\n"
            "发送链接 → 我会调研并写文章\n"
            "发送文字 → 我会理解为指令\n"
            "/status → 查看当前状态\n"
            "/help → 帮助"
        )

    async def _handle_status(self, update: Update, context):
        if not self._is_authorized(update):
            return
        # Respond directly, don't go through signal queue
        if self.status_callback:
            msg = self.status_callback()
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Agent 尚未就绪。")

    async def _handle_help(self, update: Update, context):
        if not self._is_authorized(update):
            return
        await update.message.reply_text(
            "📋 可用命令：\n\n"
            "/status — 查看文章状态\n"
            "/help — 显示帮助\n\n"
            "💡 直接发送：\n"
            "• 微信文章链接 → 自动调研+写作\n"
            "• 任意文字 → 作为指令处理\n"
            "• 回复按钮 → 审批/确认操作"
        )

    async def _handle_message(self, update: Update, context):
        if not self._is_authorized(update):
            return
        text = update.message.text.strip()
        chat_id = update.effective_chat.id

        # Detect URL
        url_pattern = r'https?://\S+'
        urls = re.findall(url_pattern, text)

        if urls:
            # Extract all URLs and remaining text as instructions
            instructions = text
            for u in urls:
                instructions = instructions.replace(u, "").strip()
            signal = Signal(
                type="user_url",
                content=urls[0],
                data={
                    "chat_id": chat_id,
                    "urls": urls,  # all URLs
                    "instructions": instructions,
                    "raw_text": text,
                },
            )
        else:
            # Quick status check keywords — respond directly
            if self.status_callback and any(
                kw in text for kw in ["进度", "状态", "怎么样了", "到哪了"]
            ):
                msg = self.status_callback()
                await update.message.reply_text(msg)
                return

            # Check if it's a response to a pending question
            callback_key = f"text_{chat_id}"
            if callback_key in self._response_futures:
                future = self._response_futures.pop(callback_key)
                if not future.done():
                    future.set_result(text)
                return

            signal = Signal(
                type="user_message",
                content=text,
                data={"chat_id": chat_id},
            )

        await self.signal_queue.put(signal)
        logger.info("Signal queued: %s — %s", signal.type, signal.content[:80])

    async def _handle_callback(self, update: Update, context):
        if not self._is_authorized(update):
            return
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        signal = Signal(
            type="callback",
            content=callback_data,
            data={"chat_id": query.message.chat_id},
        )
        await self.signal_queue.put(signal)
        logger.info("Callback: %s", callback_data)

    # --- Outbound methods ---

    async def send_message(self, chat_id: int, text: str,
                           buttons: list[list[dict]] = None):
        """Send a message to user, optionally with inline buttons."""
        if not self.app:
            logger.warning("Gateway not started, cannot send message")
            return

        reply_markup = None
        if buttons:
            keyboard = []
            for row in buttons:
                kb_row = [
                    InlineKeyboardButton(
                        text=btn.get("text", ""),
                        callback_data=btn.get("callback", ""),
                    )
                    for btn in row
                ]
                keyboard.append(kb_row)
            reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await self.app.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error("发送消息失败: %s", e)
            # Retry without markup
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                pass

    async def send_notification(self, text: str, buttons: list[list[dict]] = None):
        """Send to the authorized user."""
        if self.authorized_user:
            await self.send_message(self.authorized_user, text, buttons)
        else:
            logger.warning("No authorized_user configured, notification dropped")

    async def get_next_signal(self, timeout: float = None) -> Optional[Signal]:
        """Wait for next signal from queue."""
        try:
            if timeout:
                return await asyncio.wait_for(
                    self.signal_queue.get(), timeout=timeout
                )
            else:
                return await self.signal_queue.get()
        except asyncio.TimeoutError:
            return None
