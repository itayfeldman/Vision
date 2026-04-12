from datetime import date, timedelta

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from vision.application.market_data_service import MarketDataAppService
from vision.application.portfolio_service import PortfolioAppService
from vision.domain.portfolio.models import Holding
from vision.domain.risk.models import (
    BenchmarkComparison,
    CorrelationMatrix,
    RiskMetrics,
)
from vision.domain.risk.services import RiskCalculationService


class BenchmarkUnresolvableError(Exception):
    pass


class RiskAppService:
    def __init__(
        self,
        portfolio_service: PortfolioAppService,
        market_data_service: MarketDataAppService,
    ) -> None:
        self._portfolio_service = portfolio_service
        self._market_data_service = market_data_service

    def analyze_portfolio(
        self, portfolio_id: str, lookback_years: int = 3
    ) -> tuple[RiskMetrics, CorrelationMatrix]:
        portfolio = self._portfolio_service.get_portfolio(portfolio_id)
        return self._analyze_holdings(portfolio.holdings, lookback_years)

    def analyze_adhoc(
        self, holdings: list[Holding], lookback_years: int = 3
    ) -> tuple[RiskMetrics, CorrelationMatrix]:
        return self._analyze_holdings(holdings, lookback_years)

    def _analyze_holdings(
        self, holdings: list[Holding], lookback_years: int
    ) -> tuple[RiskMetrics, CorrelationMatrix]:
        end = date.today()
        start = end - timedelta(days=lookback_years * 365)

        ticker_returns: dict[str, NDArray[np.floating]] = {}
        for h in holdings:
            daily = self._market_data_service.get_daily_returns(h.ticker, start, end)
            if daily:
                ticker_returns[h.ticker] = np.array([r for _, r in daily])

        if not ticker_returns:
            empty_metrics = RiskMetrics(
                annualized_return=0.0,
                annualized_volatility=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
                var_95=0.0,
                var_99=0.0,
                cvar_95=0.0,
                cvar_99=0.0,
            )
            return empty_metrics, CorrelationMatrix(tickers=[], matrix=[])

        # Compute portfolio-weighted returns
        # Align all series to the shortest length
        min_len = min(len(r) for r in ticker_returns.values())
        portfolio_returns = np.zeros(min_len)
        for h in holdings:
            if h.ticker in ticker_returns:
                portfolio_returns += h.weight * ticker_returns[h.ticker][:min_len]

        metrics = RiskCalculationService.compute_risk_metrics(portfolio_returns)

        # Trim all series for correlation
        trimmed = {t: r[:min_len] for t, r in ticker_returns.items()}
        correlation = RiskCalculationService.compute_correlation_matrix(trimmed)

        return metrics, correlation

    def compare_to_benchmark(
        self,
        portfolio_id: str,
        benchmark_ticker: str = "SPY",
        lookback_years: int = 3,
    ) -> BenchmarkComparison:
        portfolio = self._portfolio_service.get_portfolio(portfolio_id)
        end = date.today()
        start = end - timedelta(days=lookback_years * 365)

        frame: dict[str, pd.Series] = {}
        for h in portfolio.holdings:
            daily = self._market_data_service.get_daily_returns(
                h.ticker, start, end
            )
            if daily:
                frame[h.ticker] = pd.Series(
                    [r for _, r in daily],
                    index=[d for d, _ in daily],
                )

        if not frame:
            raise ValueError("No market data available for portfolio holdings")

        try:
            bench_daily = self._market_data_service.get_daily_returns(
                benchmark_ticker, start, end
            )
        except Exception as e:
            raise BenchmarkUnresolvableError(
                f"Could not resolve benchmark '{benchmark_ticker}'"
            ) from e
        if not bench_daily:
            raise BenchmarkUnresolvableError(
                f"No data for benchmark '{benchmark_ticker}'"
            )
        frame["__benchmark__"] = pd.Series(
            [r for _, r in bench_daily],
            index=[d for d, _ in bench_daily],
        )

        df = pd.DataFrame(frame).dropna()
        if df.empty:
            raise ValueError(
                "Portfolio and benchmark histories do not overlap"
            )

        bench_col = df["__benchmark__"].to_numpy()
        ticker_cols = [c for c in df.columns if c != "__benchmark__"]
        weights = {h.ticker: h.weight for h in portfolio.holdings}
        port_col = np.zeros(len(df))
        for t in ticker_cols:
            port_col += weights[t] * df[t].to_numpy()

        aligned_dates = [d for d in df.index]
        return RiskCalculationService.compute_benchmark_comparison(
            dates=aligned_dates,
            portfolio_returns=port_col,
            benchmark_returns=bench_col,
            benchmark_ticker=benchmark_ticker,
        )
