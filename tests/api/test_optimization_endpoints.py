import numpy as np
from fastapi.testclient import TestClient

from tests.api.conftest import create_test_app, make_random_prices
from vision.api.routers.optimization import get_optimization_service
from vision.application.market_data_service import MarketDataAppService
from vision.application.optimization_service import OptimizationAppService
from vision.domain.optimization.services import OptimizationService
from vision.infrastructure.optimization.riskfolio_adapter import RiskfolioOptimizer


def _create_test_client() -> TestClient:
    app, engine, mock_market_repo = create_test_app()

    rng = np.random.default_rng(42)
    mock_market_repo.get_price_history.side_effect = make_random_prices(rng)

    market_data_service = MarketDataAppService(
        repo=mock_market_repo, engine=engine
    )
    opt_app_service = OptimizationAppService(
        optimization_service=OptimizationService(RiskfolioOptimizer()),
        market_data_service=market_data_service,
    )

    app.dependency_overrides[get_optimization_service] = lambda: opt_app_service
    return TestClient(app)


def test_optimize_max_sharpe() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize",
        json={
            "tickers": ["AAPL", "GOOGL", "MSFT"],
            "objective": "max_sharpe",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "weights" in data
    assert abs(sum(data["weights"].values()) - 1.0) < 1e-6
    assert "expected_return" in data
    assert "sharpe_ratio" in data


def test_optimize_invalid_objective() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize",
        json={"tickers": ["AAPL", "GOOGL"], "objective": "invalid"},
    )
    assert response.status_code == 422


def test_optimize_too_few_tickers() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize",
        json={"tickers": ["AAPL"], "objective": "max_sharpe"},
    )
    assert response.status_code == 422


def test_frontier_returns_points_and_named_portfolios() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize/frontier",
        json={
            "tickers": ["AAPL", "GOOGL", "MSFT"],
            "points": 10,
            "lookback_years": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) >= 2
    for p in data["points"]:
        assert "expected_return" in p
        assert "expected_volatility" in p
        assert "sharpe_ratio" in p
        assert abs(sum(p["weights"].values()) - 1.0) < 1e-3
    assert "min_volatility" in data
    assert "max_sharpe" in data
    assert "equal_weight" in data
    eq = data["equal_weight"]
    for w in eq["weights"].values():
        assert abs(w - 1.0 / 3) < 1e-9


def test_frontier_rejects_points_out_of_range() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize/frontier",
        json={"tickers": ["AAPL", "GOOGL"], "points": 1},
    )
    assert response.status_code == 422

    response = client.post(
        "/api/optimize/frontier",
        json={"tickers": ["AAPL", "GOOGL"], "points": 500},
    )
    assert response.status_code == 422


def test_frontier_rejects_single_ticker() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/optimize/frontier",
        json={"tickers": ["AAPL"], "points": 10},
    )
    assert response.status_code == 422
