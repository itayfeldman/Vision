import pandas as pd

from vision.domain.optimization.models import (
    FrontierResult,
    OptimizationRequest,
    OptimizationResult,
    WeightConstraint,
)
from vision.domain.optimization.optimizer import PortfolioOptimizer

MAX_FRONTIER_POINTS = 200


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

    def compute_frontier(
        self,
        returns_df: pd.DataFrame,
        constraints: list[WeightConstraint],
        points: int,
    ) -> FrontierResult:
        if len(returns_df.columns) < 2:
            raise ValueError("Need at least 2 tickers for frontier")
        if points < 2:
            raise ValueError("Frontier points must be >= 2")
        capped = min(points, MAX_FRONTIER_POINTS)
        return self._optimizer.compute_frontier(
            returns_df=returns_df,
            constraints=constraints,
            points=capped,
        )
