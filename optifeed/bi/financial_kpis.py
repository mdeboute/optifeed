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
            companyName=info.get("shortName", ""),
            marketCap=info.get("marketCap"),
            price=info.get("regularMarketPrice"),
            peRatio=info.get("trailingPE"),
            roe=info.get("returnOnEquity"),
            profitMargin=info.get("profitMargins"),
            debtEquity=info.get("debtToEquity"),
        )
    except Exception as e:
        logger.error(f"❌ Failed fetching financials for {ticker}: {e}")
        return TickerKPIs(ticker=ticker)
