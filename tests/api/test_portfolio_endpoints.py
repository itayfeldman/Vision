from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.api.conftest import create_test_app
from vision.api.routers.portfolios import get_portfolio_service
from vision.application.portfolio_service import PortfolioAppService
from vision.domain.market_data.models import PriceHistory
from vision.infrastructure.database.repositories import SQLitePortfolioRepository


def _create_test_client(with_prices: bool = False) -> TestClient:
    app, engine, mock_market_repo = create_test_app()

    if with_prices:
        def make_prices(
            ticker: str, start: date, end: date
        ) -> PriceHistory:
            n_days = 10
            base = date(2023, 1, 2)
            dates = [base + timedelta(days=i) for i in range(n_days)]
            prices = [150.0] * n_days if ticker == "AAPL" else [100.0] * n_days
            return PriceHistory(
                ticker=ticker,
                dates=dates,
                close_prices=prices,
                volumes=[1000000] * n_days,
            )

        mock_market_repo.get_price_history.side_effect = make_prices

    portfolio_repo = SQLitePortfolioRepository(engine)
    service = PortfolioAppService(
        portfolio_repo=portfolio_repo,
        market_data_repo=mock_market_repo,
    )
    app.dependency_overrides[get_portfolio_service] = lambda: service
    return TestClient(app)


def test_create_portfolio() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/portfolios",
        json={
            "name": "My Portfolio",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.6},
                {"ticker": "GOOGL", "weight": 0.4},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Portfolio"
    assert len(data["holdings"]) == 2
    assert "id" in data


def test_create_portfolio_invalid_weights() -> None:
    client = _create_test_client()
    response = client.post(
        "/api/portfolios",
        json={
            "name": "Bad Portfolio",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.5},
                {"ticker": "GOOGL", "weight": 0.3},
            ],
        },
    )
    assert response.status_code == 422


def test_get_portfolio() -> None:
    client = _create_test_client()
    create_resp = client.post(
        "/api/portfolios",
        json={
            "name": "Test",
            "holdings": [{"ticker": "AAPL", "weight": 1.0}],
        },
    )
    portfolio_id = create_resp.json()["id"]

    response = client.get(f"/api/portfolios/{portfolio_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_get_portfolio_not_found() -> None:
    client = _create_test_client()
    response = client.get("/api/portfolios/nonexistent")
    assert response.status_code == 404


def test_list_portfolios() -> None:
    client = _create_test_client()
    client.post(
        "/api/portfolios",
        json={"name": "A", "holdings": [{"ticker": "AAPL", "weight": 1.0}]},
    )
    client.post(
        "/api/portfolios",
        json={"name": "B", "holdings": [{"ticker": "GOOGL", "weight": 1.0}]},
    )
    response = client.get("/api/portfolios")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_portfolio() -> None:
    client = _create_test_client()
    create_resp = client.post(
        "/api/portfolios",
        json={"name": "Old", "holdings": [{"ticker": "AAPL", "weight": 1.0}]},
    )
    portfolio_id = create_resp.json()["id"]

    response = client.put(
        f"/api/portfolios/{portfolio_id}",
        json={
            "name": "Updated",
            "holdings": [
                {"ticker": "MSFT", "weight": 0.5},
                {"ticker": "GOOGL", "weight": 0.5},
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    assert len(response.json()["holdings"]) == 2


def test_delete_portfolio() -> None:
    client = _create_test_client()
    create_resp = client.post(
        "/api/portfolios",
        json={"name": "ToDelete", "holdings": [{"ticker": "AAPL", "weight": 1.0}]},
    )
    portfolio_id = create_resp.json()["id"]

    response = client.delete(f"/api/portfolios/{portfolio_id}")
    assert response.status_code == 204

    response = client.get(f"/api/portfolios/{portfolio_id}")
    assert response.status_code == 404


def test_get_portfolio_valued() -> None:
    client = _create_test_client(with_prices=True)
    create_resp = client.post(
        "/api/portfolios",
        json={
            "name": "Valued",
            "holdings": [
                {"ticker": "AAPL", "weight": 0.6},
                {"ticker": "GOOGL", "weight": 0.4},
            ],
        },
    )
    portfolio_id = create_resp.json()["id"]

    response = client.get(f"/api/portfolios/{portfolio_id}?valued=true")
    assert response.status_code == 200
    data = response.json()

    assert "total_value" in data
    assert data["total_value"] > 0
    for h in data["holdings"]:
        assert "current_price" in h
        assert "shares" in h
        assert "market_value" in h


def test_get_portfolio_valued_not_found() -> None:
    client = _create_test_client(with_prices=True)
    response = client.get("/api/portfolios/nonexistent?valued=true")
    assert response.status_code == 404
