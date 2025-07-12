from typing import List, Optional

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """News item model for storing preprocessed news data."""
    id: str
    text: str
    tickers: Optional[str] = None
    date: str
    source: str


class AnalyzedNews(BaseModel):
    """Analyzed news model for storing macroeconomic analysis results."""
    id: str
    text: str
    impact_score: Optional[float] = None
    magnitude_score: Optional[float] = None
    affected_sectors: List[str] = Field(default_factory=list)


class TickerKPIs(BaseModel):
    """Ticker KPIs model for storing financial data of a stock."""
    ticker: str
    companyName: Optional[str] = ""
    marketCap: Optional[int] = None
    price: Optional[float] = None
    peRatio: Optional[float] = None
    roe: Optional[float] = None
    profitMargin: Optional[float] = None
    debtEquity: Optional[float] = None


class TickerTendency(BaseModel):
    """Ticker tendency model for storing microeconomic analysis results."""
    ticker: str
    micro_score: Optional[float] = None
    rationale: Optional[str] = ""
    suggested_action: Optional[str] = ""
    news_id: str
