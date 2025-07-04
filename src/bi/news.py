import hashlib
import re
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from db.models import NewsItem
from utils.config import BRAVE_API_KEY, DEFAULT_NEWS_LIMIT, FMP_API_KEY
from utils.logger import logger


# === Utilities ===
def clean_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text()


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_tickers(text):
    return re.findall(r"\$[A-Z]{1,6}|\b[A-Z]{2,5}:[A-Z]{2,3}\b", text or "")


def hash_event(headline):
    return hashlib.sha256(headline.encode()).hexdigest()


def parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = date_parser.parse(date_str)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    ago_match = re.match(r"(\d+)\s+(day|week|hour|minute|second)s?\s+ago", date_str)
    if ago_match:
        qty = int(ago_match.group(1))
        unit = ago_match.group(2)
        now = datetime.now(timezone.utc)
        if unit == "day":
            return now - timedelta(days=qty)
        elif unit == "week":
            return now - timedelta(weeks=qty)
        elif unit == "hour":
            return now - timedelta(hours=qty)
        elif unit == "minute":
            return now - timedelta(minutes=qty)
        elif unit == "second":
            return now - timedelta(seconds=qty)
    return None


def filter_last_day(news_items):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    filtered = []
    for item in news_items:
        dt = parse_date(item["published"])
        if dt and dt >= cutoff:
            filtered.append(item)
    return filtered


# === Fetching ===
def fetch_fmp_news():
    logger.info("Fetching news from Financial Modeling Prep...")
    url = f"https://financialmodelingprep.com/api/v3/fmp/articles?apikey={FMP_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as e:
        logger.error(f"❌ FMP fetch error: {e}")
        return []
    articles = data.get("content", [])
    logger.info(f"✅ FMP loaded {len(articles)} articles.")
    return articles


def fetch_brave_news():
    logger.info("Fetching news from Brave Search...")
    url = "https://api.search.brave.com/res/v1/news/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    query = (
        "earnings OR acquisition OR downgrade OR bankruptcy OR war OR oil OR inflation OR "
        "fed OR ECB OR recession OR strike OR cyberattack OR terror OR election OR commodities OR climate OR terrorist"
    )
    params = {"q": query, "count": DEFAULT_NEWS_LIMIT}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        data = resp.json()
        articles = data.get("results", [])
    except Exception as e:
        logger.error(f"❌ Brave fetch error: {e}")
        return []
    logger.info(f"✅ Brave loaded {len(articles)} articles.")
    return articles


def build_event(headline, body, published, tickers, source):
    return {
        "headline": headline,
        "body": body,
        "tickers": tickers or extract_tickers(headline + " " + body),
        "published": published,
        "id": hash_event(headline),
        "source": source,
    }


def fetch_all_news():
    logger.info("Fetching news from all sources...")
    now_str = datetime.now(timezone.utc).isoformat()
    events = []

    # FMP
    for item in fetch_fmp_news():
        headline = clean_html(item.get("title", "No title"))
        body = clean_html(item.get("content", ""))
        published = item.get("date", now_str)
        source = item.get("link", "FMP")
        events.append(
            build_event(headline, body, published, item.get("tickers"), source)
        )

    # Brave
    for item in fetch_brave_news():
        headline = clean_html(item.get("title", "No title"))
        body = clean_html(item.get("description", ""))
        published = item.get("age", now_str)
        source = item.get("url", "Brave")
        events.append(build_event(headline, body, published, None, source))

    logger.info(f"✅ Aggregated {len(events)} news items from all sources.")
    return events


# === Filtering and categorization ===
THEMES = {
    "earnings": {"earnings", "profits", "result", "quarter"},
    "m&a": {"acquisition", "merger", "buyout", "takeover"},
    "downgrade": {"downgrade", "rating"},
    "oil": {"oil", "crude", "barrel"},
    "inflation": {"inflation", "cpi", "ppi"},
    "central_banks": {"fed", "ecb", "rate hike", "interest rates", "monetary"},
    "war_geo": {
        "war",
        "attack",
        "russia",
        "ukraine",
        "israel",
        "palestine",
        "china",
        "taiwan",
        "iran",
    },
    "bankruptcy": {"bankruptcy", "insolvency", "chapter 11"},
    "strikes": {"strike", "union", "protest"},
    "cyber": {"cyber", "hack", "data breach"},
    "climate": {"climate", "hurricane", "flood", "wildfire"},
    "elections": {"election", "vote", "ballot"},
}


def filter_and_categorize(events):
    filtered = []
    theme_counter = Counter()

    for event in events:
        text = (event["headline"] + " " + event["body"]).lower()
        matched = False
        for theme, keywords in THEMES.items():
            if any(word in text for word in keywords):
                theme_counter[theme] += 1
                matched = True
        if matched:
            filtered.append(event)

    logger.info(f"✅ Filtered and categorized {len(filtered)} news items.")
    logger.info("Themes: " + ", ".join(f"{k}: {v}" for k, v in theme_counter.items()))
    return filtered


def preprocess_news(events) -> list[NewsItem]:
    cleaned_news = []
    for event in events:
        full_text = normalize_text(event["headline"] + " " + event["body"])
        tickers = extract_tickers(full_text)
        item = NewsItem(
            id=event["id"],
            text=full_text,
            tickers=str(tickers),
            date=event["published"],
            source=event["source"],
        )
        cleaned_news.append(item)
    logger.info(
        f"✅ Preprocessed {len(cleaned_news)} news items into NewsItem objects."
    )
    return cleaned_news
