from datetime import date

import numpy as np
from numpy.typing import NDArray

from vision.domain.risk.models import (
    BenchmarkComparison,
    CorrelationMatrix,
    RiskMetrics,
    SpreadPoint,
)

TRADING_DAYS = 252
MIN_BENCHMARK_DAYS = 60


def _capture_ratio(
    portfolio_returns: NDArray[np.floating],
    benchmark_returns: NDArray[np.floating],
    mask: NDArray[np.bool_],
) -> float:
    if not np.any(mask):
        return 0.0
    bench_mean = float(np.mean(benchmark_returns[mask]))
    if bench_mean == 0:
        return 0.0
    return float(np.mean(portfolio_returns[mask]) / bench_mean)


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
    def compute_benchmark_comparison(
        dates: list[date],
        portfolio_returns: NDArray[np.floating],
        benchmark_returns: NDArray[np.floating],
        benchmark_ticker: str,
    ) -> BenchmarkComparison:
        if len(portfolio_returns) != len(benchmark_returns) or len(dates) != len(
            portfolio_returns
        ):
            raise ValueError("Portfolio and benchmark series must be aligned")
        if len(portfolio_returns) < MIN_BENCHMARK_DAYS:
            raise ValueError(
                f"Need at least {MIN_BENCHMARK_DAYS} aligned days for "
                f"benchmark comparison; got {len(portfolio_returns)}"
            )

        bench_var = float(np.var(benchmark_returns, ddof=1))
        if bench_var <= 0:
            raise ValueError("Benchmark returns have zero variance")

        cov = float(
            np.cov(portfolio_returns, benchmark_returns, ddof=1)[0, 1]
        )
        beta = cov / bench_var

        ann_port_return = float(np.mean(portfolio_returns) * TRADING_DAYS)
        ann_bench_return = float(np.mean(benchmark_returns) * TRADING_DAYS)
        alpha = ann_port_return - beta * ann_bench_return

        diffs = portfolio_returns - benchmark_returns
        tracking_error = float(
            np.std(diffs, ddof=1) * np.sqrt(TRADING_DAYS)
        )

        up_capture = _capture_ratio(
            portfolio_returns, benchmark_returns, benchmark_returns > 0
        )
        down_capture = _capture_ratio(
            portfolio_returns, benchmark_returns, benchmark_returns < 0
        )

        port_cum = np.cumprod(1 + portfolio_returns) - 1.0
        bench_cum = np.cumprod(1 + benchmark_returns) - 1.0
        spread_series = [
            SpreadPoint(
                date=dates[i].isoformat(),
                portfolio_cum=float(port_cum[i]),
                benchmark_cum=float(bench_cum[i]),
                spread=float(port_cum[i] - bench_cum[i]),
            )
            for i in range(len(dates))
        ]

        return BenchmarkComparison(
            benchmark_ticker=benchmark_ticker,
            tracking_error=tracking_error,
            beta=beta,
            alpha=alpha,
            up_capture=up_capture,
            down_capture=down_capture,
            spread_series=spread_series,
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
