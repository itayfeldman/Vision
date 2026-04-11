import numpy as np
import statsmodels.api as sm
from numpy.typing import NDArray

from vision.domain.factor.models import FactorDecomposition, FactorExposure


class FactorRegressionService:
    @staticmethod
    def regress(
        portfolio_returns: NDArray[np.floating],
        factor_returns: NDArray[np.floating],
        factor_names: list[str],
    ) -> FactorDecomposition:
        x = sm.add_constant(factor_returns)
        model = sm.OLS(portfolio_returns, x).fit()

        # First coefficient is the intercept (alpha)
        alpha = float(model.params[0])
        alpha_t_stat = float(model.tvalues[0])

        exposures = []
        for i, name in enumerate(factor_names):
            exposures.append(
                FactorExposure(
                    factor_name=name,
                    beta=float(model.params[i + 1]),
                    t_statistic=float(model.tvalues[i + 1]),
                    p_value=float(model.pvalues[i + 1]),
                )
            )

        residual_risk = float(np.std(model.resid, ddof=1))

        return FactorDecomposition(
            exposures=exposures,
            r_squared=float(model.rsquared),
            alpha=alpha,
            alpha_t_stat=alpha_t_stat,
            residual_risk=residual_risk,
        )
