from datetime import date, timedelta

import pandas as pd

from vision.application.market_data_service import MarketDataAppService
from vision.domain.optimization.models import (
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

        returns_data: dict[str, list[float]] = {}
        dates_data: dict[str, list[date]] = {}
        for ticker in request.tickers:
            daily = self._market_data_service.get_daily_returns(
                ticker, start, end
            )
            if daily:
                dates_data[ticker] = [d for d, _ in daily]
                returns_data[ticker] = [r for _, r in daily]

        if len(returns_data) < 2:
            raise ValueError("Not enough data to optimize")

        # Align to shortest series
        min_len = min(len(v) for v in returns_data.values())
        aligned = {
            t: returns_data[t][:min_len] for t in returns_data
        }

        returns_df = pd.DataFrame(aligned)
        return self._optimization_service.run_optimization(
            request, returns_df
        )
