from datetime import date

from sqlalchemy import create_engine, select

from vision.infrastructure.database.connection import metadata
from vision.infrastructure.database.models import price_cache


def test_price_cache_insert_and_query() -> None:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(
            price_cache.insert(),
            {
                "ticker": "AAPL",
                "date": date(2024, 1, 2),
                "close": 150.0,
                "volume": 1000000,
            },
        )

    with engine.connect() as conn:
        rows = conn.execute(
            select(price_cache).where(price_cache.c.ticker == "AAPL")
        ).fetchall()

    assert len(rows) == 1
    assert rows[0].ticker == "AAPL"
    assert rows[0].close == 150.0


def test_price_cache_unique_constraint() -> None:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)

    row = {
        "ticker": "AAPL",
        "date": date(2024, 1, 2),
        "close": 150.0,
        "volume": 1000000,
    }
    with engine.begin() as conn:
        conn.execute(price_cache.insert(), row)
        conn.execute(price_cache.insert().prefix_with("OR IGNORE"), row)

    with engine.connect() as conn:
        count = conn.execute(
            select(price_cache).where(price_cache.c.ticker == "AAPL")
        ).fetchall()

    assert len(count) == 1
