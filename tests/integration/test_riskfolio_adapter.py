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


def test_frontier_honors_max_weight_constraint() -> None:
    """Every point in the frontier sweep — including named portfolios — must
    respect the per-ticker max_weight bound.  Without constraints the
    unconstrained max-Sharpe portfolio often concentrates >80% in one asset;
    capping at 0.40 forces the constraint to be visible and testable."""
    optimizer = RiskfolioOptimizer()
    max_w = 0.40
    eps = 1e-4
    constraints = [
        WeightConstraint(ticker=t, min_weight=0.0, max_weight=max_w)
        for t in ("AAPL", "GOOGL", "MSFT")
    ]
    result = optimizer.compute_frontier(
        _synthetic_returns(),
        constraints,
        points=20,
    )

    # All sweep points
    for i, fp in enumerate(result.points):
        for ticker, w in fp.weights.items():
            assert w <= max_w + eps, (
                f"Sweep point {i}: {ticker} weight {w:.4f} exceeds "
                f"max_weight={max_w}"
            )

    # Named portfolios
    for label, fp in [
        ("min_volatility", result.min_volatility),
        ("max_sharpe", result.max_sharpe),
    ]:
        for ticker, w in fp.weights.items():
            assert w <= max_w + eps, (
                f"{label}: {ticker} weight {w:.4f} exceeds max_weight={max_w}"
            )


def test_frontier_honors_min_weight_constraint() -> None:
    """Every weight in the frontier must respect the per-ticker min_weight."""
    optimizer = RiskfolioOptimizer()
    min_w = 0.15
    eps = 1e-4
    constraints = [
        WeightConstraint(ticker=t, min_weight=min_w, max_weight=1.0)
        for t in ("AAPL", "GOOGL", "MSFT")
    ]

    result = optimizer.compute_frontier(
        _synthetic_returns(),
        constraints,
        points=20,
    )

    for i, fp in enumerate(result.points):
        for ticker, w in fp.weights.items():
            assert w >= min_w - eps, (
                f"Sweep point {i}: {ticker} weight {w:.4f} below "
                f"min_weight={min_w}"
            )
