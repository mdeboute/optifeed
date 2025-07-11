import json
import re
from typing import Optional

from optifeed.db.models import AnalyzedNews, NewsItem
from optifeed.utils.config import model
from optifeed.utils.logger import logger


def parse_gemini_json(text: str) -> Optional[dict]:
    """Remove markdown ```json ... ``` if present and parse JSON."""
    try:
        cleaned = re.sub(r"^```json|^```|```$", "", text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode failed: {e}")
        return None


def analyze_macro(news_item: NewsItem) -> Optional[AnalyzedNews]:
    prompt = f"""
    You are a senior macroeconomic analyst assistant.

    Given the following news, your task is to analyze its impact on financial markets and return ONLY in valid JSON format like this:
    {{
    "impact_score": float between -1 and 1,
    "magnitude_score": float between 0 and 1,
    "reasoning": "short explanation (max 5 lines)",
    "affected_sectors": ["list of sectors or industries"],
    "affected_companies": ["list of company names or tickers"],
    "affected_stocks": ["list of tickers or ETFs that could be traded"]
    }}

    Guidelines:
    - The impact_score reflects whether this is positive (near +1) or negative (near -1) for markets.
    - The magnitude_score reflects how significant this news is (near 1 = major, near 0 = minor).
    - Always provide `affected_sectors` and `affected_stocks`, even if the news doesn't mention any explicitly. Infer reasonable candidates based on the macro context.
    - If there are no explicit companies, propose tickers or ETFs that might be influenced by this type of news (e.g., "SPY", "XLF", "TSLA").
    - Keep the reasoning concise, max 10 lines.

    Text: {news_item.text}
    Tickers: {news_item.tickers}
    Date: {news_item.date}
    Source: {news_item.source}
    """
    try:
        response = model.generate_content(prompt)
        data = parse_gemini_json(response.text)
        if not data:
            return None

        return AnalyzedNews(
            id=news_item.id,
            text=data.get("reasoning"),
            impact_score=data.get("impact_score"),
            magnitude_score=data.get("magnitude_score"),
            affected_sectors=data.get("affected_sectors"),
        )
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        return None
