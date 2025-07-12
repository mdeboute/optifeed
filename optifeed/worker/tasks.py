from optifeed.api.app import publish_task
from optifeed.db.sqlite_utils import get_unsent_analyzed_news, mark_as_sent
from optifeed.telegram.telegram import escape_markdown_v2
from optifeed.utils.logger import logger

# --- Telegram constants
MAX_MESSAGE_LENGTH = 4096
SOFT_LIMIT = 3900


def format_signal_message(news) -> str:
    """
    Format a news item as a MarkdownV2-safe Telegram message.
    """
    escaped_text = escape_markdown_v2(news.text)
    sectors = news.affected_sectors or ["Other"]
    escaped_sectors = ", ".join(escape_markdown_v2(s) for s in sectors)

    header = "*🗞️ Market Signal*\n\n"
    footer = (
        f"\n\n• Impact: *{round(news.impact_score or 0, 2)}*"
        f"\n• Magnitude: *{round(news.magnitude_score or 0, 2)}*"
        f"\n• Sectors: _{escaped_sectors}_"
    )

    return header + escaped_text + footer


def split_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Split a long message into multiple chunks for Telegram.
    Prefers to cut at newlines, falls back to hard cut.
    """
    chunks = []
    while len(message) > max_length:
        split_at = message.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length  # no newline, hard split

        chunks.append(message[:split_at].strip())
        message = message[split_at:].strip()

    if message:
        chunks.append(message)

    return chunks


def detect_signals_and_push():
    """
    Detect significant market signals and push them to Telegram as tasks.
    """
    logger.info("🚀 Checking for new signals...")

    news_items = get_unsent_analyzed_news()
    logger.info(f"✅ Found {len(news_items)} unsent analyzed items.")

    impactful = [n for n in news_items if (n.magnitude_score or 0) > 0.7]
    logger.info(f"✅ {len(impactful)} items with magnitude > 0.7.")

    if not impactful:
        logger.info("🎯 Nothing significant today.")
        return

    for news in impactful:
        full_message = format_signal_message(news)
        message_parts = split_message(full_message)

        for idx, part in enumerate(message_parts, 1):
            if len(message_parts) > 1:
                part = f"*Part {idx}/{len(message_parts)}*\n\n{part}"

            publish_task(
                {
                    "type": "alert",
                    "message": part,
                }
            )

        mark_as_sent(news.id)
        logger.success(f"✅ Sent {len(message_parts)} part(s) for news id {news.id}")

    logger.info("🎯 detect_signals_and_push() completed.")
