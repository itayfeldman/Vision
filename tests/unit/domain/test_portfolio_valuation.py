from vision.domain.portfolio.models import (
    Holding,
    Portfolio,
    ValuedHolding,
    ValuedPortfolio,
)
from vision.domain.portfolio.services import PortfolioConstructionService


def test_valued_holding_market_value() -> None:
    vh = ValuedHolding(ticker="AAPL", weight=0.5, current_price=150.0, shares=10.0)
    assert vh.market_value == 1500.0


def test_valued_portfolio_total_value() -> None:
    vp = ValuedPortfolio(
        id="p1",
        name="Test",
        holdings=[
            ValuedHolding(ticker="AAPL", weight=0.6, current_price=150.0, shares=10.0),
            ValuedHolding(ticker="GOOGL", weight=0.4, current_price=100.0, shares=5.0),
        ],
    )
    assert vp.total_value == 2000.0


def test_value_portfolio_pure_function() -> None:
    portfolio = Portfolio(
        id="p1",
        name="Test",
        holdings=[
            Holding(ticker="AAPL", weight=0.6),
            Holding(ticker="GOOGL", weight=0.4),
        ],
    )
    prices = {"AAPL": 150.0, "GOOGL": 100.0}
    total_investment = 10000.0

    result = PortfolioConstructionService.value_portfolio(
        portfolio, prices, total_investment
    )

    assert isinstance(result, ValuedPortfolio)
    assert result.id == "p1"
    assert result.name == "Test"
    assert len(result.holdings) == 2

    aapl = next(h for h in result.holdings if h.ticker == "AAPL")
    assert aapl.current_price == 150.0
    assert aapl.weight == 0.6
    # 0.6 * 10000 / 150 = 40 shares
    assert abs(aapl.shares - 40.0) < 1e-6
    assert abs(aapl.market_value - 6000.0) < 1e-6

    googl = next(h for h in result.holdings if h.ticker == "GOOGL")
    assert abs(googl.shares - 40.0) < 1e-6
    assert abs(googl.market_value - 4000.0) < 1e-6

    assert abs(result.total_value - 10000.0) < 1e-6


def test_value_portfolio_missing_price_excluded() -> None:
    portfolio = Portfolio(
        id="p1",
        name="Test",
        holdings=[
            Holding(ticker="AAPL", weight=0.6),
            Holding(ticker="INVALID", weight=0.4),
        ],
    )
    prices = {"AAPL": 150.0}  # INVALID not available
    total_investment = 10000.0

    result = PortfolioConstructionService.value_portfolio(
        portfolio, prices, total_investment
    )

    assert len(result.holdings) == 1
    assert result.holdings[0].ticker == "AAPL"
