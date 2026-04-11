import numpy as np
from numpy.typing import NDArray

from vision.domain.risk.models import CorrelationMatrix, RiskMetrics

TRADING_DAYS = 252


class RiskCalculationService:
    @staticmethod
    def compute_risk_metrics(returns: NDArray[np.floating]) -> RiskMetrics:
        ann_return = float(np.mean(returns) * TRADING_DAYS)
        ann_vol = float(np.std(returns, ddof=1) * np.sqrt(TRADING_DAYS))

        sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

        downside = returns[returns < 0]
        if len(downside) > 1:
            downside_std = float(
                np.std(downside, ddof=1) * np.sqrt(TRADING_DAYS)
            )
        else:
            downside_std = ann_vol
        sortino = ann_return / downside_std if downside_std > 0 else 0.0

        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = cumulative / running_max - 1
        max_dd = float(np.min(drawdowns))

        # Max drawdown duration
        in_drawdown = drawdowns < 0
        max_duration = 0
        current_duration = 0
        for d in in_drawdown:
            if d:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        var_95 = float(np.percentile(returns, 5))
        var_99 = float(np.percentile(returns, 1))
        cvar_95 = float(np.mean(returns[returns <= var_95]))
        cvar_99 = float(np.mean(returns[returns <= var_99]))

        return RiskMetrics(
            annualized_return=ann_return,
            annualized_volatility=ann_vol,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_duration=max_duration,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
        )

    @staticmethod
    def compute_correlation_matrix(
        returns_dict: dict[str, NDArray[np.floating]],
    ) -> CorrelationMatrix:
        tickers = sorted(returns_dict.keys())
        if len(tickers) < 2:
            return CorrelationMatrix(
                tickers=tickers,
                matrix=[[1.0]] if tickers else [],
            )
        data = np.column_stack([returns_dict[t] for t in tickers])
        corr = np.corrcoef(data, rowvar=False)
        return CorrelationMatrix(
            tickers=tickers,
            matrix=corr.tolist(),
        )
