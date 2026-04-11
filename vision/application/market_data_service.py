from datetime import date

from sqlalchemy import select
from sqlalchemy.engine import Engine

from vision.domain.market_data.models import PriceHistory
from vision.domain.market_data.repository import MarketDataRepository
from vision.domain.market_data.services import MarketDataService
from vision.infrastructure.database.models import price_cache


class MarketDataAppService:
    def __init__(
        self,
        repo: MarketDataRepository,
        engine: Engine,
    ) -> None:
        self._repo = repo
        self._engine = engine
        self._domain_service = MarketDataService()

    def get_price_history(
        self, ticker: str, start: date, end: date
    ) -> PriceHistory:
        cached = self._load_from_cache(ticker, start, end)
        if cached and len(cached.dates) > 0:
            return cached

        fresh = self._repo.get_price_history(ticker, start, end)
        self._save_to_cache(fresh)
        return fresh

    def get_daily_returns(
        self, ticker: str, start: date, end: date
    ) -> list[tuple[date, float]]:
        ph = self.get_price_history(ticker, start, end)
        return MarketDataService.compute_daily_returns(ph)

    def validate_ticker(self, ticker: str) -> bool:
        return self._repo.validate_ticker(ticker)

    def _load_from_cache(
        self, ticker: str, start: date, end: date
    ) -> PriceHistory | None:
        stmt = (
            select(price_cache.c.date, price_cache.c.close, price_cache.c.volume)
            .where(price_cache.c.ticker == ticker)
            .where(price_cache.c.date >= start)
            .where(price_cache.c.date <= end)
            .order_by(price_cache.c.date)
        )
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        if not rows:
            return None
        return PriceHistory(
            ticker=ticker,
            dates=[row.date for row in rows],
            close_prices=[row.close for row in rows],
            volumes=[row.volume for row in rows],
        )

    def _save_to_cache(self, ph: PriceHistory) -> None:
        if not ph.dates:
            return
        rows = [
            {
                "ticker": ph.ticker,
                "date": d,
                "close": p,
                "volume": v,
            }
            for d, p, v in zip(ph.dates, ph.close_prices, ph.volumes, strict=True)
        ]
        with self._engine.begin() as conn:
            for row in rows:
                conn.execute(
                    price_cache.insert().prefix_with("OR IGNORE"), row
                )
