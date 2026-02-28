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
  python auto_import.py --mark-read 2026-02-20 1 3 5  # 标记已读
  python auto_import.py --stats                    # 阅读统计
  python auto_import.py --trends                   # 热点趋势
  python auto_import.py --search "Agent"           # 搜索文章
  python auto_import.py --build-site              # 构建/更新 digest-site 静态站
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
SITE_DIR = KB_ROOT / "digest-site"

READING_PROFILE_FILE = SCRIPT_DIR / "reading_profile.json"
READING_LOG_FILE = LOG_DIR / "reading_log.jsonl"


# ── 工具函数 ──────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUTO_IMPORT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def notify(title: str, msg: str):
    """macOS 原生通知"""
    subprocess.run(
        ["osascript", "-e", f'display notification "{msg}" with title "{title}"'],
        capture_output=True,
    )


def _api_get(url: str, params: dict = None, headers: dict = None, retries: int = 3, timeout: int = 10) -> requests.Response:
    """带指数退避重试的 API GET 请求，仅对超时/连接错误重试"""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)  # 2s → 4s → 8s
                log(f"  API 请求失败 (attempt {attempt + 1}/{retries}), {wait}s 后重试: {e}")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.HTTPError:
            raise  # 4xx/5xx 不重试


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
        r = _api_get(url, params=params, headers=headers)
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
            r = _api_get(url, params=params, headers=headers, timeout=15)
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


# ── 评分与生成简报 ────────────────────────────────────────

# 来源深度分级
TIER1_SOURCES = {"晚点LatePost", "晚点AI", "甲子光年", "虎嗅APP", "爱范儿"}
TIER2_SOURCES = {"机器之心", "极客公园", "InfoQ", "Founder Park"}

CLICKBAIT_WORDS = ["震惊", "刚刚", "重磅", "突发", "疯了", "炸了", "沸腾"]


