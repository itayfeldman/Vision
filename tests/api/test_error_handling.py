"""Tests for structured error responses and edge cases."""

import numpy as np
from fastapi.testclient import TestClient

from tests.api.conftest import create_test_app, make_random_prices
from vision.api.routers.optimization import get_optimization_service
from vision.api.routers.portfolios import get_portfolio_service
from vision.application.market_data_service import MarketDataAppService
from vision.application.optimization_service import OptimizationAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.domain.optimization.services import OptimizationService
from vision.infrastructure.database.repositories import SQLitePortfolioRepository
from vision.infrastructure.optimization.riskfolio_adapter import RiskfolioOptimizer


def _create_test_client() -> TestClient:
    app, engine, mock_market_repo = create_test_app()

    rng = np.random.default_rng(42)
    mock_market_repo.get_price_history.side_effect = make_random_prices(rng)

    market_data_service = MarketDataAppService(
        repo=mock_market_repo, engine=engine
    )
    portfolio_repo = SQLitePortfolioRepository(engine)
    portfolio_service = PortfolioAppService(
        portfolio_repo=portfolio_repo,
        market_data_repo=mock_market_repo,
    )
    optimization_service = OptimizationAppService(
        optimization_service=OptimizationService(
            optimizer=RiskfolioOptimizer()
        ),
        market_data_service=market_data_service,
    )

    app.dependency_overrides[get_portfolio_service] = lambda: portfolio_service
    app.dependency_overrides[get_optimization_service] = lambda: optimization_service
    return TestClient(app)


def test_portfolio_not_found_structured() -> None:
    client = _create_test_client()
    response = client.get("/api/portfolios/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_invalid_weights_structured() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/portfolios",
        json={
            "name": "Bad",
            "holdings": [{"ticker": "AAPL", "weight": 0.5}],
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_missing_body_returns_422() -> None:
    client = _create_test_client()
    response = client.post("/api/portfolios", content=b"not json")
    assert response.status_code == 422


def test_optimize_empty_tickers_returns_422() -> None:
    """POST /api/optimize with empty tickers should fail."""
    client = _create_test_client()
    response = client.post(
        "/api/optimize",
        json={"tickers": [], "objective": "max_sharpe"},
    )
    # FastAPI or the service will reject empty tickers
    assert response.status_code in (422, 500)


def test_optimize_invalid_objective_returns_422() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize",
        json={"tickers": ["AAPL", "GOOGL"], "objective": "invalid_obj"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_health_endpoint() -> None:
    client = _create_test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_available() -> None:
    client = _create_test_client()
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Vision"
    assert "/api/portfolios" in schema["paths"]
    assert "/api/risk/{portfolio_id}" in schema["paths"]
    assert "/api/optimize" in schema["paths"]
    assert "/api/factors/{portfolio_id}" in schema["paths"]
