import numpy as np
import pandas as pd
import riskfolio as rp

from vision.domain.optimization.models import (
    FrontierPoint,
    FrontierResult,
    OptimizationObjective,
    OptimizationResult,
    WeightConstraint,
)
from vision.domain.optimization.optimizer import PortfolioOptimizer

TRADING_DAYS = 252


def _apply_constraints(
    port: "rp.Portfolio",
    tickers: list[str],
    constraints: list[WeightConstraint],
) -> None:
    if not constraints:
        return
    constraint_map = {c.ticker: c for c in constraints}
    n = len(tickers)
    upper = np.ones(n)
    lower = np.zeros(n)
    for i, ticker in enumerate(tickers):
        if ticker in constraint_map:
            c = constraint_map[ticker]
            upper[i] = c.max_weight
            lower[i] = c.min_weight
    port.upperlng = upper
    port.lowerlng = lower


def _weights_from_column(
    tickers: list[str], weights_df: pd.DataFrame, col: object
) -> dict[str, float]:
    return {t: float(weights_df.loc[t, col]) for t in tickers}


def _point_metrics(
    returns_df: pd.DataFrame, weight_dict: dict[str, float]
) -> tuple[float, float, float]:
    w = np.array([weight_dict[t] for t in returns_df.columns])
    port_returns = returns_df.values @ w
    exp_return = float(np.mean(port_returns) * TRADING_DAYS)
    exp_vol = float(np.std(port_returns, ddof=1) * np.sqrt(TRADING_DAYS))
    sharpe = exp_return / exp_vol if exp_vol > 0 else 0.0
    return exp_return, exp_vol, sharpe


class RiskfolioOptimizer(PortfolioOptimizer):
    def optimize(
        self,
        returns_df: pd.DataFrame,
        objective: OptimizationObjective,
        constraints: list[WeightConstraint],
    ) -> OptimizationResult:
        port = rp.Portfolio(returns=returns_df)
        port.assets_stats(method_mu="hist", method_cov="hist")
        _apply_constraints(port, list(returns_df.columns), constraints)

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

        weight_dict = _weights_from_column(
            list(returns_df.columns), weights, "weights"
        )
        exp_return, exp_vol, sharpe = _point_metrics(returns_df, weight_dict)

        return OptimizationResult(
            weights=weight_dict,
            expected_return=exp_return,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
        )

    def compute_frontier(
        self,
        returns_df: pd.DataFrame,
        constraints: list[WeightConstraint],
        points: int,
    ) -> FrontierResult:
        tickers = list(returns_df.columns)
        port = rp.Portfolio(returns=returns_df)
        port.assets_stats(method_mu="hist", method_cov="hist")
        _apply_constraints(port, tickers, constraints)

        frontier_df = port.efficient_frontier(
            model="Classic", rm="MV", points=points, hist=True
        )
        if frontier_df is None or frontier_df.empty:
            raise RuntimeError("Frontier computation failed")

        frontier_points: list[FrontierPoint] = []
        for col in frontier_df.columns:
            weights = _weights_from_column(tickers, frontier_df, col)
            exp_return, exp_vol, sharpe = _point_metrics(returns_df, weights)
            frontier_points.append(
                FrontierPoint(
                    expected_return=exp_return,
                    expected_volatility=exp_vol,
                    sharpe_ratio=sharpe,
                    weights=weights,
                )
            )

        min_vol = self._solve_named(
            port, returns_df, tickers, "MinRisk"
        )
        max_sharpe = self._solve_named(
            port, returns_df, tickers, "Sharpe"
        )
        equal_weight = self._equal_weight(returns_df, tickers)

        return FrontierResult(
            points=frontier_points,
            min_volatility=min_vol,
            max_sharpe=max_sharpe,
            equal_weight=equal_weight,
        )

    @staticmethod
    def _solve_named(
        port: "rp.Portfolio",
        returns_df: pd.DataFrame,
        tickers: list[str],
        obj_name: str,
    ) -> FrontierPoint:
        weights = port.optimization(
            model="Classic", rm="MV", obj=obj_name, hist=True
        )
        if weights is None or weights.empty:
            raise RuntimeError(f"Failed to solve {obj_name}")
        weight_dict = _weights_from_column(tickers, weights, "weights")
        exp_return, exp_vol, sharpe = _point_metrics(returns_df, weight_dict)
        return FrontierPoint(
            expected_return=exp_return,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            weights=weight_dict,
        )

    @staticmethod
    def _equal_weight(
        returns_df: pd.DataFrame, tickers: list[str]
    ) -> FrontierPoint:
        n = len(tickers)
        weight_dict = {t: 1.0 / n for t in tickers}
        exp_return, exp_vol, sharpe = _point_metrics(returns_df, weight_dict)
        return FrontierPoint(
            expected_return=exp_return,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            weights=weight_dict,
        )
