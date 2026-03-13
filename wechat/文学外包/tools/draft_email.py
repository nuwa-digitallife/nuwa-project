#!/usr/bin/env python3
"""
文学投稿邮件工具

根据发件邮箱后缀自动选择 SMTP 通道（Gmail / Outlook / 通用）发送投稿邮件。

用法：
  python draft_email.py --work-dir ../作品/邕城朝暮 --venues 红豆,广西民族报
  python draft_email.py --work-dir ../作品/邕城朝暮 --venues 红豆 --dry-run
  python draft_email.py --work-dir ../作品/邕城朝暮 --venues 红豆 --identity anti_aigc
  python draft_email.py --work-dir ../作品/邕城朝暮 --venues 红豆 --save-draft  # 存草稿不发送
"""

import argparse
import email.mime.application
import email.mime.multipart
import email.mime.text
import imaplib
import json
import os
import smtplib
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
SUBMISSIONS_FILE = PROJECT_DIR / "已投稿" / "submissions.jsonl"
IDENTITIES_FILE = PROJECT_DIR / "identities.json"
TEMPLATE_FILE = SCRIPT_DIR / "email_template.txt"
CREDS_DIR = Path.home() / ".config" / "nuwa"

# 刊物信息（从机会数据库提取关键字段）
VENUES = {
    "红豆": {
        "full_name": "《红豆》",
        "email": "hdzz1972@163.com",
        "subject_format": "{genre}+{title}+{pen_name}",
        "level": "市级",
        "aigc_policy": "reject_aigc",  # 明确拒绝AI辅助，要求原创首发独投
    },
    "广西民族报": {
        "full_name": "《广西民族报》副刊",
        "email": "gxmzbfk@126.com",
        "subject_format": "散文投稿：{title}",
        "level": "省级",
        "aigc_policy": "normal",
    },
    "广西文学": {
        "full_name": "《广西文学》",
        "email": "",  # 待确认
        "subject_format": "{genre}投稿：{title}",
        "level": "省级",
        "aigc_policy": "normal",
    },
    "人民文学": {
        "full_name": "《人民文学》",
        "email": "rmwxsanwen@126.com",
        "subject_format": "{title}（{genre}）",
        "level": "国家级",
        "aigc_policy": "normal",
    },
    "花城": {
        "full_name": "《花城》",
        "email": "huachengsanwen@163.com",
        "subject_format": "{title}（{genre}）",
        "level": "国家级",
        "aigc_policy": "normal",
    },
    "科幻世界": {
        "full_name": "《科幻世界》",
        "email": "tougao@sfw.com.cn",
        "subject_format": "{title}",
        "level": "国家级",
        "aigc_policy": "reject_aigc",
    },
    "延河绿色文学": {
        "full_name": "《延河·绿色文学》",
        "email": "yanhexbysw@163.com",
        "subject_format": "{genre}投稿：{title}",
        "level": "省级",
        "aigc_policy": "normal",
    },
    "真实故事计划": {
        "full_name": "真实故事计划",
        "email": "tougao@zhenshigushijihua.com",
        "subject_format": "{title}",
        "level": "网络平台",
        "aigc_policy": "normal",
    },
    "家乡好": {
        "full_name": "\u201c谁不说俺家乡好\u201d征文",
        "email": "wdwxtg@qq.com",
        "subject_format": "谁不说俺家乡好+{title}+{pen_name}",
        "level": "国家级协会",
        "aigc_policy": "normal",
    },
}


# SMTP 通道配置：邮箱后缀 → (smtp_host, port, env_file, env_key_email, env_key_password)
SMTP_CHANNELS = {
    "outlook.com": ("smtp-mail.outlook.com", 587, "outlook.env", "OUTLOOK_EMAIL", "OUTLOOK_PASSWORD"),
    "hotmail.com": ("smtp-mail.outlook.com", 587, "outlook.env", "OUTLOOK_EMAIL", "OUTLOOK_PASSWORD"),
    "live.com":    ("smtp-mail.outlook.com", 587, "outlook.env", "OUTLOOK_EMAIL", "OUTLOOK_PASSWORD"),
    "gmail.com":   ("smtp.gmail.com",        587, "gmail.env",   "GMAIL_ADDRESS",  "GMAIL_APP_PASSWORD"),
}
# 默认通道（未知后缀时尝试 outlook）
DEFAULT_CHANNEL = SMTP_CHANNELS["outlook.com"]


