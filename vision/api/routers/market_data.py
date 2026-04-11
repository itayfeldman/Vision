from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from vision.application.market_data_service import MarketDataAppService

router = APIRouter(prefix="/api/market-data", tags=["Market Data"])

_default_start = Query(default_factory=lambda: date.today() - timedelta(days=365))
_default_end = Query(default_factory=date.today)


class PriceResponse(BaseModel):
    ticker: str
    dates: list[date]
    close_prices: list[float]
    volumes: list[int]


def get_market_data_service() -> MarketDataAppService:
    raise NotImplementedError("Must be overridden via dependency_overrides")


@router.get("/{ticker}/prices", response_model=PriceResponse)
def get_prices(
    ticker: str,
    start: date = _default_start,
    end: date = _default_end,
    service: MarketDataAppService = Depends(get_market_data_service),  # noqa: B008
) -> PriceResponse:
    ph = service.get_price_history(ticker, start, end)
    if not ph.dates:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker}")
    return PriceResponse(
        ticker=ph.ticker,
        dates=ph.dates,
        close_prices=ph.close_prices,
        volumes=ph.volumes,
    )
