from vision.domain.optimization.models import (
    OptimizationObjective,
    OptimizationRequest,
    OptimizationResult,
    WeightConstraint,
)


def test_optimization_request_creation() -> None:
    req = OptimizationRequest(
        tickers=["AAPL", "GOOGL", "MSFT"],
        objective=OptimizationObjective.MAX_SHARPE,
        constraints=[],
        lookback_years=3,
    )
    assert len(req.tickers) == 3
    assert req.objective == OptimizationObjective.MAX_SHARPE


def test_optimization_result_creation() -> None:
    result = OptimizationResult(
        weights={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
        expected_return=0.12,
        expected_volatility=0.15,
        sharpe_ratio=0.8,
    )
    total = sum(result.weights.values())
    assert abs(total - 1.0) < 1e-9


def test_all_objectives_exist() -> None:
    assert OptimizationObjective.MIN_VOLATILITY
    assert OptimizationObjective.MAX_SHARPE
    assert OptimizationObjective.MAX_RETURN
    assert OptimizationObjective.RISK_PARITY


def test_weight_constraint() -> None:
    c = WeightConstraint(ticker="AAPL", min_weight=0.05, max_weight=0.4)
    assert c.min_weight == 0.05
    assert c.max_weight == 0.4
