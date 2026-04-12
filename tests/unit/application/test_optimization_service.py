"""Unit tests for OptimizationAppService, focusing on data alignment."""

from datetime import date, timedelta
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from vision.application.market_data_service import MarketDataAppService
from vision.application.optimization_service import OptimizationAppService
from vision.domain.market_data.models import PriceHistory
from vision.domain.optimization.models import (
    FrontierRequest,
    OptimizationObjective,
    OptimizationRequest,
)
from vision.domain.optimization.services import OptimizationService
from vision.infrastructure.database.connection import init_db
from vision.infrastructure.optimization.riskfolio_adapter import RiskfolioOptimizer


def _make_service(side_effect: object) -> OptimizationAppService:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    mock_repo: MagicMock = MagicMock()
    mock_repo.validate_ticker.return_value = True
    mock_repo.get_price_history.side_effect = side_effect

    market_data_service = MarketDataAppService(repo=mock_repo, engine=engine)
    return OptimizationAppService(
        optimization_service=OptimizationService(RiskfolioOptimizer()),
        market_data_service=market_data_service,
    )


def _mismatched_calendar_prices(
    base: date,
) -> object:
    """
    AAPL: 200 prices (days 0-199). Days 0-99: explosive growth (~50% daily
    return), days 100-199: flat (+0.1% daily).
    NVDA: 100 prices (days 100-199): flat (+0.1% daily).

    With [:min_len] positional alignment the optimizer sees AAPL's first
    100 explosive returns alongside NVDA's 100 flat returns — completely
    different calendar windows, producing absurd expected_return.

    With date-intersection alignment both tickers contribute only returns
    for days 101-199 (99 data points each), both flat ~0.1%/day.
    Annualised expected_return should be modest (< 50%).
    """
    aapl_dates = [base + timedelta(days=i) for i in range(200)]
    nvda_dates = [base + timedelta(days=i) for i in range(100, 200)]

    # AAPL: prices double roughly every day for the first 100 days, then flat
    aapl_prices = [100.0 * (2 ** (i / 10)) for i in range(100)] + [
        1000.0 * (1.001 ** i) for i in range(100)
    ]
    # NVDA: flat throughout
    nvda_prices = [200.0 * (1.001 ** i) for i in range(100)]

    def make_prices(ticker: str, start: date, end: date) -> PriceHistory:
        if ticker == "AAPL":
            return PriceHistory(
                ticker="AAPL",
                dates=aapl_dates,
                close_prices=aapl_prices,
                volumes=[1_000_000] * 200,
            )
        return PriceHistory(
            ticker="NVDA",
            dates=nvda_dates,
            close_prices=nvda_prices,
            volumes=[500_000] * 100,
        )

    return make_prices


def test_optimize_aligns_mismatched_calendars() -> None:
    base = date(2022, 1, 3)
    svc = _make_service(_mismatched_calendar_prices(base))
    req = OptimizationRequest(
        tickers=["AAPL", "NVDA"],
        objective=OptimizationObjective.MIN_VOLATILITY,
        constraints=[],
        lookback_years=1,
    )
    result = svc.optimize(req)

    # Correct intersection: both tickers flat ~0.1%/day → annualised ~30%.
    # Wrong alignment: AAPL's ~7% daily return → annualised >>1000%.
    assert result.expected_return < 5.0, (
        f"expected_return={result.expected_return:.2f} suggests misaligned "
        "calendar windows (AAPL's explosive early period was included)"
    )


def test_frontier_aligns_mismatched_calendars() -> None:
    base = date(2022, 1, 3)
    svc = _make_service(_mismatched_calendar_prices(base))
    req = FrontierRequest(
        tickers=["AAPL", "NVDA"],
        constraints=[],
        lookback_years=1,
        points=10,
    )
    result = svc.compute_frontier(req)

    for label, fp in [
        ("min_volatility", result.min_volatility),
        ("max_sharpe", result.max_sharpe),
        ("equal_weight", result.equal_weight),
    ]:
        assert fp.expected_return < 5.0, (
            f"{label}.expected_return={fp.expected_return:.2f} suggests "
            "misaligned calendar windows"
        )
