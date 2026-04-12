from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from vision.application.optimization_service import OptimizationAppService
from vision.domain.optimization.models import (
    FrontierPoint,
    FrontierRequest,
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


class FrontierRequestSchema(BaseModel):
    tickers: list[str]
    constraints: list[WeightConstraintSchema] = []
    lookback_years: int = 3
    points: int = 50


class FrontierPointSchema(BaseModel):
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


class FrontierResponse(BaseModel):
    points: list[FrontierPointSchema]
    min_volatility: FrontierPointSchema
    max_sharpe: FrontierPointSchema
    equal_weight: FrontierPointSchema


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


def _to_point_schema(p: FrontierPoint) -> FrontierPointSchema:
    return FrontierPointSchema(
        expected_return=p.expected_return,
        expected_volatility=p.expected_volatility,
        sharpe_ratio=p.sharpe_ratio,
        weights=p.weights,
    )


@router.post("/frontier", response_model=FrontierResponse)
def compute_frontier(
    req: FrontierRequestSchema,
    service: OptimizationAppService = Depends(get_optimization_service),  # noqa: B008
) -> FrontierResponse:
    if req.points < 2 or req.points > 200:
        raise HTTPException(
            status_code=422, detail="points must be between 2 and 200"
        )

    domain_constraints = [
        WeightConstraint(
            ticker=c.ticker,
            min_weight=c.min_weight,
            max_weight=c.max_weight,
        )
        for c in req.constraints
    ]
    frontier_request = FrontierRequest(
        tickers=req.tickers,
        constraints=domain_constraints,
        lookback_years=req.lookback_years,
        points=req.points,
    )

    try:
        result = service.compute_frontier(frontier_request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=500, detail="Frontier computation failed"
        ) from e

    return FrontierResponse(
        points=[_to_point_schema(p) for p in result.points],
        min_volatility=_to_point_schema(result.min_volatility),
        max_sharpe=_to_point_schema(result.max_sharpe),
        equal_weight=_to_point_schema(result.equal_weight),
    )
