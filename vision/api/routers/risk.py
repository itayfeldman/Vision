from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from vision.application.portfolio_service import PortfolioNotFoundError
from vision.application.risk_service import RiskAppService
from vision.domain.portfolio.models import Holding

router = APIRouter(prefix="/api/risk", tags=["Risk Analytics"])


class HoldingInput(BaseModel):
    ticker: str
    weight: float


class AdhocRiskRequest(BaseModel):
    holdings: list[HoldingInput]


class RiskMetricsResponse(BaseModel):
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float


class CorrelationMatrixResponse(BaseModel):
    tickers: list[str]
    matrix: list[list[float]]


class RiskReportResponse(BaseModel):
    metrics: RiskMetricsResponse
    correlation: CorrelationMatrixResponse


class PerformancePointResponse(BaseModel):
    date: str
    cumulative_return: float
    volume: int


class PerformanceResponse(BaseModel):
    points: list[PerformancePointResponse]


def get_risk_service() -> RiskAppService:
    raise NotImplementedError("Must be overridden via dependency_overrides")


@router.get("/{portfolio_id}/performance", response_model=PerformanceResponse)
def get_performance(
    portfolio_id: str,
    lookback_years: int = Query(default=3, ge=1, le=10),
    service: RiskAppService = Depends(get_risk_service),  # noqa: B008
) -> PerformanceResponse:
    try:
        series = service.get_portfolio_performance(portfolio_id, lookback_years)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return PerformanceResponse(
        points=[
            PerformancePointResponse(
                date=p.date,
                cumulative_return=p.cumulative_return,
                volume=p.volume,
            )
            for p in series.points
        ]
    )


@router.get("/{portfolio_id}", response_model=RiskReportResponse)
def get_risk_report(
    portfolio_id: str,
    lookback_years: int = Query(default=3, ge=1, le=10),
    service: RiskAppService = Depends(get_risk_service),  # noqa: B008
) -> RiskReportResponse:
    try:
        metrics, correlation = service.analyze_portfolio(portfolio_id, lookback_years)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RiskReportResponse(
        metrics=RiskMetricsResponse(
            annualized_return=metrics.annualized_return,
            annualized_volatility=metrics.annualized_volatility,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            max_drawdown=metrics.max_drawdown,
            max_drawdown_duration=metrics.max_drawdown_duration,
            var_95=metrics.var_95,
            var_99=metrics.var_99,
            cvar_95=metrics.cvar_95,
            cvar_99=metrics.cvar_99,
        ),
        correlation=CorrelationMatrixResponse(
            tickers=correlation.tickers,
            matrix=correlation.matrix,
        ),
    )


@router.post("/analyze", response_model=RiskReportResponse)
def analyze_adhoc(
    req: AdhocRiskRequest,
    lookback_years: int = Query(default=3, ge=1, le=10),
    service: RiskAppService = Depends(get_risk_service),  # noqa: B008
) -> RiskReportResponse:
    holdings = [Holding(ticker=h.ticker, weight=h.weight) for h in req.holdings]
    metrics, correlation = service.analyze_adhoc(holdings, lookback_years)
    return RiskReportResponse(
        metrics=RiskMetricsResponse(
            annualized_return=metrics.annualized_return,
            annualized_volatility=metrics.annualized_volatility,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            max_drawdown=metrics.max_drawdown,
            max_drawdown_duration=metrics.max_drawdown_duration,
            var_95=metrics.var_95,
            var_99=metrics.var_99,
            cvar_95=metrics.cvar_95,
            cvar_99=metrics.cvar_99,
        ),
        correlation=CorrelationMatrixResponse(
            tickers=correlation.tickers,
            matrix=correlation.matrix,
        ),
    )
