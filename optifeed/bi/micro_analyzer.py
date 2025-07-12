from typing import Optional

from optifeed.bi.macro_analyzer import parse_gemini_json
from optifeed.db.models import AnalyzedNews, TickerKPIs, TickerTendency
from optifeed.utils.llm import ask_something
from optifeed.utils.logger import logger


def analyze_micro(
    news: AnalyzedNews, financial_data: TickerKPIs
) -> Optional[TickerTendency]:
    """Analyze microeconomic impact of macro news on a specific ticker."""
    prompt = f"""
    You are a senior equity analyst assistant.

    Given:
    - This macroeconomic news impact analysis:
    Text: {news.text}
    Impact score: {news.impact_score}
    Magnitude score: {news.magnitude_score}
    Reasoning: {news.reasoning}
    - And these fundamentals for {financial_data.ticker}:
    Company: {financial_data.company_name or "N/A"}
    Market Cap: {financial_data.market_cap or "N/A"}
    Price: {financial_data.price or "N/A"}
    PE Ratio: {financial_data.pe_ratio or "N/A"}
    ROE: {financial_data.roe or "N/A"}
    Profit Margin: {financial_data.profit_margin or "N/A"}
    Debt/Equity: {financial_data.debt_equity or "N/A"}

    Please respond ONLY in this exact JSON format:
    {{
    "micro_score": float between -1 and 1,
    "rationale": "short explanation (max 5 lines)",
    "suggested_action": "buy / hold / sell / watch"
    }}
    """
    try:
        response = ask_something(prompt)
        data = parse_gemini_json(response.text)
        if not data:
            return None
        return TickerTendency(
            ticker=financial_data.ticker,
            micro_score=data.get("micro_score"),
            rationale=data.get("rationale"),
            suggested_action=data.get("suggested_action"),
            news_id=news.id,
        )
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        return None