def _load_env_file(filename: str) -> dict:
    """从 ~/.config/nuwa/<filename> 加载 key=value。"""
    env = {}
    path = CREDS_DIR / filename
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_smtp_config(sender_email: str) -> dict:
    """根据发件邮箱后缀，自动选择 SMTP 通道并加载凭据。"""
    domain = sender_email.rsplit("@", 1)[-1].lower() if "@" in sender_email else ""
    channel = SMTP_CHANNELS.get(domain, DEFAULT_CHANNEL)
    smtp_host, smtp_port, env_file, key_email, key_password = channel

    env = _load_env_file(env_file)
    address = os.environ.get(key_email, env.get(key_email, ""))
    password = os.environ.get(key_password, env.get(key_password, ""))

    return {
        "host": smtp_host,
        "port": smtp_port,
        "address": address,
        "password": password,
        "channel": domain or "unknown",
    }


def load_identities():
    """加载笔名身份配置。"""
    if IDENTITIES_FILE.exists():
        return json.loads(IDENTITIES_FILE.read_text())
    return {}


def select_identity(venue_key: str, identities: dict, override: str = None) -> dict:
    """根据刊物 AIGC 政策选择身份。"""
    if override and override in identities:
        return identities[override]
    venue = VENUES.get(venue_key, {})
    if venue.get("aigc_policy") == "reject_aigc" and "anti_aigc" in identities:
        return identities["anti_aigc"]
    return identities.get("default", {})


def build_email(meta: dict, venue_key: str, identity: dict, docx_path: Path, work_dir: Path) -> email.mime.multipart.MIMEMultipart:
    """构建 MIME 邮件（正文粘贴全文 + 文末个人信息 + DOCX 附件）。"""
    venue = VENUES[venue_key]

    # 读取文章全文（MD 版本，去掉 markdown 标记）
    md_path = work_dir / meta.get("source_md", f"{meta['title']}.md")
    article_text = ""
    if md_path.exists():
        raw = md_path.read_text()
        # 去掉开头的 **标题** 行（正文不重复标题）
        lines = raw.split("\n")
        if lines and lines[0].strip().startswith("**") and lines[0].strip().endswith("**"):
            lines = lines[1:]
        article_text = "\n".join(lines).strip()
        # pandoc 将破折号转为 ------，还原为 ——
        article_text = article_text.replace("------", "——")
        # 去掉转义的引号
        article_text = article_text.replace('\\"', '"')
    else:
        article_text = "（见附件）"

    template = TEMPLATE_FILE.read_text()
    body = template.format(
        genre=meta.get("genre", "散文"),
        title=meta["title"],
        char_count=meta["char_count"],
        article_text=article_text,
        pen_name=identity.get("pen_name", ""),
        contact=identity.get("contact", ""),
        address=identity.get("address", ""),
        bio=identity.get("bio", ""),
    )

    subject = venue["subject_format"].format(
        genre=meta.get("genre", "散文"),
        title=meta["title"],
        pen_name=identity.get("pen_name", ""),
    )

    msg = email.mime.multipart.MIMEMultipart()
    msg["Subject"] = subject
    msg["To"] = venue["email"]
    msg["From"] = identity.get("email", "")
    msg.attach(email.mime.text.MIMEText(body, "plain", "utf-8"))

    # 附件
    if docx_path.exists():
        with open(docx_path, "rb") as f:
            att = email.mime.application.MIMEApplication(f.read(), Name=docx_path.name)
        att["Content-Disposition"] = f'attachment; filename="{docx_path.name}"'
        msg.attach(att)

    return msg


