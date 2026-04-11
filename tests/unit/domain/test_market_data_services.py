from datetime import date

from vision.domain.market_data.models import PriceHistory
from vision.domain.market_data.services import MarketDataService


def test_compute_daily_returns() -> None:
    ph = PriceHistory(
        ticker="AAPL",
        dates=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
        close_prices=[100.0, 110.0, 105.0],
        volumes=[1000000, 1100000, 900000],
    )
    returns = MarketDataService.compute_daily_returns(ph)
    assert len(returns) == 2
    assert returns[0] == (date(2024, 1, 3), (110.0 - 100.0) / 100.0)
    assert returns[1] == (date(2024, 1, 4), (105.0 - 110.0) / 110.0)


def test_compute_daily_returns_single_price() -> None:
    ph = PriceHistory(
        ticker="AAPL",
        dates=[date(2024, 1, 2)],
        close_prices=[100.0],
        volumes=[1000000],
    )
    returns = MarketDataService.compute_daily_returns(ph)
    assert returns == []


def test_compute_daily_returns_empty() -> None:
    ph = PriceHistory(
        ticker="AAPL",
        dates=[],
        close_prices=[],
        volumes=[],
    )
    returns = MarketDataService.compute_daily_returns(ph)
    assert returns == []
