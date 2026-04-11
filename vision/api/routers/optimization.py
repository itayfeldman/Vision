from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from vision.application.optimization_service import OptimizationAppService
from vision.domain.optimization.models import (
    OptimizationObjective,
    OptimizationRequest,
    WeightConstraint,
)

router = APIRouter(prefix="/api/optimize", tags=["Optimization"])


class WeightConstraintSchema(BaseModel):
    ticker: str
    min_weight: float = 0.0
    max_weight: float = 1.0


class OptimizeRequest(BaseModel):
    tickers: list[str]
    objective: str = "max_sharpe"
    constraints: list[WeightConstraintSchema] = []
    lookback_years: int = 3
    portfolio_id: str | None = None


class OptimizeResponse(BaseModel):
    weights: dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float


def get_optimization_service() -> OptimizationAppService:
    raise NotImplementedError("Must be overridden via dependency_overrides")


@router.post("", response_model=OptimizeResponse)
def optimize_portfolio(
    req: OptimizeRequest,
    service: OptimizationAppService = Depends(get_optimization_service),  # noqa: B008
) -> OptimizeResponse:
    try:
        objective = OptimizationObjective(req.objective)
    except ValueError as e:
        valid = [o.value for o in OptimizationObjective]
        raise HTTPException(
            status_code=422,
            detail=f"Invalid objective '{req.objective}'. "
            f"Must be one of: {valid}",
        ) from e

    domain_constraints = [
        WeightConstraint(
            ticker=c.ticker,
            min_weight=c.min_weight,
            max_weight=c.max_weight,
        )
        for c in req.constraints
    ]

    request = OptimizationRequest(
        tickers=req.tickers,
        objective=objective,
        constraints=domain_constraints,
        lookback_years=req.lookback_years,
    )

    try:
        result = service.optimize(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=500, detail="Optimization failed"
        ) from e

    return OptimizeResponse(
        weights=result.weights,
        expected_return=result.expected_return,
        expected_volatility=result.expected_volatility,
        sharpe_ratio=result.sharpe_ratio,
    )
