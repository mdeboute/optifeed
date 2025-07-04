import os

from dotenv import load_dotenv

load_dotenv()

# API keys & tokens
FMP_API_KEY = os.getenv("FMP_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DEFAULT_NEWS_LIMIT = 30

# Directories
DATA_DIR = os.path.join(os.path.dirname(__file__), "../..", "data")
SQL_DB_FILE = os.path.join(DATA_DIR, "news.db")
LOG_DIR = os.path.join(os.path.dirname(__file__), "../..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# RabbitMQ configuration
RABBIT_HOST = os.getenv("RABBIT_HOST")
RABBIT_USER = os.getenv("RABBIT_USER")
RABBIT_PASS = os.getenv("RABBIT_PASS")

# LLM
LLM_MODEL = "gemini-2.0-flash-lite"
