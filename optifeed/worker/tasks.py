from optifeed.api.app import publish_task
from optifeed.db.sqlite_utils import get_unsent_analyzed_news, mark_as_sent
from optifeed.utils.logger import logger


def escape_markdown(text: str) -> str:
    """
    Escape MarkdownV2 special chars for Telegram.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in escape_chars else c for c in (text or ""))


def detect_signals_and_push():
    """Detect significant market signals and push alerts to Telegram."""
    logger.info("🚀 Checking for new signals...")

    news_items = get_unsent_analyzed_news()
    logger.info(f"✅ Found {len(news_items)} unsent analyzed items.")

    impactful = [n for n in news_items if (n.magnitude_score or 0) > 0.5]
    logger.info(f"✅ {len(impactful)} items with magnitude > 0.5.")

    if not impactful:
        logger.info("🎯 Nothing significant today.")
        return

    for news in impactful:
        text = (
            f"*🗞️ Market Signal*\n\n"
            f"{escape_markdown(news.text)}\n\n"
            f"• Impact: *{round(news.impact_score or 0, 2)}*\n"
            f"• Magnitude: *{round(news.magnitude_score or 0, 2)}*\n"
            f"• Sectors: _{', '.join([escape_markdown(s) for s in news.affected_sectors or ['Other']])}_"
        )

        publish_task(
            {
                "type": "alert",
                "message": text,
            }
        )

        mark_as_sent(news.id)
        logger.success(f"✅ Sent alert for news id {news.id}")

    logger.info("🎯 detect_signals_and_push() completed.")
