from optifeed.bi.macro_analyzer import analyze_macro
from optifeed.bi.news import (
    fetch_all_news,
    filter_and_categorize,
    filter_last_day,
    preprocess_news,
)
from optifeed.db.sqlite_utils import (
    init_db,
    is_cached,
    save_analyzed_news,
    save_news_items,
)
from optifeed.utils.logger import logger
from optifeed.worker.tasks import detect_signals_and_push


def main():
    logger.info("🚀 Starting daily pipeline...")

    # Init DB
    init_db()

    # Fetch fresh news
    news_items = fetch_all_news()
    logger.info(f"✅ Fetched {len(news_items)} raw news items.")

    # Filter for last 24 hours
    recent_news = filter_last_day(news_items)
    logger.info(f"✅ {len(recent_news)} news items are from last 24 hours.")

    # Categorize and filter
    categorized_news = filter_and_categorize(recent_news)

    # Preprocess into cleaned NewsItem objects
    processed_news = preprocess_news(categorized_news)

    # Filter out duplicates
    new_items = [item for item in processed_news if not is_cached(item.id)]
    logger.info(f"✅ {len(new_items)} new items after deduplication.")

    # Save to raw news table
    save_news_items(new_items)
    logger.info(f"✅ Saved {len(new_items)} new items to the news table.")

    # Analyze with Gemini and save to analyzed_news table
    analyzed_count = 0
    for item in new_items:
        analysis = analyze_macro(item)
        save_analyzed_news(analysis)
        analyzed_count += 1
        logger.success(
            f"✅ Analyzed {item.id} with magnitude {analysis.magnitude_score:.2f}, "
        )

    logger.info(f"🎯 Analysis completed. Total analyzed: {analyzed_count}.")

    # Now detect signals & publish alerts
    detect_signals_and_push()
    logger.info("🎯 Pipeline fully completed.")


if __name__ == "__main__":
    main()
