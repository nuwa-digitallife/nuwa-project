#!/usr/bin/env python3
"""
AI 日报简报生成器
每天从 wechat-article-exporter API 拉取关注公众号的最新文章，
筛选 AI 相关，合并同类项，生成简报供人工精选入库。

全自动：直接从 Chrome Cookies 提取 auth-key，调用 exporter API。
公众号列表从 exporter 的 /api/public/v1/followed-accounts 动态获取。

使用方式：
  source ~/venv/automation/bin/activate
  python auto_import.py              # 默认最近 24h
  python auto_import.py --hours 48   # 最近 48h
  python auto_import.py --list-accounts          # 查看关注列表
  python auto_import.py --add-account "新账号"    # 添加公众号
  python auto_import.py --remove-account "旧账号" # 移除公众号
  python auto_import.py --sync-accounts           # 从 Chrome exporter 同步列表
"""

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

import requests

# ── 路径配置 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
KB_ROOT = SCRIPT_DIR.parent
KNOWLEDGE_BASE_DIR = KB_ROOT / "knowledge_base"
INDEX_DIR = KNOWLEDGE_BASE_DIR / "_index"
ARTICLES_INDEX_FILE = INDEX_DIR / "articles_index.json"
CLASSIFICATION_RULES_FILE = INDEX_DIR / "classification_rules.json"
LOG_DIR = KB_ROOT / "logs"
DEVLOG_FILE = LOG_DIR / "devlog.jsonl"
AUTO_IMPORT_LOG = LOG_DIR / "auto_import.log"
DIGEST_DIR = KB_ROOT / "digests"

EXPORTER_BASE = "http://localhost:3000"
CHROME_COOKIES_DB = (
    Path.home()
    / "Library/Application Support/Google/Chrome/Default/Cookies"
)

FOLLOWED_ACCOUNTS_API = f"{EXPORTER_BASE}/api/public/v1/followed-accounts"

# AI 相关性高频词
AI_TITLE_KEYWORDS = [
    "AI", "人工智能", "机器人", "大模型", "LLM", "GPT", "Claude",
    "DeepSeek", "OpenAI", "Agent", "算法", "芯片", "英伟达",
    "千问", "豆包", "Gemini", "Sora", "ChatGPT", "Copilot",
    "AGI", "机器学习", "深度学习", "神经网络", "Transformer",
    "强化学习", "自动驾驶", "具身智能", "多模态", "Anthropic",
    "Llama", "开源模型", "AIGC", "生成式",
]

SIMILARITY_THRESHOLD = 0.45
API_DELAY = 1.5  # 秒，API 请求间隔


# ── 工具函数 ──────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUTO_IMPORT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def devlog(entry: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now().isoformat()
    entry["project"] = "knowledgebase"
    with open(DEVLOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_classification_rules() -> dict:
    with open(CLASSIFICATION_RULES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_articles_index() -> dict:
    with open(ARTICLES_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Chrome Cookie 解密 ───────────────────────────────────
def _get_chrome_safe_storage_password() -> str:
    """从 macOS Keychain 获取 Chrome Safe Storage 密码"""
    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage", "-a", "Chrome"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"无法获取 Chrome Safe Storage 密码: {result.stderr}")
    return result.stdout.strip()


def _derive_chrome_key(password: str) -> bytes:
    """PBKDF2 派生 AES 密钥"""
    return hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), b"saltysalt", 1003, dklen=16)


def _decrypt_chrome_cookie(encrypted_value: bytes, key: bytes) -> str:
    """解密 Chrome v10 格式 cookie"""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    if encrypted_value[:3] != b"v10":
        raise ValueError("不是 v10 格式 cookie")

    encrypted_data = encrypted_value[3:]
    iv = b" " * 16
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_data) + decryptor.finalize()

    # 去掉 PKCS7 padding
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()

    # Chrome cookie 解密后有 32 字节二进制前缀 + 32 字节 ASCII auth-key
    # auth-key 是 crypto.randomUUID() 去掉连字符的 32 hex chars
    try:
        return unpadded.decode("utf-8")
    except UnicodeDecodeError:
        # 取最后 32 字节作为 auth-key
        auth_bytes = unpadded[-32:]
        try:
            return auth_bytes.decode("ascii")
        except Exception:
            raise ValueError(f"无法从解密数据中提取 auth-key: {unpadded.hex()}")


