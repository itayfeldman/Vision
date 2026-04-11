import numpy as np
from fastapi.testclient import TestClient

from tests.api.conftest import create_test_app, make_random_prices
from vision.api.routers.factors import get_factor_service
from vision.api.routers.portfolios import get_portfolio_service
from vision.application.factor_service import FactorAppService
from vision.application.market_data_service import MarketDataAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.infrastructure.database.repositories import SQLitePortfolioRepository
from vision.infrastructure.market_data.factor_data_adapter import FactorDataAdapter


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
    factor_service = FactorAppService(
        portfolio_service=portfolio_service,
        market_data_service=market_data_service,
        factor_data_adapter=FactorDataAdapter(),
    )

    app.dependency_overrides[get_portfolio_service] = (
        lambda: portfolio_service
    )
    app.dependency_overrides[get_factor_service] = (
        lambda: factor_service
    )
    return TestClient(app)


def test_get_factor_decomposition() -> None:
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

    response = client.get(f"/api/factors/{portfolio_id}")
    assert response.status_code == 200
    data = response.json()

    assert len(data["exposures"]) == 5
    factor_names = [e["factor_name"] for e in data["exposures"]]
    assert "Mkt-RF" in factor_names
    assert "SMB" in factor_names
    assert "HML" in factor_names
    assert "RMW" in factor_names
    assert "CMA" in factor_names

    assert 0.0 <= data["r_squared"] <= 1.0
    assert "alpha" in data
    assert "residual_risk" in data


def test_factor_not_found() -> None:
    client = _create_test_client()
    response = client.get("/api/factors/nonexistent")
    assert response.status_code == 404
