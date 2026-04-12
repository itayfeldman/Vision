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
    PerformancePoint,
    PerformanceSeries,
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

    def get_portfolio_performance(
        self, portfolio_id: str, lookback_years: int = 3
    ) -> PerformanceSeries:
        portfolio = self._portfolio_service.get_portfolio(portfolio_id)
        return self._compute_performance(portfolio.holdings, lookback_years)

    def _compute_performance(
        self, holdings: list[Holding], lookback_years: int
    ) -> PerformanceSeries:
        end = date.today()
        start = end - timedelta(days=lookback_years * 365)

        from vision.domain.market_data.models import PriceHistory
        from vision.domain.market_data.services import MarketDataService

        ticker_prices: dict[str, PriceHistory] = {}
        for h in holdings:
            ph = self._market_data_service.get_price_history(
                h.ticker, start, end
            )
            if ph and len(ph.dates) > 1:
                ticker_prices[h.ticker] = ph

        if not ticker_prices:
            return PerformanceSeries(points=[])

        # Compute daily returns from price histories
        ticker_returns: dict[str, list[tuple[date, float]]] = {}
        for ticker, ph in ticker_prices.items():
            ticker_returns[ticker] = MarketDataService.compute_daily_returns(ph)

        # returns have len(prices)-1 entries; volumes align with prices
        # so volume index i corresponds to return index i-1
        min_len = min(len(v) for v in ticker_returns.values())
        dates = list(ticker_returns.values())[0][:min_len]

        portfolio_returns = np.zeros(min_len)
        total_volumes = np.zeros(min_len, dtype=np.int64)

        for h in holdings:
            if h.ticker in ticker_returns:
                returns = np.array(
                    [r for _, r in ticker_returns[h.ticker][:min_len]]
                )
                portfolio_returns += h.weight * returns
                # volumes[1:] aligns with returns (skip first price day)
                vols = ticker_prices[h.ticker].volumes[1 : min_len + 1]
                total_volumes += np.array(vols, dtype=np.int64)

        cumulative = np.cumprod(1 + portfolio_returns)
        return PerformanceSeries(
            points=[
                PerformancePoint(
                    date=dates[i][0].isoformat(),
                    cumulative_return=float(cumulative[i]) - 1.0,
                    volume=int(total_volumes[i]),
                )
                for i in range(len(cumulative))
            ]
        )

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
