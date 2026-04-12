from abc import ABC, abstractmethod

import pandas as pd

from vision.domain.optimization.models import (
    FrontierResult,
    OptimizationObjective,
    OptimizationResult,
    WeightConstraint,
)


class PortfolioOptimizer(ABC):
    @abstractmethod
    def optimize(
        self,
        returns_df: pd.DataFrame,
        objective: OptimizationObjective,
        constraints: list[WeightConstraint],
    ) -> OptimizationResult: ...

    @abstractmethod
    def compute_frontier(
        self,
        returns_df: pd.DataFrame,
        constraints: list[WeightConstraint],
        points: int,
    ) -> FrontierResult: ...
