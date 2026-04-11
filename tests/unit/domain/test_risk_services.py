import numpy as np

from vision.domain.risk.models import RiskMetrics
from vision.domain.risk.services import RiskCalculationService


def _known_returns() -> np.ndarray:
    """Daily returns for ~1 year with known properties."""
    rng = np.random.default_rng(42)
    return rng.normal(0.0004, 0.01, 252)  # ~10% annual return, ~16% vol


def test_compute_risk_metrics_returns_all_fields() -> None:
    returns = _known_returns()
    metrics = RiskCalculationService.compute_risk_metrics(returns)
    assert isinstance(metrics, RiskMetrics)
    assert metrics.annualized_return is not None
    assert metrics.annualized_volatility > 0
    assert metrics.sharpe_ratio is not None
    assert metrics.sortino_ratio is not None
    assert metrics.max_drawdown <= 0
    assert metrics.var_95 < 0
    assert metrics.var_99 < 0
    assert metrics.cvar_95 <= metrics.var_95
    assert metrics.cvar_99 <= metrics.var_99


def test_annualized_return_reasonable() -> None:
    returns = _known_returns()
    metrics = RiskCalculationService.compute_risk_metrics(returns)
    assert -0.5 < metrics.annualized_return < 1.0


def test_annualized_volatility_reasonable() -> None:
    returns = _known_returns()
    metrics = RiskCalculationService.compute_risk_metrics(returns)
    assert 0.05 < metrics.annualized_volatility < 0.5


def test_sharpe_ratio_calculation() -> None:
    returns = _known_returns()
    metrics = RiskCalculationService.compute_risk_metrics(returns)
    expected_sharpe = (metrics.annualized_return) / metrics.annualized_volatility
    assert abs(metrics.sharpe_ratio - expected_sharpe) < 0.01


def test_var_ordering() -> None:
    returns = _known_returns()
    metrics = RiskCalculationService.compute_risk_metrics(returns)
    assert metrics.var_99 <= metrics.var_95


def test_max_drawdown_is_negative() -> None:
    returns = _known_returns()
    metrics = RiskCalculationService.compute_risk_metrics(returns)
    assert metrics.max_drawdown < 0


def test_compute_correlation_matrix() -> None:
    rng = np.random.default_rng(42)
    returns_dict = {
        "AAPL": rng.normal(0, 0.01, 100),
        "GOOGL": rng.normal(0, 0.01, 100),
    }
    corr = RiskCalculationService.compute_correlation_matrix(returns_dict)
    assert corr.tickers == ["AAPL", "GOOGL"]
    assert len(corr.matrix) == 2
    assert len(corr.matrix[0]) == 2
    assert abs(corr.matrix[0][0] - 1.0) < 1e-9
    assert abs(corr.matrix[1][1] - 1.0) < 1e-9