def _load_reading_profile() -> dict | None:
    """加载用户阅读画像（如存在）"""
    if READING_PROFILE_FILE.exists():
        try:
            with open(READING_PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def score_article(article: dict, group_size: int) -> float:
    """为文章/组打分，用于简报排序"""
    score = 0.0
    title = article.get("title", "")
    digest = article.get("digest", "")
    nickname = article.get("nickname", "")

    # 内容丰富度：digest 长度
    if len(digest) > 80:
        score += 2
    elif len(digest) > 40:
        score += 1

    # 来源深度分级
    if nickname in TIER1_SOURCES:
        score += 3
    elif nickname in TIER2_SOURCES:
        score += 2
    else:
        score += 1

    # 独家性：只有 1 家报道 > 多家同题
    if group_size == 1:
        score += 2

    # 多家报道也有价值（热度加分，但不如独家）
    if group_size >= 3:
        score += 1

    # 标题党惩罚
    if any(w in title for w in CLICKBAIT_WORDS):
        score -= 1

    # 用户兴趣加权（reading_profile.json）
    profile = _load_reading_profile()
    if profile:
        sp = profile.get("source_preference", {})
        if nickname in sp:
            pref = sp[nickname]
            read_rate = pref.get("read", 0) / max(pref.get("offered", 1), 1)
            if read_rate > 0.3:
                score += 2
            elif read_rate > 0.15:
                score += 1

        topic_kw = profile.get("topic_keywords", {})
        for kw in topic_kw:
            if kw in title:
                score += 1
                break  # 最多加 1 分

    return score


def generate_digest(
    groups: list[list[dict]],
    hours: int,
    total_raw: int,
    total_ai: int,
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    # 按 score 排序
    scored = []
    for group in groups:
        best = group[0]
        s = score_article(best, len(group))
        scored.append((s, group))
    scored.sort(key=lambda x: x[0], reverse=True)

    TOP_N = 5
    top_groups = scored[:TOP_N]
    rest_groups = scored[TOP_N:]

    # 热点话题：group_size >= 3
    hot_topics = []
    for s, group in scored:
        if len(group) >= 3:
            best = group[0]
            sources = [a.get("nickname", "") for a in group]
            hot_topics.append({"title": best["title"], "count": len(group), "sources": sources})

    lines = []
    lines.append(f"# AI 日报 {today}")
    lines.append("")
    lines.append(
        f"> {total_raw} 篇 → AI {total_ai} 篇 → 合并 {len(groups)} 条 ｜ 最近 {hours}h ｜ {datetime.now().strftime('%H:%M')}"
    )
    lines.append("")

    # ── 必读区 ──
    lines.append(f"## 必读 (Top {len(top_groups)})")
    lines.append("")

    global_idx = 0
    for _score, group in top_groups:
        global_idx += 1
        best = group[0]
        nickname = best.get("nickname", "")
        dt = datetime.fromtimestamp(best["create_time"]).strftime("%m-%d")

        summary_parts = [f"<b>{global_idx}.</b> {best['title']}"]
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

    # ── 速览区 ──
    if rest_groups:
        lines.append("## 速览")
        lines.append("")
        lines.append("| # | 标题 | 来源 | 日期 |")
        lines.append("|---|------|------|------|")

        for _score, group in rest_groups:
            global_idx += 1
            best = group[0]
            nickname = best.get("nickname", "")
            dt = datetime.fromtimestamp(best["create_time"]).strftime("%m-%d")
            title_link = f"[{best['title']}]({best['link']})"
            extra = f" +{len(group)-1}同题" if len(group) > 1 else ""
            lines.append(f"| {global_idx} | {title_link}{extra} | {nickname} | {dt} |")

        lines.append("")

    # ── 热点话题区 ──
    if hot_topics:
        lines.append("## 热点话题")
        lines.append("")
        for topic in hot_topics:
            lines.append(f"**{topic['title'][:30]}{'...' if len(topic['title']) > 30 else ''}** ({topic['count']} 篇报道)")
            lines.append(f"- {', '.join(topic['sources'])}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*入库：把链接发给 Claude → `帮忙加下 <url>`*")

    return "\n".join(lines)


# ── 阅读反馈闭环 ──────────────────────────────────────────

def _parse_digest_articles(digest_path: Path) -> dict[int, dict]:
    """从 digest 文件解析编号→文章映射，支持新旧两种格式"""
    articles = {}
    content = digest_path.read_text(encoding="utf-8")

    # 新格式：必读区 <details> + 速览区表格
    # 匹配 <b>N.</b> 标题 <code>来源</code>
    detail_pattern = re.compile(
        r'<b>(\d+)\.</b>\s*(.+?)\s*<code>([^<]+)</code>\s*<code>(\d{2}-\d{2})</code>'
    )
    link_pattern = re.compile(r'\[原文\]\(([^)]+)\)')

    # 先处理 <details> 块
    blocks = content.split("<details>")
    for block in blocks[1:]:  # skip first part before any <details>
        header_m = detail_pattern.search(block)
        link_m = link_pattern.search(block)
        if header_m:
            num = int(header_m.group(1))
            title = header_m.group(2).strip()
            source = header_m.group(3).strip()
            link = link_m.group(1) if link_m else ""
            articles[num] = {"title": title, "source": source, "link": link}

    # 速览区表格行: | N | [标题](link) | 来源 | 日期 |
    table_pattern = re.compile(
        r'^\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)[^|]*\|\s*([^|]+)\|\s*(\d{2}-\d{2})\s*\|',
        re.MULTILINE,
    )
    for m in table_pattern.finditer(content):
        num = int(m.group(1))
        if num not in articles:
            articles[num] = {
                "title": m.group(2).strip(),
                "source": m.group(4).strip(),
                "link": m.group(3).strip(),
            }

    return articles


def _update_reading_profile(read_articles: list[dict]):
    """更新 reading_profile.json"""
    profile = {}
    if READING_PROFILE_FILE.exists():
        try:
            with open(READING_PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
        except Exception:
            pass

    profile.setdefault("total_offered", 0)
    profile.setdefault("total_read", 0)
    profile.setdefault("source_preference", {})
    profile.setdefault("topic_keywords", {})

    for art in read_articles:
        profile["total_read"] += 1
        source = art.get("source", "")
        if source:
            sp = profile["source_preference"].setdefault(source, {"offered": 0, "read": 0})
            sp["read"] += 1

        # 提取标题关键词（中文 2-4 字，英文 2+ 字母）
        title = art.get("title", "")
        words = _extract_keywords(title)
        for w in words:
            profile["topic_keywords"][w] = profile["topic_keywords"].get(w, 0) + 1

    profile["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(READING_PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def _update_offered_count(num_articles: int, sources: list[str]):
    """在每次生成 digest 后更新 offered 计数"""
    profile = {}
    if READING_PROFILE_FILE.exists():
        try:
            with open(READING_PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
        except Exception:
            pass

    profile.setdefault("total_offered", 0)
    profile.setdefault("total_read", 0)
    profile.setdefault("source_preference", {})
    profile.setdefault("topic_keywords", {})

    profile["total_offered"] += num_articles
    for src in sources:
        sp = profile["source_preference"].setdefault(src, {"offered": 0, "read": 0})
        sp["offered"] += 1

    profile["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(READING_PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def cmd_mark_read(date: str, numbers: list[int]):
    """标记某日简报中的指定文章为已读"""
    digest_path = DIGEST_DIR / f"{date}.md"
    if not digest_path.exists():
        print(f"找不到简报: {digest_path}")
        return

    articles_map = _parse_digest_articles(digest_path)
    if not articles_map:
        print(f"未能从 {digest_path} 解析出文章")
        return

    read_articles = []
    for n in numbers:
        if n in articles_map:
            read_articles.append({"number": n, **articles_map[n]})
        else:
            print(f"  编号 {n} 未找到，跳过")

    if not read_articles:
        print("没有有效的文章编号")
        return

    # 写入 reading_log.jsonl
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "date": date,
        "read_at": datetime.now().isoformat(),
        "articles": read_articles,
    }
    with open(READING_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # 更新 articles_index.json 中的 read_status
    try:
        index = load_articles_index()
        read_titles = {a["title"] for a in read_articles}
        updated = 0
        for art in index["articles"]:
            if art["title"] in read_titles:
                art["read_status"] = "read"
                updated += 1
        if updated:
            with open(ARTICLES_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 更新 reading_profile.json
    _update_reading_profile(read_articles)

    print(f"已标记 {len(read_articles)} 篇文章为已读:")
    for a in read_articles:
        print(f"  #{a['number']} {a['title'][:40]} ({a.get('source', '')})")


def cmd_stats():
    """输出阅读统计"""
    if not READING_LOG_FILE.exists():
        print("暂无阅读记录。使用 --mark-read <date> <numbers> 标记已读文章。")
        return

    # 读取所有 reading log
    entries = []
    with open(READING_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass

    # 最近 30 天
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent = [e for e in entries if e.get("date", "") >= cutoff]

    # 统计 digest 篇数
    digest_files = sorted(DIGEST_DIR.glob("????-??-??.md"))
    recent_digests = [f for f in digest_files if f.stem >= cutoff]
    total_offered = 0
    for df in recent_digests:
        articles = _parse_digest_articles(df)
        total_offered += len(articles)

    # 已读文章
    all_read = []
    source_stats = {}
    topic_stats = {}
    for entry in recent:
        for art in entry.get("articles", []):
            all_read.append(art)
            src = art.get("source", "未知")
            source_stats.setdefault(src, {"read": 0})
            source_stats[src]["read"] += 1

            # 提取关键词
            title = art.get("title", "")
            words = _extract_keywords(title)
            for w in words:
                topic_stats[w] = topic_stats.get(w, 0) + 1

    total_read = len(all_read)
    pct = f"{total_read / total_offered * 100:.1f}%" if total_offered > 0 else "N/A"

    print(f"阅读统计 (最近 30 天):")
    print(f"  日报篇数: {total_offered} 篇")
    print(f"  已读: {total_read} 篇 ({pct})")
    print()

    # 来源 Top 5 — 计算 offered per source from digests
    source_offered = {}
    for df in recent_digests:
        articles = _parse_digest_articles(df)
        for art in articles.values():
            src = art.get("source", "未知")
            source_offered[src] = source_offered.get(src, 0) + 1

    print("  最常读来源 Top 5:")
    sorted_sources = sorted(source_stats.items(), key=lambda x: x[1]["read"], reverse=True)[:5]
    for i, (src, data) in enumerate(sorted_sources, 1):
        offered = source_offered.get(src, "?")
        read_count = data["read"]
        rate = f"{read_count / offered * 100:.0f}%" if isinstance(offered, int) and offered > 0 else "?"
        print(f"    {i}. {src:<16} {read_count}/{offered} ({rate})")

    print()
    print("  最常读话题 Top 5:")
    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for i, (topic, count) in enumerate(sorted_topics, 1):
        print(f"    {i}. {topic:<16} {count} 次")


# ── 选题辅助 ──────────────────────────────────────────────

def _extract_keywords(title: str) -> set[str]:
    """从标题提取关键词（中文 2-4 字词、英文 token）"""
    words = set(re.findall(r'[\u4e00-\u9fff]{2,4}|[A-Za-z][A-Za-z0-9.]*(?:\s+[0-9.]+)?', title))
    stopwords = {"刚刚", "重磅", "最新", "突发", "独家", "一个", "什么", "怎么", "如何",
                 "就是", "可以", "这个", "那个", "还是", "已经", "终于", "居然", "竟然",
                 "为什么", "关于", "但是", "因为", "所以", "不是", "只是", "还有", "然而",
                 "来了", "出了", "看看", "我们", "他们", "自己", "真的", "到底",
                 "the", "and", "for", "with", "from", "that", "this", "are", "was",
                 "not", "but", "all", "has", "had", "will", "how", "can", "its"}
    return {w.strip() for w in words if w.strip() not in stopwords and len(w.strip()) >= 2}


def cmd_trends():
    """输出最近 3 天的热点趋势"""
    digest_files = sorted(DIGEST_DIR.glob("????-??-??.md"), reverse=True)[:3]
    if not digest_files:
        print("没有找到 digest 文件")
        return

    today_file = digest_files[0] if digest_files else None
    today_stem = today_file.stem if today_file else ""
    older_stems = {f.stem for f in digest_files[1:]}

    all_keywords = {}  # keyword → count
    today_keywords = set()
    older_keywords = set()
    total_articles = 0

    for df in digest_files:
        articles = _parse_digest_articles(df)
        total_articles += len(articles)
        for art in articles.values():
            words = _extract_keywords(art.get("title", ""))
            for w in words:
                all_keywords[w] = all_keywords.get(w, 0) + 1
                if df.stem == today_stem:
                    today_keywords.add(w)
                else:
                    older_keywords.add(w)

    # 排序，标注 NEW
    sorted_kw = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)

    days = len(digest_files)
    print(f"热点趋势 (最近 {days} 天, {total_articles} 篇):")
    print()

    max_count = sorted_kw[0][1] if sorted_kw else 1
    for kw, count in sorted_kw[:15]:
        bar_len = int(count / max_count * 12)
        bar = "█" * bar_len

        is_new = kw in today_keywords and kw not in older_keywords and days > 1
        if is_new:
            label = "🆕"
        elif count >= 5:
            label = "🔥"
        else:
            label = "  "

        new_tag = "  ← 新话题" if is_new else ""
        print(f"  {label} {kw:<16} {count} 次   {bar}{new_tag}")


def cmd_search(keyword: str):
    """搜索知识库和近期简报中匹配的文章"""
    kw_lower = keyword.lower()
    results_kb = []
    results_digest = []

    # 1. 搜索 articles_index.json
    try:
        index = load_articles_index()
        for art in index["articles"]:
            title = art.get("title", "")
            tags = " ".join(art.get("tags", []))
            if kw_lower in title.lower() or kw_lower in tags.lower():
                results_kb.append(art)
    except Exception:
        pass

    # 2. 搜索最近 7 天 digest
    digest_files = sorted(DIGEST_DIR.glob("????-??-??.md"), reverse=True)[:7]
    for df in digest_files:
        articles = _parse_digest_articles(df)
        for num, art in sorted(articles.items()):
            if kw_lower in art.get("title", "").lower():
                results_digest.append({"date": df.stem, "number": num, **art})

    total = len(results_kb) + len(results_digest)
    print(f'搜索: "{keyword}" ({total} 条匹配)')
    print()

    if results_kb:
        print("  知识库:")
        for art in results_kb:
            status = "已读" if art.get("read_status") == "read" else "未读"
            print(f"    [{status}] {art['title']} ({art.get('author', '')}, {art.get('crawl_date', '')})")
            print(f"           → knowledge_base/{art.get('path', '')}/")
        print()

    if results_digest:
        print("  近期简报:")
        for art in results_digest:
            print(f"    {art['date']} #{art['number']}  {art['title'][:50]} ({art.get('source', '')})")


# ── digest-site 构建 ─────────────────────────────────────
def cmd_build_site():
    """生成/更新 digest-site 静态站"""
    site_digests = SITE_DIR / "digests"
    site_digests.mkdir(parents=True, exist_ok=True)

    # 1. 复制所有 YYYY-MM-DD.md 到 site_digests/
    copied = 0
    for f in DIGEST_DIR.glob("????-??-??.md"):
        shutil.copy2(f, site_digests / f.name)
        copied += 1

    # 2. 生成 index.json
    dates = sorted([f.stem for f in site_digests.glob("????-??-??.md")], reverse=True)
    index = [{"date": d} for d in dates]
    (SITE_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))

    # 3. 确保 index.html 存在（首次从同目录模板复制）
    html_path = SITE_DIR / "index.html"
    if not html_path.exists():
        print(f"警告: {html_path} 不存在，请手动放置 index.html")

    print(f"digest-site 已更新: {copied} 篇 → {SITE_DIR}")

    # 4. 部署到 Vercel
    if shutil.which("vercel") and (SITE_DIR / ".vercel").is_dir():
        print("正在部署到 Vercel...")
        result = subprocess.run(
            ["vercel", "--yes", "--prod"],
            cwd=SITE_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            # 从输出中提取 URL
            for line in result.stdout.splitlines():
                if "https://" in line and "vercel.app" in line:
                    print(f"已部署: {line.strip()}")
                    break
            else:
                print("Vercel 部署完成")
        else:
            print(f"Vercel 部署失败: {result.stderr.strip()}")
    elif not shutil.which("vercel"):
        print("跳过部署: vercel CLI 未安装")
    else:
        print("跳过部署: 尚未初始化 Vercel 项目（先手动运行 vercel 一次）")


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
    # Feature 3: 阅读反馈
    parser.add_argument("--mark-read", nargs="+", metavar=("DATE", "NUM"), help="标记已读: --mark-read 2026-02-20 1 3 5")
    parser.add_argument("--stats", action="store_true", help="输出阅读统计")
    # Feature 4: 选题辅助
    parser.add_argument("--trends", action="store_true", help="输出最近 3 天热点趋势")
    parser.add_argument("--search", type=str, metavar="KEYWORD", help="搜索知识库和简报中的文章")
    parser.add_argument("--build-site", action="store_true", help="构建/更新 digest-site 静态站")
    args = parser.parse_args()

    # Feature 3 子命令
    if args.mark_read:
        date = args.mark_read[0]
        numbers = [int(n) for n in args.mark_read[1:]]
        cmd_mark_read(date, numbers)
        return

    if args.stats:
        cmd_stats()
        return

    # Feature 4 子命令
    if args.trends:
        cmd_trends()
        return

    if args.search:
        cmd_search(args.search)
        return

    if args.build_site:
        cmd_build_site()
        return

    if manage_accounts(args):
        return

    log("=" * 60)
    log("AI 日报简报 开始生成")
    log("=" * 60)

    # 1. 检查 exporter
    if not check_exporter():
        log("exporter 服务不可达 (localhost:3000)，退出")
        notify("AI 日报失败", "exporter 不可达 (localhost:3000)")
        sys.exit(1)
    log("exporter 服务正常")

    # 2. 获取 auth-key
    try:
        auth_key = get_auth_key()
        log(f"auth-key 已获取 ({auth_key[:8]}...)")
    except Exception as e:
        log(f"获取 auth-key 失败: {e}")
        log("请先在浏览器中登录 exporter (localhost:3000)")
        notify("AI 日报失败", "auth-key 获取失败，请登录 exporter")
        sys.exit(1)

    # 2.5 健康检查：验证 auth-key 实际可用
    try:
        test_r = _api_get(
            f"{EXPORTER_BASE}/api/web/mp/searchbiz",
            params={"keyword": "虎嗅"},
            headers={"X-Auth-Key": auth_key},
        )
        test_data = test_r.json()
        if not test_data.get("list"):
            raise ValueError("auth-key 验证失败：搜索返回空结果")
        log("auth-key 验证通过")
    except Exception as e:
        log(f"auth-key 验证失败: {e}")
        notify("AI 日报失败", "auth-key 过期或无效")
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
    notify("AI 日报", f"{len(groups)} 条新文章 → digests/{today}.md")

    # 更新 reading_profile 的 offered 计数
    sources = [g[0].get("nickname", "") for g in groups if g]
    _update_offered_count(len(groups), sources)

    # 自动更新 digest-site
    cmd_build_site()

    devlog({
        "type": "task",
        "context": "ai_digest",
        "action": f"生成 AI 日报 ({args.hours}h)",
        "result": f"全部 {total_raw} → AI {total_ai} → 去重 {len(fresh)} → 合并 {len(groups)} 条",
    })


if __name__ == "__main__":
    main()
