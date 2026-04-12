from datetime import date, timedelta

import pandas as pd

from vision.application.market_data_service import MarketDataAppService
from vision.domain.optimization.models import (
    FrontierRequest,
    FrontierResult,
    OptimizationRequest,
    OptimizationResult,
)
from vision.domain.optimization.services import OptimizationService


class OptimizationAppService:
    def __init__(
        self,
        optimization_service: OptimizationService,
        market_data_service: MarketDataAppService,
    ) -> None:
        self._optimization_service = optimization_service
        self._market_data_service = market_data_service

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        end = date.today()
        start = end - timedelta(days=request.lookback_years * 365)

        series: dict[str, pd.Series] = {}
        for ticker in request.tickers:
            daily = self._market_data_service.get_daily_returns(
                ticker, start, end
            )
            if daily:
                series[ticker] = pd.Series(
                    [r for _, r in daily], index=[d for d, _ in daily]
                )

        if len(series) < 2:
            raise ValueError("Not enough data to optimize")

        returns_df = pd.DataFrame(series).dropna()
        return self._optimization_service.run_optimization(
            request, returns_df
        )

    def compute_frontier(self, request: FrontierRequest) -> FrontierResult:
        if len(request.tickers) < 2:
            raise ValueError("Need at least 2 tickers for frontier")

        end = date.today()
        start = end - timedelta(days=request.lookback_years * 365)

        series: dict[str, pd.Series] = {}
        for ticker in request.tickers:
            daily = self._market_data_service.get_daily_returns(
                ticker, start, end
            )
            if daily:
                series[ticker] = pd.Series(
                    [r for _, r in daily], index=[d for d, _ in daily]
                )

        if len(series) < 2:
            raise ValueError("Not enough data to compute frontier")

        returns_df = pd.DataFrame(series).dropna()
        return self._optimization_service.compute_frontier(
            returns_df, request.constraints, request.points
        )
