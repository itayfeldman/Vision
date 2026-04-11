import numpy as np
import pandas as pd

from vision.domain.optimization.models import (
    OptimizationObjective,
    WeightConstraint,
)
from vision.infrastructure.optimization.riskfolio_adapter import RiskfolioOptimizer


def _synthetic_returns() -> pd.DataFrame:
    """Create synthetic return data for 3 assets over 252 days."""
    rng = np.random.default_rng(42)
    n_days = 252
    returns = pd.DataFrame(
        {
            "AAPL": rng.normal(0.0005, 0.015, n_days),
            "GOOGL": rng.normal(0.0004, 0.018, n_days),
            "MSFT": rng.normal(0.0006, 0.012, n_days),
        }
    )
    return returns


def test_min_volatility() -> None:
    optimizer = RiskfolioOptimizer()
    result = optimizer.optimize(
        _synthetic_returns(), OptimizationObjective.MIN_VOLATILITY, []
    )
    assert abs(sum(result.weights.values()) - 1.0) < 1e-6
    assert result.expected_volatility > 0


def test_max_sharpe() -> None:
    optimizer = RiskfolioOptimizer()
    result = optimizer.optimize(
        _synthetic_returns(), OptimizationObjective.MAX_SHARPE, []
    )
    assert abs(sum(result.weights.values()) - 1.0) < 1e-6


def test_risk_parity() -> None:
    optimizer = RiskfolioOptimizer()
    result = optimizer.optimize(
        _synthetic_returns(), OptimizationObjective.RISK_PARITY, []
    )
    assert abs(sum(result.weights.values()) - 1.0) < 1e-6


def test_with_weight_constraints() -> None:
    optimizer = RiskfolioOptimizer()
    constraints = [
        WeightConstraint(ticker="AAPL", min_weight=0.1, max_weight=0.5),
        WeightConstraint(ticker="GOOGL", min_weight=0.1, max_weight=0.5),
        WeightConstraint(ticker="MSFT", min_weight=0.1, max_weight=0.5),
    ]
    result = optimizer.optimize(
        _synthetic_returns(), OptimizationObjective.MAX_SHARPE, constraints
    )
    for ticker, weight in result.weights.items():
        assert weight >= 0.1 - 1e-6, f"{ticker} weight {weight} below min"
        assert weight <= 0.5 + 1e-6, f"{ticker} weight {weight} above max"
