from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from vision.api.routers.factors import get_factor_service
from vision.api.routers.risk import get_risk_service
from vision.application.factor_service import FactorAppService
from vision.application.portfolio_service import (
    PortfolioAppService,
    PortfolioNotFoundError,
)
from vision.application.risk_service import RiskAppService
from vision.domain.portfolio.models import Holding, Portfolio
from vision.domain.portfolio.services import InvalidTickerError, InvalidWeightsError

router = APIRouter(prefix="/api/portfolios", tags=["Portfolios"])


class HoldingSchema(BaseModel):
    ticker: str
    weight: float


class CreatePortfolioRequest(BaseModel):
    name: str
    holdings: list[HoldingSchema]


class PortfolioResponse(BaseModel):
    id: str
    name: str
    holdings: list[HoldingSchema]


class ValuedHoldingSchema(BaseModel):
    ticker: str
    weight: float
    current_price: float
    shares: float
    market_value: float


class ValuedPortfolioResponse(BaseModel):
    id: str
    name: str
    holdings: list[ValuedHoldingSchema]
    total_value: float


class FactorExposureSummary(BaseModel):
    factor_name: str
    beta: float


class RiskSummary(BaseModel):
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float


class PortfolioSummaryResponse(BaseModel):
    id: str
    name: str
    holdings: list[HoldingSchema]
    risk: RiskSummary
    factor_exposures: list[FactorExposureSummary]


def get_portfolio_service() -> PortfolioAppService:
    raise NotImplementedError("Must be overridden via dependency_overrides")


def _to_response(p: Portfolio) -> PortfolioResponse:
    return PortfolioResponse(
        id=p.id,
        name=p.name,
        holdings=[
            HoldingSchema(ticker=h.ticker, weight=h.weight)
            for h in p.holdings
        ],
    )


def _to_domain_holdings(
    schemas: list[HoldingSchema],
) -> list[Holding]:
    return [Holding(ticker=h.ticker, weight=h.weight) for h in schemas]


@router.post("", response_model=PortfolioResponse, status_code=201)
def create_portfolio(
    req: CreatePortfolioRequest,
    service: PortfolioAppService = Depends(get_portfolio_service),  # noqa: B008
) -> PortfolioResponse:
    try:
        portfolio = service.create_portfolio(
            name=req.name,
            holdings=_to_domain_holdings(req.holdings),
        )
    except (InvalidWeightsError, InvalidTickerError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _to_response(portfolio)


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    service: PortfolioAppService = Depends(get_portfolio_service),  # noqa: B008
) -> list[PortfolioResponse]:
    return [_to_response(p) for p in service.list_portfolios()]


@router.get(
    "/{portfolio_id}/summary",
    response_model=PortfolioSummaryResponse,
)
def get_portfolio_summary(
    portfolio_id: str,
    portfolio_svc: PortfolioAppService = Depends(get_portfolio_service),  # noqa: B008
    risk_svc: RiskAppService = Depends(get_risk_service),  # noqa: B008
    factor_svc: FactorAppService = Depends(get_factor_service),  # noqa: B008
) -> PortfolioSummaryResponse:
    try:
        portfolio = portfolio_svc.get_portfolio(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    metrics, _ = risk_svc.analyze_portfolio(portfolio_id)
    decomposition = factor_svc.analyze_portfolio(portfolio_id)

    return PortfolioSummaryResponse(
        id=portfolio.id,
        name=portfolio.name,
        holdings=[
            HoldingSchema(ticker=h.ticker, weight=h.weight)
            for h in portfolio.holdings
        ],
        risk=RiskSummary(
            annualized_return=metrics.annualized_return,
            annualized_volatility=metrics.annualized_volatility,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            var_95=metrics.var_95,
        ),
        factor_exposures=[
            FactorExposureSummary(
                factor_name=e.factor_name,
                beta=e.beta,
            )
            for e in decomposition.exposures
        ],
    )


@router.get(
    "/{portfolio_id}",
    response_model=ValuedPortfolioResponse | PortfolioResponse,
)
def get_portfolio(
    portfolio_id: str,
    valued: bool = Query(default=False),
    service: PortfolioAppService = Depends(get_portfolio_service),  # noqa: B008
) -> ValuedPortfolioResponse | PortfolioResponse:
    try:
        if valued:
            vp = service.get_portfolio_with_values(portfolio_id)
            return ValuedPortfolioResponse(
                id=vp.id,
                name=vp.name,
                holdings=[
                    ValuedHoldingSchema(
                        ticker=h.ticker,
                        weight=h.weight,
                        current_price=h.current_price,
                        shares=h.shares,
                        market_value=h.market_value,
                    )
                    for h in vp.holdings
                ],
                total_value=vp.total_value,
            )
        portfolio = service.get_portfolio(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return _to_response(portfolio)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: str,
    req: CreatePortfolioRequest,
    service: PortfolioAppService = Depends(get_portfolio_service),  # noqa: B008
) -> PortfolioResponse:
    try:
        portfolio = service.update_portfolio(
            portfolio_id=portfolio_id,
            name=req.name,
            holdings=_to_domain_holdings(req.holdings),
        )
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (InvalidWeightsError, InvalidTickerError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _to_response(portfolio)


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(
    portfolio_id: str,
    service: PortfolioAppService = Depends(get_portfolio_service),  # noqa: B008
) -> None:
    try:
        service.delete_portfolio(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
