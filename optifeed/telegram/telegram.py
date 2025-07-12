import requests

from optifeed.utils.config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from optifeed.utils.logger import logger


def send_telegram_message(message: str, parse_mode: str = "MarkdownV2"):
    """
    Sends a Telegram message via the Bot HTTP API using predefined TOKEN and CHAT_ID.
    Supports optional parse_mode ("MarkdownV2", "HTML", etc.).
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": str(TELEGRAM_CHAT_ID),
        "text": message,
        "parse_mode": parse_mode,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"✅ Sent Telegram message: {message[:60]}...")
        return json_response
    except requests.RequestException as e:
        logger.error(f"❌ Failed to send Telegram message: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}