def get_auth_key() -> str:
    """从 Chrome Cookies DB 提取 exporter 的 auth-key"""
    if not CHROME_COOKIES_DB.exists():
        raise FileNotFoundError(f"Chrome Cookies DB 不存在: {CHROME_COOKIES_DB}")

    # Chrome 锁定 Cookies DB，需要复制一份
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(str(CHROME_COOKIES_DB), tmp)

    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.execute(
            "SELECT encrypted_value FROM cookies WHERE host_key = ? AND name = ?",
            ("localhost", "auth-key"),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError("Cookies DB 中没有 auth-key（需要先在浏览器中登录 exporter）")

        password = _get_chrome_safe_storage_password()
        key = _derive_chrome_key(password)
        return _decrypt_chrome_cookie(row[0], key)
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── 检查 exporter 服务 ───────────────────────────────────
def check_exporter() -> bool:
    try:
        r = requests.get(EXPORTER_BASE, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ── API 拉取文章 ─────────────────────────────────────────
def search_account(auth_key: str, keyword: str) -> dict | None:
    """搜索公众号，返回 {fakeid, nickname}"""
    url = f"{EXPORTER_BASE}/api/web/mp/searchbiz"
    params = {"keyword": keyword}
    headers = {"X-Auth-Key": auth_key}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        items = data.get("base_resp", {}).get("ret") if data.get("base_resp") else None
        if items == 0:  # success
            biz_list = data.get("list", [])
            if biz_list:
                return {"fakeid": biz_list[0]["fakeid"], "nickname": biz_list[0]["nickname"]}
        # Fallback: check direct list field
        biz_list = data.get("list", [])
        if biz_list:
            return {"fakeid": biz_list[0]["fakeid"], "nickname": biz_list[0]["nickname"]}
    except Exception as e:
        log(f"  搜索 {keyword} 失败: {e}")
    return None


def fetch_account_articles(auth_key: str, fakeid: str, cutoff_ts: int) -> list[dict]:
    """拉取某公众号自 cutoff_ts 以来的所有文章"""
    url = f"{EXPORTER_BASE}/api/web/mp/appmsgpublish"
    headers = {"X-Auth-Key": auth_key}
    articles = []
    begin = 0
    size = 10

    while True:
        params = {"id": fakeid, "begin": begin, "size": size}
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            data = r.json()
        except Exception as e:
            log(f"    page {begin // size + 1} 失败: {e}")
            break

        # publish_page 是 JSON 字符串，需要二次解析
        publish_page_raw = data.get("publish_page", "")
        if not publish_page_raw:
            break

        try:
            publish_page = json.loads(publish_page_raw) if isinstance(publish_page_raw, str) else publish_page_raw
        except json.JSONDecodeError:
            log(f"    publish_page 解析失败")
            break

        publish_list = publish_page.get("publish_list", [])
        if not publish_list:
            break

        reached_cutoff = False
        for batch in publish_list:
            # publish_info 也是 JSON 字符串
            pub_info_raw = batch.get("publish_info", "")
            try:
                pub_info = json.loads(pub_info_raw) if isinstance(pub_info_raw, str) else pub_info_raw
            except (json.JSONDecodeError, TypeError):
                continue

            for item in pub_info.get("appmsgex", []):
                create_time = item.get("create_time", 0)
                if create_time < cutoff_ts:
                    reached_cutoff = True
                    break
                articles.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "create_time": create_time,
                    "digest": item.get("digest", ""),
                    "fakeid": fakeid,
                    "nickname": "",  # filled by caller
                    "cover": item.get("cover", ""),
                })
            if reached_cutoff:
                break

        if reached_cutoff or len(publish_list) < size:
            break

        begin += size
        time.sleep(API_DELAY)

    return articles