def send_smtp(smtp_cfg: dict, msg: email.mime.multipart.MIMEMultipart) -> bool:
    """通过 SMTP 发送邮件。smtp_cfg 由 get_smtp_config() 生成。"""
    try:
        server = smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"])
        server.starttls()
        server.login(smtp_cfg["address"], smtp_cfg["password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"  SMTP 错误 ({smtp_cfg['channel']}): {e}", file=sys.stderr)
        return False


# IMAP 服务器映射（草稿功能用）
IMAP_SERVERS = {
    "outlook.com": "imap-mail.outlook.com",
    "hotmail.com": "imap-mail.outlook.com",
    "live.com":    "imap-mail.outlook.com",
    "gmail.com":   "imap.gmail.com",
}
IMAP_DRAFTS_FOLDER = {
    "gmail.com": "[Gmail]/Drafts",
}


def save_draft_imap(smtp_cfg: dict, msg: email.mime.multipart.MIMEMultipart) -> bool:
    """通过 IMAP 存入草稿箱（不发送）。"""
    domain = smtp_cfg["channel"]
    imap_host = IMAP_SERVERS.get(domain, "outlook.office365.com")
    drafts_folder = IMAP_DRAFTS_FOLDER.get(domain, "Drafts")
    try:
        imap = imaplib.IMAP4_SSL(imap_host)
        imap.login(smtp_cfg["address"], smtp_cfg["password"])
        raw = msg.as_bytes()
        imap.append(drafts_folder, "\\Draft", None, raw)
        imap.logout()
        return True
    except Exception as e:
        print(f"  IMAP 草稿错误 ({domain}): {e}", file=sys.stderr)
        return False


def append_submission(venue_key: str, meta: dict, identity: dict, status: str = "草稿"):
    """追加投稿记录到 submissions.jsonl。"""
    venue = VENUES[venue_key]
    # 计算下一个 ID
    existing = []
    if SUBMISSIONS_FILE.exists():
        for line in SUBMISSIONS_FILE.read_text().splitlines():
            if line.strip():
                existing.append(json.loads(line))
    next_id = f"sub-{len(existing) + 1:03d}"

    record = {
        "id": next_id,
        "timestamp": datetime.now().isoformat(),
        "work": meta["title"],
        "venue": venue["full_name"],
        "venue_level": venue.get("level", ""),
        "identity": identity.get("pen_name", "default"),
        "email": venue["email"],
        "subject_format": venue["subject_format"],
        "status": status,
        "result": None,
        "result_date": None,
    }
    SUBMISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBMISSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return next_id


def main():
    parser = argparse.ArgumentParser(description="文学投稿邮件草稿工具")
    parser.add_argument("--work-dir", required=True, help="作品目录（含 meta.json 和 DOCX）")
    parser.add_argument("--venues", required=True, help="逗号分隔的目标刊物 key（如：红豆,广西民族报）")
    parser.add_argument("--identity", default=None, help="强制使用指定身份（覆盖自动选择）")
    parser.add_argument("--dry-run", action="store_true", help="只打印邮件内容，不发送")
    parser.add_argument("--save-draft", action="store_true", help="存入 Outlook 草稿箱，不直接发送")
    args = parser.parse_args()

    work_dir = Path(args.work_dir).resolve()
    meta_file = work_dir / "meta.json"
    if not meta_file.exists():
        print(f"错误：找不到 {meta_file}", file=sys.stderr)
        sys.exit(1)
    meta = json.loads(meta_file.read_text())

    docx_path = work_dir / meta.get("source_docx", f"{meta['title']}.docx")
    if not docx_path.exists():
        print(f"警告：找不到 DOCX 附件 {docx_path}", file=sys.stderr)

    identities = load_identities()
    if not identities:
        print("警告：identities.json 未找到或为空，将使用空身份", file=sys.stderr)

    venue_keys = [v.strip() for v in args.venues.split(",")]
    for vk in venue_keys:
        if vk not in VENUES:
            print(f"错误：未知刊物 '{vk}'。可选：{', '.join(VENUES.keys())}", file=sys.stderr)
            sys.exit(1)
        venue = VENUES[vk]
        if not venue["email"]:
            print(f"跳过 {vk}：邮箱待确认", file=sys.stderr)
            continue

        identity = select_identity(vk, identities, args.identity)
        msg = build_email(meta, vk, identity, docx_path, work_dir)

        # 根据身份邮箱后缀自动选择 SMTP 通道
        sender_email = identity.get("email", "")
        smtp_cfg = get_smtp_config(sender_email)

        print(f"\n{'='*50}")
        print(f"目标: {venue['full_name']} ({venue['email']})")
        print(f"主题: {msg['Subject']}")
        print(f"身份: {identity.get('pen_name', 'N/A')} ({sender_email})")
        print(f"通道: {smtp_cfg['channel']} → {smtp_cfg['host']}")
        print(f"附件: {docx_path.name}")

        if args.dry_run:
            print(f"\n--- 邮件正文 ---")
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    print(part.get_payload(decode=True).decode("utf-8"))
            print(f"--- [DRY RUN] 未发送 ---")
        else:
            if not smtp_cfg["address"] or not smtp_cfg["password"]:
                print(f"  错误：{smtp_cfg['channel']} 凭据未配置。请编辑 ~/.config/nuwa/{smtp_cfg['channel']}.env",
                      file=sys.stderr)
                continue

            if args.save_draft:
                ok = save_draft_imap(smtp_cfg, msg)
                if ok:
                    sub_id = append_submission(vk, meta, identity, status="草稿")
                    print(f"  已存入草稿箱 (记录: {sub_id})")
                else:
                    print(f"  草稿保存失败！")
            else:
                ok = send_smtp(smtp_cfg, msg)
                if ok:
                    sub_id = append_submission(vk, meta, identity, status="已投")
                    print(f"  已发送 ✓ (记录: {sub_id})")
                else:
                    print(f"  发送失败！")

    print()


if __name__ == "__main__":
    main()
