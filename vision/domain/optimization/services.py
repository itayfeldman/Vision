import pandas as pd

from vision.domain.optimization.models import (
    OptimizationRequest,
    OptimizationResult,
)
from vision.domain.optimization.optimizer import PortfolioOptimizer


class OptimizationService:
    def __init__(self, optimizer: PortfolioOptimizer) -> None:
        self._optimizer = optimizer

    def run_optimization(
        self,
        request: OptimizationRequest,
        returns_df: pd.DataFrame,
    ) -> OptimizationResult:
        if len(request.tickers) < 2:
            raise ValueError("Need at least 2 tickers to optimize")
        return self._optimizer.optimize(
            returns_df=returns_df,
            objective=request.objective,
            constraints=request.constraints,
        )
