from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from vision.application.factor_service import FactorAppService
from vision.application.portfolio_service import PortfolioNotFoundError

router = APIRouter(prefix="/api/factors", tags=["Factor Analysis"])


class FactorExposureResponse(BaseModel):
    factor_name: str
    beta: float
    t_statistic: float
    p_value: float


class FactorDecompositionResponse(BaseModel):
    exposures: list[FactorExposureResponse]
    r_squared: float
    alpha: float
    alpha_t_stat: float
    residual_risk: float


def get_factor_service() -> FactorAppService:
    raise NotImplementedError("Must be overridden via dependency_overrides")


@router.get(
    "/{portfolio_id}",
    response_model=FactorDecompositionResponse,
)
def get_factor_decomposition(
    portfolio_id: str,
    lookback_years: int = Query(default=3, ge=1, le=10),
    service: FactorAppService = Depends(get_factor_service),  # noqa: B008
) -> FactorDecompositionResponse:
    try:
        result = service.analyze_portfolio(
            portfolio_id, lookback_years
        )
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return FactorDecompositionResponse(
        exposures=[
            FactorExposureResponse(
                factor_name=e.factor_name,
                beta=e.beta,
                t_statistic=e.t_statistic,
                p_value=e.p_value,
            )
            for e in result.exposures
        ],
        r_squared=result.r_squared,
        alpha=result.alpha,
        alpha_t_stat=result.alpha_t_stat,
        residual_risk=result.residual_risk,
    )
