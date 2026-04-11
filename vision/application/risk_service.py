from datetime import date, timedelta

import numpy as np
from numpy.typing import NDArray

from vision.application.market_data_service import MarketDataAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.domain.portfolio.models import Holding
from vision.domain.risk.models import CorrelationMatrix, RiskMetrics
from vision.domain.risk.services import RiskCalculationService


class RiskAppService:
    def __init__(
        self,
        portfolio_service: PortfolioAppService,
        market_data_service: MarketDataAppService,
    ) -> None:
        self._portfolio_service = portfolio_service
        self._market_data_service = market_data_service

    def analyze_portfolio(
        self, portfolio_id: str, lookback_years: int = 3
    ) -> tuple[RiskMetrics, CorrelationMatrix]:
        portfolio = self._portfolio_service.get_portfolio(portfolio_id)
        return self._analyze_holdings(portfolio.holdings, lookback_years)

    def analyze_adhoc(
        self, holdings: list[Holding], lookback_years: int = 3
    ) -> tuple[RiskMetrics, CorrelationMatrix]:
        return self._analyze_holdings(holdings, lookback_years)

    def _analyze_holdings(
        self, holdings: list[Holding], lookback_years: int
    ) -> tuple[RiskMetrics, CorrelationMatrix]:
        end = date.today()
        start = end - timedelta(days=lookback_years * 365)

        ticker_returns: dict[str, NDArray[np.floating]] = {}
        for h in holdings:
            daily = self._market_data_service.get_daily_returns(h.ticker, start, end)
            if daily:
                ticker_returns[h.ticker] = np.array([r for _, r in daily])

        if not ticker_returns:
            empty_metrics = RiskMetrics(
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
                var_95=0.0,
                var_99=0.0,
                cvar_95=0.0,
                cvar_99=0.0,
            )
            return empty_metrics, CorrelationMatrix(tickers=[], matrix=[])

        # Compute portfolio-weighted returns
        # Align all series to the shortest length
        min_len = min(len(r) for r in ticker_returns.values())
        portfolio_returns = np.zeros(min_len)
        for h in holdings:
            if h.ticker in ticker_returns:
                portfolio_returns += h.weight * ticker_returns[h.ticker][:min_len]

        metrics = RiskCalculationService.compute_risk_metrics(portfolio_returns)

        # Trim all series for correlation
        trimmed = {t: r[:min_len] for t, r in ticker_returns.items()}
        correlation = RiskCalculationService.compute_correlation_matrix(trimmed)

        return metrics, correlation
