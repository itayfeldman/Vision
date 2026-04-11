"""Dependency injection container for FastAPI."""

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from vision.api.routers.factors import get_factor_service
from vision.api.routers.market_data import get_market_data_service
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
from vision.infrastructure.market_data.yfinance_adapter import (
    YFinanceMarketDataRepository,
)
from vision.infrastructure.optimization.riskfolio_adapter import RiskfolioOptimizer


def wire_dependencies(app: FastAPI, engine: Engine) -> None:
    """Wire all application services into FastAPI's DI system."""
    market_data_repo = YFinanceMarketDataRepository()
    portfolio_repo = SQLitePortfolioRepository(engine)

    market_data_service = MarketDataAppService(
        repo=market_data_repo, engine=engine
    )
    portfolio_service = PortfolioAppService(
        portfolio_repo=portfolio_repo,
        market_data_repo=market_data_repo,
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

    app.dependency_overrides[get_market_data_service] = lambda: market_data_service
    app.dependency_overrides[get_portfolio_service] = lambda: portfolio_service
    app.dependency_overrides[get_risk_service] = lambda: risk_service
    app.dependency_overrides[get_optimization_service] = lambda: optimization_service
    app.dependency_overrides[get_factor_service] = lambda: factor_service
