"""
Skill: 查收件箱 (Check Inbox)

IMAP 连接 Gmail，检查投稿目标刊物是否有回信。
发现新邮件时返回摘要，由 daemon 通过 Telegram 通知用户。

追踪已读邮件 UID，避免重复通知。
"""

import imaplib
import email
import json
import logging
from datetime import datetime
from email.header import decode_header
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult

logger = logging.getLogger("editor.skills.check_inbox")

# 关注的发件地址（投稿目标刊物邮箱）
VENUE_EMAILS = {
    "hdzz1972@163.com": "《红豆》",
    "gxmzbfk@126.com": "《广西民族报》",
    "rmwxsanwen@126.com": "《人民文学》",
    "huachengsanwen@163.com": "《花城》",
    "tougao@sfw.com.cn": "《科幻世界》",
    "yanhexbysw@163.com": "《延河》",
    "wdwxtg@qq.com": "\u201c家乡好\u201d征文",
    "tougao@zhenshigushijihua.com": "真实故事计划",
}

CREDS_DIR = Path.home() / ".config" / "nuwa"


def _load_env(filename: str) -> dict:
    env = {}
    path = CREDS_DIR / filename
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _decode_header_value(value: str) -> str:
    """Decode RFC 2047 encoded header."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


class CheckInboxSkill(Skill):
    name = "check_inbox"
    description = "检查 Gmail 收件箱，查看投稿刊物是否有回信"
    estimated_duration = "15s"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        env = _load_env("gmail.env")
        gmail_addr = env.get("GMAIL_ADDRESS", "")
        gmail_pass = env.get("GMAIL_APP_PASSWORD", "")

        if not gmail_addr or not gmail_pass:
            return SkillResult(False, "Gmail 凭据未配置（~/.config/nuwa/gmail.env）")

        # Load seen UIDs
        logs_dir = Path(config["paths"].get("logs_dir", "")).expanduser()
        logs_dir.mkdir(parents=True, exist_ok=True)
        seen_file = logs_dir / "seen_emails.json"

        seen_uids = set()
        if seen_file.exists():
            try:
                seen_uids = set(json.loads(seen_file.read_text()))
            except (json.JSONDecodeError, TypeError):
                seen_uids = set()

        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(gmail_addr, gmail_pass)
            imap.select("INBOX", readonly=True)

            new_emails = []

            # Search for emails from each venue
            for venue_email, venue_name in VENUE_EMAILS.items():
                status, data = imap.search(None, f'FROM "{venue_email}"')
                if status != "OK":
                    continue

                msg_nums = data[0].split()
                for num in msg_nums:
                    uid_status, uid_data = imap.fetch(num, "(UID)")
                    if uid_status != "OK":
                        continue
                    # Parse UID from response like b'1 (UID 12345)'
                    uid_str = uid_data[0].decode()
                    uid = uid_str.split("UID")[1].strip().rstrip(")")
                    uid_key = f"{venue_email}:{uid}"

                    if uid_key in seen_uids:
                        continue

                    # Fetch headers
                    status2, msg_data = imap.fetch(num, "(RFC822.HEADER)")
                    if status2 != "OK":
                        continue

                    raw_headers = msg_data[0][1]
                    msg = email.message_from_bytes(raw_headers)

                    subject = _decode_header_value(msg.get("Subject", ""))
                    date_str = msg.get("Date", "")
                    from_addr = _decode_header_value(msg.get("From", ""))

                    new_emails.append({
                        "venue": venue_name,
                        "from": from_addr,
                        "subject": subject,
                        "date": date_str,
                        "uid_key": uid_key,
                    })

            imap.logout()

            # Update seen UIDs
            if new_emails:
                for em in new_emails:
                    seen_uids.add(em["uid_key"])
                seen_file.write_text(json.dumps(list(seen_uids), ensure_ascii=False))

            if not new_emails:
                return SkillResult(True, "收件箱无新回信。", {"new_count": 0})

            # Build notification
            lines = [f"收到 {len(new_emails)} 封新邮件：\n"]
            for em in new_emails:
                lines.append(
                    f"  {em['venue']}\n"
                    f"  主题: {em['subject']}\n"
                    f"  时间: {em['date']}\n"
                )

            return SkillResult(
                True,
                "\n".join(lines),
                {"new_count": len(new_emails), "emails": new_emails},
            )

        except imaplib.IMAP4.error as e:
            return SkillResult(False, f"IMAP 错误: {e}")
        except Exception as e:
            return SkillResult(False, f"检查收件箱失败: {e}")
