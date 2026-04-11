"""End-to-end integration test: create portfolio → risk → factors → summary."""

import numpy as np
from fastapi.testclient import TestClient

from tests.api.conftest import create_test_app, make_random_prices
from vision.api.routers.factors import get_factor_service
from vision.api.routers.optimization import get_optimization_service
from vision.api.routers.portfolios import get_portfolio_service
from vision.api.routers.risk import get_risk_service
from vision.application.factor_service import FactorAppService
from vision.application.market_data_service import MarketDataAppService
from vision.application.optimization_service import OptimizationAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.application.risk_service import RiskAppService
from vision.domain.optimization.services import OptimizationService
from vision.infrastructure.database.repositories import SQLitePortfolioRepository
from vision.infrastructure.market_data.factor_data_adapter import FactorDataAdapter
from vision.infrastructure.optimization.riskfolio_adapter import RiskfolioOptimizer


def _create_integrated_client() -> TestClient:
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
    risk_service = RiskAppService(
        portfolio_service=portfolio_service,
        market_data_service=market_data_service,
    )
    optimization_service = OptimizationAppService(
        optimization_service=OptimizationService(
            optimizer=RiskfolioOptimizer()
        ),
        market_data_service=market_data_service,
    )
    factor_service = FactorAppService(
        portfolio_service=portfolio_service,
        market_data_service=market_data_service,
        factor_data_adapter=FactorDataAdapter(),
    )

    app.dependency_overrides[get_portfolio_service] = lambda: portfolio_service
    app.dependency_overrides[get_risk_service] = lambda: risk_service
    app.dependency_overrides[get_optimization_service] = lambda: optimization_service
    app.dependency_overrides[get_factor_service] = lambda: factor_service
    return TestClient(app)


def test_full_integration_flow() -> None:
    """Create portfolio → get risk → get factors → get summary."""
    client = _create_integrated_client()

    # 1. Create portfolio
    create_resp = client.post(
        "/api/portfolios",
        json={
            "name": "Integration Test",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.4},
                {"ticker": "GOOGL", "weight": 0.3},
                {"ticker": "MSFT", "weight": 0.3},
            ],
        },
    )
    assert create_resp.status_code == 201
    portfolio_id = create_resp.json()["id"]

    # 2. Get risk report
    risk_resp = client.get(f"/api/risk/{portfolio_id}")
    assert risk_resp.status_code == 200
    risk_data = risk_resp.json()
    assert "metrics" in risk_data
    assert "correlation" in risk_data
    assert risk_data["metrics"]["annualized_volatility"] > 0

    # 3. Get factor decomposition
    factor_resp = client.get(f"/api/factors/{portfolio_id}")
    assert factor_resp.status_code == 200
    factor_data = factor_resp.json()
    assert len(factor_data["exposures"]) == 5
    assert 0.0 <= factor_data["r_squared"] <= 1.0

    # 4. Get portfolio summary (combines all contexts)
    summary_resp = client.get(f"/api/portfolios/{portfolio_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()

    assert summary["id"] == portfolio_id
    assert summary["name"] == "Integration Test"
    assert len(summary["holdings"]) == 3
    assert "risk" in summary
    assert summary["risk"]["annualized_volatility"] > 0
    assert "factor_exposures" in summary
    assert len(summary["factor_exposures"]) == 5


def test_optimize_then_summary() -> None:
    """Optimize portfolio → create from results → summary."""
    client = _create_integrated_client()

    # 1. Optimize
    opt_resp = client.post(
        "/api/optimize",
        json={
            "tickers": ["AAPL", "GOOGL", "MSFT"],
            "objective": "min_volatility",
        },
    )
    assert opt_resp.status_code == 200
    weights = opt_resp.json()["weights"]
    assert abs(sum(weights.values()) - 1.0) < 1e-4

    # 2. Create portfolio from optimal weights
    holdings = [
        {"ticker": t, "weight": round(w, 6)}
        for t, w in weights.items()
    ]
    # Normalize to ensure sum = 1.0 after rounding
    total = sum(h["weight"] for h in holdings)
    holdings[-1]["weight"] += 1.0 - total

    create_resp = client.post(
        "/api/portfolios",
        json={"name": "Optimized", "holdings": holdings},
    )
    assert create_resp.status_code == 201
    portfolio_id = create_resp.json()["id"]

    # 3. Get summary
    summary_resp = client.get(f"/api/portfolios/{portfolio_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["name"] == "Optimized"
    assert "risk" in summary
    assert "factor_exposures" in summary
