"""Shared test helpers for API tests."""

from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

import numpy as np
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from vision.api.app import create_app
from vision.domain.market_data.models import PriceHistory
from vision.infrastructure.database.connection import init_db


def create_test_app() -> tuple[FastAPI, Engine, MagicMock]:
    """Create a FastAPI app with an in-memory SQLite DB and a mock market repo.

    Returns (app, engine, mock_market_repo).
    The mock repo has validate_ticker returning True by default.
    """
    app = create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    mock_market_repo: Any = MagicMock()
    mock_market_repo.validate_ticker.return_value = True
    return app, engine, mock_market_repo


def make_random_prices(
    rng: np.random.Generator, n_days: int = 252
) -> Any:
    """Return a make_prices side_effect function using the given RNG."""

    def make_prices(
        ticker: str, start: date, end: date
    ) -> PriceHistory:
        base = date(2023, 1, 2)
        dates = [base + timedelta(days=i) for i in range(n_days)]
        prices = list(np.cumsum(rng.normal(0.5, 1.0, n_days)) + 100)
        return PriceHistory(
            ticker=ticker,
            dates=dates,
            close_prices=prices,
            volumes=[1000000] * n_days,
        )

    return make_prices
