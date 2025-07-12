import yfinance as yf

from optifeed.db.models import TickerKPIs
from optifeed.utils.logger import logger


def fetch_financial_kpis(ticker: str) -> TickerKPIs:
    """Fetch financial KPIs for a given stock ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return TickerKPIs(
            ticker=ticker,
            company_name=info.get("shortName", ""),
            market_cap=info.get("marketCap"),
            price=info.get("regularMarketPrice"),
            pe_ratio=info.get("trailingPE"),
            roe=info.get("returnOnEquity"),
            profit_margin=info.get("profitMargins"),
            debt_equity=info.get("debtToEquity"),
        )
    except Exception as e:
        logger.error(f"❌ Failed fetching financials for {ticker}: {e}")
        return TickerKPIs(ticker=ticker)
