"""SQLAlchemy Core table definitions."""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)

from vision.infrastructure.database.connection import metadata

price_cache = Table(
    "price_cache",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticker", String, nullable=False),
    Column("date", Date, nullable=False),
    Column("close", Float, nullable=False),
    Column("volume", Integer, nullable=False),
    UniqueConstraint("ticker", "date", name="uq_ticker_date"),
)

portfolios = Table(
    "portfolios",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

holdings = Table(
    "holdings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "portfolio_id",
        String,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ticker", String, nullable=False),
    Column("weight", Float, nullable=False),
)
