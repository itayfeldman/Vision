from datetime import date
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from vision.api.app import create_app
from vision.api.routers.market_data import get_market_data_service
from vision.application.market_data_service import MarketDataAppService
from vision.domain.market_data.models import PriceHistory
from vision.infrastructure.database.connection import init_db


def _create_test_app() -> TestClient:
    app = create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    mock_repo = MagicMock()
    mock_repo.get_price_history.return_value = PriceHistory(
        ticker="AAPL",
        dates=[date(2024, 1, 2), date(2024, 1, 3)],
        close_prices=[150.0, 152.0],
        volumes=[1000000, 1100000],
    )
    mock_repo.validate_ticker.return_value = True

    service = MarketDataAppService(repo=mock_repo, engine=engine)
    app.dependency_overrides[get_market_data_service] = lambda: service

    return TestClient(app)


def test_get_prices_returns_data() -> None:
    client = _create_test_app()
    response = client.get(
        "/api/market-data/AAPL/prices?start=2024-01-01&end=2024-01-31"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert len(data["dates"]) == 2
    assert data["close_prices"] == [150.0, 152.0]


def test_get_prices_no_data_returns_404() -> None:
    app = create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    mock_repo = MagicMock()
    mock_repo.get_price_history.return_value = PriceHistory(
        ticker="INVALID", dates=[], close_prices=[], volumes=[]
    )

    service = MarketDataAppService(repo=mock_repo, engine=engine)
    app.dependency_overrides[get_market_data_service] = lambda: service

    client = TestClient(app)
    response = client.get(
        "/api/market-data/INVALID/prices?start=2024-01-01&end=2024-01-31"
    )
    assert response.status_code == 404


def test_cache_prevents_second_fetch() -> None:
    app = create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    mock_repo = MagicMock()
    mock_repo.get_price_history.return_value = PriceHistory(
        ticker="AAPL",
        dates=[date(2024, 1, 2)],
        close_prices=[150.0],
        volumes=[1000000],
    )

    service = MarketDataAppService(repo=mock_repo, engine=engine)
    app.dependency_overrides[get_market_data_service] = lambda: service

    client = TestClient(app)

    # First call — hits yfinance
    client.get("/api/market-data/AAPL/prices?start=2024-01-02&end=2024-01-02")
    assert mock_repo.get_price_history.call_count == 1

    # Second call — should use cache
    client.get("/api/market-data/AAPL/prices?start=2024-01-02&end=2024-01-02")
    assert mock_repo.get_price_history.call_count == 1
