from dataclasses import dataclass


@dataclass(frozen=True)
class RiskMetrics:
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int  # days
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float


@dataclass(frozen=True)
class CorrelationMatrix:
    tickers: list[str]
    matrix: list[list[float]]


@dataclass(frozen=True)
class SpreadPoint:
    date: str  # ISO format
    portfolio_cum: float
    benchmark_cum: float
    spread: float


@dataclass(frozen=True)
class BenchmarkComparison:
    benchmark_ticker: str
    tracking_error: float
    beta: float
    alpha: float
    up_capture: float
    down_capture: float
    spread_series: list[SpreadPoint]
