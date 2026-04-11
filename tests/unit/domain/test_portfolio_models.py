import pytest

from vision.domain.portfolio.models import Holding, Portfolio


def test_holding_creation() -> None:
    h = Holding(ticker="AAPL", weight=0.5)
    assert h.ticker == "AAPL"
    assert h.weight == 0.5


def test_holding_is_frozen() -> None:
    h = Holding(ticker="AAPL", weight=0.5)
    with pytest.raises(AttributeError):
        h.weight = 0.3  # type: ignore[misc]


def test_portfolio_creation() -> None:
    holdings = [
        Holding(ticker="AAPL", weight=0.6),
        Holding(ticker="GOOGL", weight=0.4),
    ]
    p = Portfolio(id="p1", name="Test Portfolio", holdings=holdings)
    assert p.id == "p1"
    assert p.name == "Test Portfolio"
    assert len(p.holdings) == 2


def test_portfolio_total_weight() -> None:
    holdings = [
        Holding(ticker="AAPL", weight=0.6),
        Holding(ticker="GOOGL", weight=0.4),
    ]
    p = Portfolio(id="p1", name="Test", holdings=holdings)
    assert abs(p.total_weight - 1.0) < 1e-9
