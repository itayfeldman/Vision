import numpy as np

from vision.domain.factor.services import FactorRegressionService


def test_regress_with_known_betas() -> None:
    """Create synthetic data with known factor loadings and verify regression."""
    rng = np.random.default_rng(42)
    n = 500

    # Known factor loadings
    true_alpha = 0.0002  # daily alpha
    true_betas = {
        "Mkt-RF": 1.2,
        "SMB": 0.3,
        "HML": -0.1,
        "RMW": 0.2,
        "CMA": -0.05,
    }

    # Generate factor returns
    factor_names = list(true_betas.keys())
    factor_returns = {
        name: rng.normal(0.0003, 0.01, n) for name in factor_names
    }

    # Generate portfolio returns as linear combination + noise
    portfolio_returns = np.full(n, true_alpha)
    for name, beta in true_betas.items():
        portfolio_returns = portfolio_returns + beta * factor_returns[name]
    portfolio_returns = portfolio_returns + rng.normal(0, 0.002, n)

    # Convert to numpy arrays
    factor_array = np.column_stack(
        [factor_returns[name] for name in factor_names]
    )

    result = FactorRegressionService.regress(
        portfolio_returns, factor_array, factor_names
    )

    # Check structure
    assert len(result.exposures) == 5
    assert 0.0 <= result.r_squared <= 1.0

    # Check that estimated betas are close to true values
    exposure_map = {e.factor_name: e for e in result.exposures}
    for name, true_beta in true_betas.items():
        estimated = exposure_map[name].beta
        assert abs(estimated - true_beta) < 0.15, (
            f"Factor {name}: expected ~{true_beta}, got {estimated}"
        )

    # R-squared should be high since noise is small relative to signal
    assert result.r_squared > 0.8


def test_regress_returns_all_factor_names() -> None:
    rng = np.random.default_rng(42)
    n = 100
    factor_names = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
    portfolio_returns = rng.normal(0, 0.01, n)
    factor_array = rng.normal(0, 0.01, (n, 5))

    result = FactorRegressionService.regress(
        portfolio_returns, factor_array, factor_names
    )

    result_names = [e.factor_name for e in result.exposures]
    assert result_names == factor_names


def test_regress_alpha_is_reasonable() -> None:
    rng = np.random.default_rng(42)
    n = 252
    factor_names = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
    portfolio_returns = rng.normal(0.0005, 0.01, n)
    factor_array = rng.normal(0, 0.01, (n, 5))

    result = FactorRegressionService.regress(
        portfolio_returns, factor_array, factor_names
    )

    # Alpha should be small in magnitude for daily returns
    assert abs(result.alpha) < 0.01