def get_followed_accounts() -> list[str]:
    """从 exporter API 获取关注的公众号列表"""
    try:
        r = requests.get(FOLLOWED_ACCOUNTS_API, timeout=5)
        data = r.json()
        accounts = data.get("accounts", [])
        if accounts:
            return accounts
    except Exception as e:
        log(f"从 exporter 获取公众号列表失败: {e}")
    log("公众号列表为空，请先通过 POST /api/public/v1/followed-accounts 设置")
    return []


def sync_accounts_from_chrome() -> list[str]:
    """通过 AppleScript 从 Chrome IndexedDB 拉取 exporter 的公众号列表并同步到 API"""
    import json as _json
    script = '''
    tell application "Google Chrome"
        repeat with w in windows
            repeat with t in tabs of w
                if URL of t starts with "http://localhost:3000" then
                    set jsResult to execute t javascript "
                        var req = indexedDB.open('exporter.wxdown.online');
                        req.onsuccess = function(e) {
                            var db = e.target.result;
                            var tx = db.transaction(['info'], 'readonly');
                            var store = tx.objectStore('info');
                            var getAll = store.getAll();
                            getAll.onsuccess = function() {
                                var names = getAll.result.map(function(a) { return a.nickname || ''; }).filter(Boolean);
                                document.title = JSON.stringify(names);
                            };
                        };
                        'ok'
                    "
                    delay 1
                    return title of t
                end if
            end repeat
        end repeat
        return "NO_TAB"
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    raw = result.stdout.strip()
    if not raw or raw == "NO_TAB":
        print("未找到 exporter 标签页，请确保 Chrome 中打开了 localhost:3000")
        return []

    try:
        accounts = _json.loads(raw)
    except Exception:
        print(f"解析失败: {raw[:200]}")
        return []

    # 同步到 API
    try:
        r = requests.post(FOLLOWED_ACCOUNTS_API, json={"accounts": accounts}, timeout=5)
        data = r.json()
        synced = data.get("accounts", accounts)
        print(f"已从 Chrome 同步 {len(synced)} 个公众号到 API")
        for a in synced:
            print(f"  - {a}")
        return synced
    except Exception as e:
        print(f"同步到 API 失败: {e}")
        return accounts


def fetch_all_articles(auth_key: str, hours: int) -> list[dict]:
    """拉取所有关注公众号的最新文章"""
    cutoff_ts = int((datetime.now() - timedelta(hours=hours)).timestamp())
    all_articles = []

    followed = get_followed_accounts()
    if not followed:
        return []

    log(f"关注列表 ({len(followed)}): {', '.join(followed)}")

    for name in followed:
        log(f"搜索: {name}")
        account = search_account(auth_key, name)
        time.sleep(API_DELAY)

        if not account:
            log(f"  未找到: {name}")
            continue

        log(f"  找到: {account['nickname']} ({account['fakeid'][:8]}...)")
        articles = fetch_account_articles(auth_key, account["fakeid"], cutoff_ts)

        # Fill in nickname
        for a in articles:
            a["nickname"] = account["nickname"]

        log(f"  {account['nickname']}: {len(articles)} 篇")
        all_articles.extend(articles)
        time.sleep(API_DELAY)

    return all_articles


# ── AI 相关性判断 ─────────────────────────────────────────
def is_ai_related(title: str, digest: str) -> bool:
    text = (title + " " + digest).lower()
    title_lower = title.lower()

    for kw in AI_TITLE_KEYWORDS:
        if kw.lower() in title_lower:
            return True

    rules = load_classification_rules()
    ai_keywords = rules["categories"].get("人工智能", {}).get("keywords", [])
    match_count = sum(1 for kw in ai_keywords if kw.lower() in text)
    return match_count >= 2


# ── 合并同类项 ────────────────────────────────────────────
def _clean_title(title: str) -> str:
    title = re.sub(r'[，。！？、：；\u201c\u201d\u2018\u2019【】《》（）\s|｜·…]', ' ', title)
    title = re.sub(r'[,.\\!?:;\'"()\[\]{}\\-]', ' ', title)
    for prefix in ["最新", "重磅", "突发", "刚刚", "独家", "深度"]:
        title = title.replace(prefix, "")
    return title.strip()


def _title_similarity(a: str, b: str) -> float:
    ca, cb = _clean_title(a), _clean_title(b)
    ratio = SequenceMatcher(None, ca, cb).ratio()

    words_a = set(re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', ca))
    words_b = set(re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{2,}', cb))
    if words_a and words_b:
        overlap = len(words_a & words_b)
        union = len(words_a | words_b)
        jaccard = overlap / union if union > 0 else 0
        ratio = max(ratio, jaccard)

    return ratio


def merge_similar_articles(articles: list[dict]) -> list[list[dict]]:
    n = len(articles)
    visited = [False] * n
    groups = []

    for i in range(n):
        if visited[i]:
            continue
        group = [articles[i]]
        visited[i] = True
        for j in range(i + 1, n):
            if visited[j]:
                continue
            sim = _title_similarity(articles[i]["title"], articles[j]["title"])
            if sim >= SIMILARITY_THRESHOLD:
                group.append(articles[j])
                visited[j] = True
        group.sort(key=lambda a: len(a.get("digest", "")), reverse=True)
        groups.append(group)

    return groups


# ── 生成简报 ──────────────────────────────────────────────
def generate_digest(
    groups: list[list[dict]],
    hours: int,
    total_raw: int,
    total_ai: int,
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# AI 日报 {today}")
    lines.append("")
    lines.append(
        f"> {total_raw} 篇 → AI {total_ai} 篇 → 合并 {len(groups)} 条 ｜ 最近 {hours}h ｜ {datetime.now().strftime('%H:%M')}"
    )
    lines.append("")

    for idx, group in enumerate(groups, 1):
        best = group[0]
        nickname = best.get("nickname", "")
        dt = datetime.fromtimestamp(best["create_time"]).strftime("%m-%d")

        summary_parts = [f"<b>{idx}.</b> {best['title']}"]
        if nickname:
            summary_parts.append(f" <code>{nickname}</code>")
        summary_parts.append(f" <code>{dt}</code>")
        if len(group) > 1:
            summary_parts.append(f" <code>+{len(group) - 1}同题</code>")

        lines.append(f'<details><summary>{"".join(summary_parts)}</summary>')
        lines.append("")

        if best.get("digest"):
            lines.append(f"> {best['digest']}")
            lines.append("")

        lines.append(f"[原文]({best['link']})")

        if len(group) > 1:
            lines.append("")
            lines.append("同题报道：")
            for alt in group[1:]:
                alt_name = alt.get("nickname", "同题")
                lines.append(f"- [{alt_name}]({alt['link']})")

        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*入库：把链接发给 Claude → `帮忙加下 <url>`*")

    return "\n".join(lines)


# ── 主流程 ────────────────────────────────────────────────
def manage_accounts(args):
    """管理关注的公众号列表"""
    if args.list_accounts:
        accounts = get_followed_accounts()
        print(f"关注列表 ({len(accounts)}):")
        for a in accounts:
            print(f"  - {a}")
        return True

    if args.add_account:
        try:
            r = requests.post(FOLLOWED_ACCOUNTS_API, json={"add": args.add_account}, timeout=5)
            data = r.json()
            print(f"已添加: {args.add_account}")
            print(f"当前列表: {data.get('accounts', [])}")
        except Exception as e:
            print(f"添加失败: {e}")
        return True

    if args.remove_account:
        try:
            r = requests.post(FOLLOWED_ACCOUNTS_API, json={"remove": args.remove_account}, timeout=5)
            data = r.json()
            print(f"已移除: {args.remove_account}")
            print(f"当前列表: {data.get('accounts', [])}")
        except Exception as e:
            print(f"移除失败: {e}")
        return True

    if args.sync_accounts:
        sync_accounts_from_chrome()
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="AI 日报简报生成器")
    parser.add_argument("--hours", type=int, default=24, help="扫描最近 N 小时（默认 24）")
    parser.add_argument("--list-accounts", action="store_true", help="列出关注的公众号")
    parser.add_argument("--add-account", type=str, help="添加公众号")
    parser.add_argument("--remove-account", type=str, help="移除公众号")
    parser.add_argument("--sync-accounts", action="store_true", help="从 Chrome exporter 同步公众号列表")
    args = parser.parse_args()

    if manage_accounts(args):
        return

    log("=" * 60)
    log("AI 日报简报 开始生成")
    log("=" * 60)

    # 1. 检查 exporter
    if not check_exporter():
        log("exporter 服务不可达 (localhost:3000)，退出")
        sys.exit(1)
    log("exporter 服务正常")

    # 2. 获取 auth-key
    try:
        auth_key = get_auth_key()
        log(f"auth-key 已获取 ({auth_key[:8]}...)")
    except Exception as e:
        log(f"获取 auth-key 失败: {e}")
        log("请先在浏览器中登录 exporter (localhost:3000)")
        sys.exit(1)

    # 3. 拉取所有公众号文章
    raw_articles = fetch_all_articles(auth_key, args.hours)
    if not raw_articles:
        log("没有找到最近的文章，退出")
        return

    total_raw = len(raw_articles)
    log(f"原始文章: {total_raw} 篇（来自 {len(set(a['nickname'] for a in raw_articles))} 个公众号）")

    # 4. AI 相关性过滤
    ai_articles = [a for a in raw_articles if is_ai_related(a["title"], a.get("digest", ""))]
    total_ai = len(ai_articles)
    log(f"AI 相关: {total_ai}/{total_raw}")

    if not ai_articles:
        log("没有 AI 相关文章，退出")
        return

    ai_articles.sort(key=lambda a: a.get("create_time", 0), reverse=True)

    # 5. 去掉已入库的
    index = load_articles_index()
    existing_titles = {a["title"] for a in index["articles"]}
    existing_urls = set()
    for a in index["articles"]:
        meta_path = KNOWLEDGE_BASE_DIR / a["path"] / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("source_url"):
                        existing_urls.add(meta["source_url"])
            except Exception:
                pass

    fresh = []
    for a in ai_articles:
        if a["link"] in existing_urls or a["title"] in existing_titles:
            continue
        fresh.append(a)

    log(f"去已入库: {len(fresh)} 篇（已跳过 {total_ai - len(fresh)} 篇）")

    if not fresh:
        log("全部已入库，无需生成简报")
        return

    # 6. 合并同类项
    groups = merge_similar_articles(fresh)
    log(f"合并同类项: {len(fresh)} → {len(groups)} 条")

    # 7. 生成简报
    digest_md = generate_digest(groups, args.hours, total_raw, total_ai)

    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    digest_path = DIGEST_DIR / f"{today}.md"
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write(digest_md)

    log(f"简报已生成: {digest_path}")

    devlog({
        "type": "task",
        "context": "ai_digest",
        "action": f"生成 AI 日报 ({args.hours}h)",
        "result": f"全部 {total_raw} → AI {total_ai} → 去重 {len(fresh)} → 合并 {len(groups)} 条",
    })


if __name__ == "__main__":
    main()
