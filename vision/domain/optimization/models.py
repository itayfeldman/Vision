from dataclasses import dataclass
from enum import Enum


class OptimizationObjective(Enum):
    MIN_VOLATILITY = "min_volatility"
    MAX_SHARPE = "max_sharpe"
    MAX_RETURN = "max_return"
    RISK_PARITY = "risk_parity"


@dataclass(frozen=True)
class WeightConstraint:
    ticker: str
    min_weight: float
    max_weight: float


@dataclass(frozen=True)
class OptimizationRequest:
    tickers: list[str]
    objective: OptimizationObjective
    constraints: list[WeightConstraint]
    lookback_years: int = 3


@dataclass(frozen=True)
class OptimizationResult:
    weights: dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
