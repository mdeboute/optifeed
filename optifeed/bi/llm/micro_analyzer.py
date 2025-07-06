from typing import Optional

import google.generativeai as genai

from optifeed.bi.llm.macro_analyzer import parse_gemini_json
from optifeed.db.models import AnalyzedNews, TickerKPIs, TickerTendency
from optifeed.utils.config import GOOGLE_API_KEY, LLM_MODEL
from optifeed.utils.logger import logger

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(LLM_MODEL)


def analyze_micro(
    news: AnalyzedNews, financial_data: TickerKPIs
) -> Optional[TickerTendency]:
    prompt = f"""
    You are a senior equity analyst assistant.

    Given:
    - This macroeconomic news impact analysis:
    Text: {news.text}
    Impact score: {news.impact_score}
    Magnitude score: {news.magnitude_score}
    Reasoning: {news.reasoning}
    - And these fundamentals for {financial_data.ticker}:
    Company: {financial_data.companyName or "N/A"}
    Market Cap: {financial_data.marketCap or "N/A"}
    Price: {financial_data.price or "N/A"}
    PE Ratio: {financial_data.peRatio or "N/A"}
    ROE: {financial_data.roe or "N/A"}
    Profit Margin: {financial_data.profitMargin or "N/A"}
    Debt/Equity: {financial_data.debtEquity or "N/A"}

    Please respond ONLY in this exact JSON format:
    {{
    "micro_score": float between -1 and 1,
    "rationale": "short explanation (max 5 lines)",
    "suggested_action": "buy / hold / sell / watch"
    }}
    """
    try:
        response = model.generate_content(prompt)
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
