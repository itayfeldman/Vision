from datetime import date, timedelta

import numpy as np
from fastapi.testclient import TestClient

from tests.api.conftest import create_test_app
from vision.api.routers.portfolios import get_portfolio_service
from vision.api.routers.risk import get_risk_service
from vision.application.market_data_service import MarketDataAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.application.risk_service import RiskAppService
from vision.domain.market_data.models import PriceHistory
from vision.infrastructure.database.repositories import SQLitePortfolioRepository


def _create_test_client() -> TestClient:
    app, engine, mock_market_repo = create_test_app()

    prices = [100.0 + i * 0.5 for i in range(252)]
    base = date(2023, 1, 2)
    dates = [base + timedelta(days=i) for i in range(252)]
    mock_market_repo.get_price_history.return_value = PriceHistory(
        ticker="AAPL",
        dates=dates,
        close_prices=prices,
        volumes=[1000000] * 252,
    )

    market_data_service = MarketDataAppService(repo=mock_market_repo, engine=engine)
    portfolio_repo = SQLitePortfolioRepository(engine)
    portfolio_service = PortfolioAppService(
        portfolio_repo=portfolio_repo,
        market_data_repo=mock_market_repo,
    )
    risk_service = RiskAppService(
        portfolio_service=portfolio_service,
        market_data_service=market_data_service,
    )

    app.dependency_overrides[get_portfolio_service] = lambda: portfolio_service
    app.dependency_overrides[get_risk_service] = lambda: risk_service

    return TestClient(app)


def test_get_risk_report_for_portfolio() -> None:
    client = _create_test_client()

    create_resp = client.post(
        "/api/portfolios",
        json={
            "name": "Test",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.6},
                {"ticker": "GOOGL", "weight": 0.4},
            ],
        },
    )
    portfolio_id = create_resp.json()["id"]

    response = client.get(f"/api/risk/{portfolio_id}")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "correlation" in data
    metrics = data["metrics"]
    assert "annualized_return" in metrics
    assert "sharpe_ratio" in metrics
    assert "var_95" in metrics
    assert "max_drawdown" in metrics


def test_get_risk_report_not_found() -> None:
    client = _create_test_client()
    response = client.get("/api/risk/nonexistent")
    assert response.status_code == 404


def test_analyze_adhoc() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/risk/analyze",
        json={
            "holdings": [
                {"ticker": "AAPL", "weight": 0.5},
                {"ticker": "GOOGL", "weight": 0.5},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["annualized_volatility"] > 0


def _create_benchmark_test_client() -> TestClient:
    app, engine, mock_market_repo = create_test_app()

    n = 252
    base = date(2023, 1, 2)
    dates = [base + timedelta(days=i) for i in range(n)]
    rng = np.random.default_rng(42)

    def make_prices(ticker: str, start: date, end: date) -> PriceHistory:
        rets = rng.normal(0.0005, 0.01, n)
        prices = list(100.0 * np.cumprod(1 + rets))
        return PriceHistory(
            ticker=ticker,
            dates=dates,
            close_prices=prices,
            volumes=[1000000] * n,
        )

    mock_market_repo.get_price_history.side_effect = make_prices

    market_data_service = MarketDataAppService(repo=mock_market_repo, engine=engine)
    portfolio_repo = SQLitePortfolioRepository(engine)
    portfolio_service = PortfolioAppService(
        portfolio_repo=portfolio_repo,
        market_data_repo=mock_market_repo,
    )
    risk_service = RiskAppService(
        portfolio_service=portfolio_service,
        market_data_service=market_data_service,
    )

    app.dependency_overrides[get_portfolio_service] = lambda: portfolio_service
    app.dependency_overrides[get_risk_service] = lambda: risk_service
    return TestClient(app)


def test_benchmark_comparison_returns_all_metrics() -> None:
    client = _create_benchmark_test_client()
    create_resp = client.post(
        "/api/portfolios",
        json={
            "name": "Test",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.6},
                {"ticker": "GOOGL", "weight": 0.4},
            ],
        },
    )
    portfolio_id = create_resp.json()["id"]

    response = client.get(f"/api/portfolios/{portfolio_id}/benchmark?ticker=SPY")
    assert response.status_code == 200
    data = response.json()
    assert data["benchmark_ticker"] == "SPY"
    assert "beta" in data
    assert "alpha" in data
    assert "tracking_error" in data
    assert "up_capture" in data
    assert "down_capture" in data
    assert len(data["spread_series"]) > 0
    first = data["spread_series"][0]
    assert "date" in first
    assert "portfolio_cum" in first
    assert "benchmark_cum" in first
    assert "spread" in first


def test_benchmark_comparison_not_found() -> None:
    client = _create_benchmark_test_client()
    response = client.get("/api/portfolios/nonexistent/benchmark")
    assert response.status_code == 404


def test_benchmark_comparison_default_ticker_is_spy() -> None:
    client = _create_benchmark_test_client()
    create_resp = client.post(
        "/api/portfolios",
        json={"name": "Test", "holdings": [{"ticker": "AAPL", "weight": 1.0}]},
    )
    portfolio_id = create_resp.json()["id"]
    response = client.get(f"/api/portfolios/{portfolio_id}/benchmark")
    assert response.status_code == 200
    assert response.json()["benchmark_ticker"] == "SPY"


def test_risk_with_lookback_param() -> None:
    client = _create_test_client()

    create_resp = client.post(
        "/api/portfolios",
        json={"name": "Test", "holdings": [{"ticker": "AAPL", "weight": 1.0}]},
    )
    portfolio_id = create_resp.json()["id"]

    response = client.get(f"/api/risk/{portfolio_id}?lookback_years=1")
    assert response.status_code == 200
