"""Concrete repository implementations backed by SQLite."""

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.engine import Engine

from vision.domain.portfolio.models import Holding, Portfolio
from vision.domain.portfolio.repository import PortfolioRepository
from vision.infrastructure.database.models import holdings, portfolios


class SQLitePortfolioRepository(PortfolioRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, portfolio: Portfolio) -> None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            existing = conn.execute(
                select(portfolios).where(portfolios.c.id == portfolio.id)
            ).first()

            if existing:
                conn.execute(
                    portfolios.update()
                    .where(portfolios.c.id == portfolio.id)
                    .values(name=portfolio.name, updated_at=now)
                )
                conn.execute(
                    delete(holdings).where(
                        holdings.c.portfolio_id == portfolio.id
                    )
                )
            else:
                conn.execute(
                    portfolios.insert().values(
                        id=portfolio.id,
                        name=portfolio.name,
                        created_at=now,
                        updated_at=now,
                    )
                )

            for h in portfolio.holdings:
                conn.execute(
                    holdings.insert().values(
                        portfolio_id=portfolio.id,
                        ticker=h.ticker,
                        weight=h.weight,
                    )
                )

    def get_by_id(self, portfolio_id: str) -> Portfolio | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(portfolios).where(portfolios.c.id == portfolio_id)
            ).first()
            if not row:
                return None

            holding_rows = conn.execute(
                select(holdings).where(holdings.c.portfolio_id == portfolio_id)
            ).fetchall()

        return Portfolio(
            id=row.id,
            name=row.name,
            holdings=[
                Holding(ticker=h.ticker, weight=h.weight) for h in holding_rows
            ],
        )

    def list_all(self) -> list[Portfolio]:
        with self._engine.connect() as conn:
            portfolio_rows = conn.execute(select(portfolios)).fetchall()
            result = []
            for p in portfolio_rows:
                holding_rows = conn.execute(
                    select(holdings).where(holdings.c.portfolio_id == p.id)
                ).fetchall()
                result.append(
                    Portfolio(
                        id=p.id,
                        name=p.name,
                        holdings=[
                            Holding(ticker=h.ticker, weight=h.weight)
                            for h in holding_rows
                        ],
                    )
                )
        return result

    def delete(self, portfolio_id: str) -> bool:
        with self._engine.begin() as conn:
            conn.execute(
                delete(holdings).where(holdings.c.portfolio_id == portfolio_id)
            )
            result = conn.execute(
                delete(portfolios).where(portfolios.c.id == portfolio_id)
            )
        return result.rowcount > 0
