import sqlite3

from db.models import AnalyzedNews, NewsItem
from utils.config import SQL_DB_FILE
from utils.logger import logger


def init_db():
    """Initialize the SQLite database and create the necessary tables."""
    logger.info("Initializing SQLite database...")
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            text TEXT,
            tickers TEXT,
            date TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analyzed_news (
            id TEXT PRIMARY KEY,
            text TEXT,
            impact_score REAL,
            magnitude_score REAL,
            affected_sectors TEXT,
            sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()
    logger.info("✅ Database initialized (tables created if not exist).")


def is_cached(news_id: str) -> bool:
    """Check if a news item with the given ID is already cached in `news`."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM news WHERE id = ?", (news_id,))
    result = cur.fetchone()
    conn.close()
    logger.debug(
        f"News item with id {news_id} is {'cached' if result else 'not cached'}."
    )
    return result is not None


def save_news_items(news_items: list[NewsItem]):
    """Save a list of NewsItem objects to the `news` table."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()
    for item in news_items:
        try:
            cur.execute(
                """
                INSERT INTO news (id, text, tickers, date, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item.id, item.text, item.tickers, item.date, item.source),
            )
        except sqlite3.IntegrityError:
            logger.debug(f"Skipped duplicate news id {item.id}")
    conn.commit()
    conn.close()
    logger.info(f"✅ Saved {len(news_items)} raw news items.")


def save_analyzed_news(news: AnalyzedNews):
    """Save an analyzed news item to the `analyzed_news` table with sent=0 by default."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO analyzed_news 
            (id, text, impact_score, magnitude_score, affected_sectors, sent)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                news.id,
                news.text,
                news.impact_score,
                news.magnitude_score,
                ",".join(news.affected_sectors),
                0,  # sent=0 pour marquer comme non envoyé
            ),
        )
        logger.debug(f"Inserted analyzed news id {news.id}")
    except sqlite3.IntegrityError:
        logger.debug(f"Skipped duplicate analyzed news id {news.id}")
    conn.commit()
    conn.close()


def get_all_cached_news() -> list[NewsItem]:
    """Retrieve all cached news items as NewsItem objects from `news`."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, text, tickers, date, source FROM news ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return [
        NewsItem(id=row[0], text=row[1], tickers=row[2], date=row[3], source=row[4])
        for row in rows
    ]


def get_unsent_analyzed_news() -> list[AnalyzedNews]:
    """Retrieve unsent analyzed news items from `analyzed_news`."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, text, impact_score, magnitude_score, affected_sectors 
        FROM analyzed_news 
        WHERE sent IS NULL OR sent = 0
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        AnalyzedNews(
            id=row[0],
            text=row[1],
            impact_score=row[2],
            magnitude_score=row[3],
            affected_sectors=row[4].split(",") if row[4] else [],
        )
        for row in rows
    ]


def mark_as_sent(news_id: str):
    """Mark an analyzed news item as sent in the `analyzed_news` table."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE analyzed_news SET sent = 1 WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()
    logger.debug(f"Marked analyzed news id {news_id} as sent.")
