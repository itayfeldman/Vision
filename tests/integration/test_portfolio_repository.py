from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from vision.domain.portfolio.models import Holding, Portfolio
from vision.infrastructure.database.connection import init_db
from vision.infrastructure.database.repositories import SQLitePortfolioRepository


def _make_engine():  # type: ignore[no-untyped-def]
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    return engine


def test_save_and_get_portfolio() -> None:
    engine = _make_engine()
    repo = SQLitePortfolioRepository(engine)
    portfolio = Portfolio(
        id="p1",
        name="Test",
        holdings=[
            Holding(ticker="AAPL", weight=0.6),
            Holding(ticker="GOOGL", weight=0.4),
        ],
    )
    repo.save(portfolio)
    result = repo.get_by_id("p1")
    assert result is not None
    assert result.id == "p1"
    assert result.name == "Test"
    assert len(result.holdings) == 2


def test_get_nonexistent_returns_none() -> None:
    engine = _make_engine()
    repo = SQLitePortfolioRepository(engine)
    assert repo.get_by_id("nonexistent") is None


def test_list_all() -> None:
    engine = _make_engine()
    repo = SQLitePortfolioRepository(engine)
    repo.save(
        Portfolio(id="p1", name="A", holdings=[Holding(ticker="AAPL", weight=1.0)])
    )
    repo.save(
        Portfolio(id="p2", name="B", holdings=[Holding(ticker="GOOGL", weight=1.0)])
    )
    results = repo.list_all()
    assert len(results) == 2


def test_update_portfolio() -> None:
    engine = _make_engine()
    repo = SQLitePortfolioRepository(engine)
    repo.save(
        Portfolio(id="p1", name="Old", holdings=[Holding(ticker="AAPL", weight=1.0)])
    )
    repo.save(
        Portfolio(
            id="p1",
            name="New",
            holdings=[
                Holding(ticker="GOOGL", weight=0.5),
                Holding(ticker="MSFT", weight=0.5),
            ],
        )
    )
    result = repo.get_by_id("p1")
    assert result is not None
    assert result.name == "New"
    assert len(result.holdings) == 2
    tickers = {h.ticker for h in result.holdings}
    assert tickers == {"GOOGL", "MSFT"}


def test_delete_portfolio() -> None:
    engine = _make_engine()
    repo = SQLitePortfolioRepository(engine)
    repo.save(
        Portfolio(id="p1", name="Test", holdings=[Holding(ticker="AAPL", weight=1.0)])
    )
    assert repo.delete("p1") is True
    assert repo.get_by_id("p1") is None


def test_delete_nonexistent_returns_false() -> None:
    engine = _make_engine()
    repo = SQLitePortfolioRepository(engine)
    assert repo.delete("nonexistent") is False
