from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from vision.api.middleware import RequestLoggingMiddleware
from vision.api.routers.factors import router as factors_router
from vision.api.routers.market_data import router as market_data_router
from vision.api.routers.optimization import router as optimization_router
from vision.api.routers.portfolios import router as portfolios_router
from vision.api.routers.risk import router as risk_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vision",
        description="Portfolio Construction & Analytics Platform",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(market_data_router)
    app.include_router(portfolios_router)
    app.include_router(risk_router)
    app.include_router(optimization_router)
    app.include_router(factors_router)

    return app
