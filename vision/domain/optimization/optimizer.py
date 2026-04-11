from abc import ABC, abstractmethod

import pandas as pd

from vision.domain.optimization.models import (
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
