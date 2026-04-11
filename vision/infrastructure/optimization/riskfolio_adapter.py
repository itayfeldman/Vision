import numpy as np
import pandas as pd
import riskfolio as rp

from vision.domain.optimization.models import (
    OptimizationObjective,
    OptimizationResult,
    WeightConstraint,
)
from vision.domain.optimization.optimizer import PortfolioOptimizer

TRADING_DAYS = 252


class RiskfolioOptimizer(PortfolioOptimizer):
    def optimize(
        self,
        returns_df: pd.DataFrame,
        objective: OptimizationObjective,
        constraints: list[WeightConstraint],
    ) -> OptimizationResult:
        port = rp.Portfolio(returns=returns_df)
        port.assets_stats(method_mu="hist", method_cov="hist")

        # Apply weight bounds via riskfolio's built-in constraints
        if constraints:
            constraint_map = {c.ticker: c for c in constraints}
            n = len(returns_df.columns)
            upper = np.ones(n)
            lower = np.zeros(n)
            for i, ticker in enumerate(returns_df.columns):
                if ticker in constraint_map:
                    c = constraint_map[ticker]
                    upper[i] = c.max_weight
                    lower[i] = c.min_weight
            port.upperlng = upper
            port.lowerlng = lower

        if objective == OptimizationObjective.RISK_PARITY:
            weights = port.rp_optimization(
                model="Classic",
                rm="MV",
                hist=True,
            )
        else:
            obj_map = {
                OptimizationObjective.MIN_VOLATILITY: ("MinRisk", "MV"),
                OptimizationObjective.MAX_SHARPE: ("Sharpe", "MV"),
                OptimizationObjective.MAX_RETURN: ("MaxRet", "MV"),
            }
            obj_name, rm = obj_map[objective]
            weights = port.optimization(
                model="Classic",
                rm=rm,
                obj=obj_name,
                hist=True,
            )

        if weights is None or weights.empty:
            raise RuntimeError(
                "Optimization failed to find a solution"
            )

        weight_dict: dict[str, float] = {}
        for ticker in returns_df.columns:
            weight_dict[ticker] = float(weights.loc[ticker, "weights"])

        # Compute portfolio metrics
        w_array = np.array(
            [weight_dict[t] for t in returns_df.columns]
        )
        port_returns = returns_df.values @ w_array
        exp_return = float(np.mean(port_returns) * TRADING_DAYS)
        exp_vol = float(
            np.std(port_returns, ddof=1) * np.sqrt(TRADING_DAYS)
        )
        sharpe = exp_return / exp_vol if exp_vol > 0 else 0.0

        return OptimizationResult(
            weights=weight_dict,
            expected_return=exp_return,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
        )
