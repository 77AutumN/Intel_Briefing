"""
Intel Briefing - 统一配置模块
所有硬编码常量集中管理
"""
import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# --- Logging ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_file: str = None):
    """配置全局日志。"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=handlers,
        force=True,
    )


# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PRODUCTHUNT_TOKEN = os.getenv("PRODUCTHUNT_TOKEN")

# --- API Endpoints ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.5-flash-lite"
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1/chat/completions")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-beta")
GITHUB_API_URL = "https://api.github.com/graphql"
JINA_READER_URL = "https://r.jina.ai/"

# --- Timeouts (seconds) ---
DEFAULT_TIMEOUT = 15
GEMINI_TIMEOUT = 60
JINA_TIMEOUT = 30
GROK_TIMEOUT = 60

# --- Content Limits ---
CONTENT_TRUNCATE_LIMIT = 3000
JINA_MAX_CHARS = 15000
PH_HYDRATION_TRUNCATE = 5000
GEMINI_MAX_OUTPUT_TOKENS = 1024
GEMINI_SUMMARY_MAX_TOKENS = 256
GEMINI_DETAIL_MAX_TOKENS = 1024

# --- Rate Limiting ---
GEMINI_RATE_LIMIT_DELAY = 1.5  # seconds between Gemini API calls
GEMINI_MAX_RETRIES = 3

# --- Fetch Limits ---
MAX_BLOGS_TO_FETCH = 20
MAX_ARTICLES_PER_BLOG = 2
RSS_FETCH_TIMEOUT = 10

# --- Deduplication ---
DEDUP_SIMILARITY_THRESHOLD = 0.85
