import os

from dotenv import load_dotenv

load_dotenv()

# API keys & tokens
FMP_API_KEY = os.getenv("FMP_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_BOT_USERNAME = "@macro_hedge_bot"

# Gmail API configuration
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
GMAIL_TOKEN_FILE = "token.json"
GMAIL_CREDENTIALS_FILE = "credentials.json"

DEFAULT_BRAVE_NEWS_LIMIT = 30

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
DEFAULT_LLM_MODEL = "gemini-2.5-flash-lite-preview-06-17"

# Telegram admin user
ADMIN_USER = os.getenv("ADMIN_USER")

# Pipeline alerts
ALERTS_ENABLED_FILE = os.path.join(
    os.path.dirname(__file__), "../..", "alerts_enabled.flag"
)
