from datetime import date, timedelta

import numpy as np

from vision.application.market_data_service import MarketDataAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.domain.factor.models import FactorDecomposition
from vision.domain.factor.services import FactorRegressionService
from vision.infrastructure.market_data.factor_data_adapter import (
    FactorDataAdapter,
)


class FactorAppService:
    def __init__(
        self,
        portfolio_service: PortfolioAppService,
        market_data_service: MarketDataAppService,
        factor_data_adapter: FactorDataAdapter,
    ) -> None:
        self._portfolio_service = portfolio_service
        self._market_data_service = market_data_service
        self._factor_adapter = factor_data_adapter

    def analyze_portfolio(
        self, portfolio_id: str, lookback_years: int = 3
    ) -> FactorDecomposition:
        portfolio = self._portfolio_service.get_portfolio(portfolio_id)
        end = date.today()
        start = end - timedelta(days=lookback_years * 365)

        # Get portfolio weighted returns
        all_returns: dict[str, list[float]] = {}
        for h in portfolio.holdings:
            daily = self._market_data_service.get_daily_returns(
                h.ticker, start, end
            )
            if daily:
                all_returns[h.ticker] = [r for _, r in daily]

        if not all_returns:
            raise ValueError("No return data available")

        # Align and compute weighted returns
        min_len = min(len(v) for v in all_returns.values())
        portfolio_returns = np.zeros(min_len)
        for h in portfolio.holdings:
            if h.ticker in all_returns:
                r = np.array(all_returns[h.ticker][:min_len])
                portfolio_returns += h.weight * r

        # Get factor data
        _, factor_array, factor_names = (
            self._factor_adapter.get_factor_returns(start, end)
        )

        # Align lengths
        n = min(len(portfolio_returns), len(factor_array))
        portfolio_returns = portfolio_returns[:n]
        factor_array = factor_array[:n]

        return FactorRegressionService.regress(
            portfolio_returns, factor_array, factor_names
        )
