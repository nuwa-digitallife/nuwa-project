"""Twitter 采集配置"""
import os

# === 路径 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_DIR = os.path.join(BASE_DIR, "auth")
DATA_DIR = os.path.join(BASE_DIR, "data")
TWEETS_DIR = os.path.join(DATA_DIR, "tweets")
SIGNALS_DIR = os.path.join(DATA_DIR, "signals")
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# === Twitter List ===
LIST_URL = "https://x.com/i/lists/2024053078484521383"

# === 抓取参数 ===
PAGE_TIMEOUT_MS = 60_000       # 页面加载超时
TWEET_WAIT_TIMEOUT_MS = 30_000 # 等待推文元素出现
SCROLL_COUNT = 3               # 向下滚动次数（加载更多推文）
SCROLL_DELAY_MS = 2000         # 每次滚动后等待时间

# === DOM 选择器（Twitter/X 关键选择器，集中管理便于维护）===
SELECTORS = {
    "tweet":       '[data-testid="tweet"]',
    "tweet_text":  '[data-testid="tweetText"]',
    "time":        "time[datetime]",
    "status_link": 'a[href*="/status/"]',
    "user_link":   'a[role="link"][href^="/"]',
    "reply":       '[data-testid="reply"]',
    "retweet":     '[data-testid="retweet"]',
    "like":        '[data-testid="like"]',
}

# === 热点检测阈值 ===
HOT_TOPIC_MIN_HANDLES = 3     # 至少 N 个不同 KOL 提到才算热点
ENGAGEMENT_WEIGHT = 0.001     # 互动数据权重因子

# === 目标 KOL 列表（用于验证）===
TARGET_HANDLES = [
    "elonmusk", "demaborsa", "DarioAmodei", "ylecun",
    "DrJimFan", "AndrewYNg", "sama", "GaryMarcus",
    "fchollet", "hardmaru", "ClementDelangue", "JeffDean",
    "svpino", "kaborosx", "EMostaque",
]
