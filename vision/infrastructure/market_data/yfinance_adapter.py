from datetime import date

import yfinance as yf

from vision.domain.core.currency import Currency
from vision.domain.market_data.models import AssetInfo, PriceHistory
from vision.domain.market_data.repository import MarketDataRepository


class YFinanceMarketDataRepository(MarketDataRepository):
    def get_price_history(self, ticker: str, start: date, end: date) -> PriceHistory:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start.isoformat(), end=end.isoformat())
        if df.empty:
            return PriceHistory(ticker=ticker, dates=[], close_prices=[], volumes=[])
        dates = [d.date() for d in df.index]
        close_prices = df["Close"].tolist()
        volumes = df["Volume"].astype(int).tolist()
        return PriceHistory(
            ticker=ticker,
            dates=dates,
            close_prices=close_prices,
            volumes=volumes,
        )

    def get_asset_info(self, ticker: str) -> AssetInfo:
        stock = yf.Ticker(ticker)
        info = stock.info
        return AssetInfo(
            ticker=ticker,
            name=info.get("longName", ticker),
            sector=info.get("sector", "Unknown"),
            currency=info.get("currency", Currency.USD.value),
        )

    def validate_ticker(self, ticker: str) -> bool:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get("regularMarketPrice") is not None
        except Exception:
            return False
