# Vision Implementation Plan

## Dependency Graph

```
Task 1: Project Scaffolding
    │
    v
Task 2: Market Data Context (domain + infra + API + tests)
    │
    ├───────────────┐
    v               v
Task 3: Portfolio   │
  Domain + CRUD     │
    │               │
    ├───────┬───────┤
    v       v       v
Task 4   Task 5   Task 6   Task 7
Valuatn  Risk     Optim.   Factor
    │       │       │       │
    └───────┴───────┴───────┘
            │
            v
    Task 8: Cross-Context Integration
            │
            v
    Task 9: Error Handling & API Polish
            │
            v
    Task 10: CI/CD + Docker + Deploy Config
```

- **Task 1** blocks everything
- **Task 2** blocks Tasks 3-7 (all contexts need market data)
- **Task 3** blocks Tasks 4-7 (they need a portfolio to operate on)
- **Tasks 4, 5, 6, 7** are independent of each other (parallelizable)
- **Task 8** depends on Tasks 5, 6, 7
- **Task 9** depends on Task 8
- **Task 10** depends on Task 9

---

## Task 1: Project Scaffolding + Dev Tooling

**Goal:** Create directory structure, install dependencies, configure tooling, write a smoke test (`GET /health` returning 200).

**Key files to create:**
- `vision/` package with all subpackage `__init__.py` files
- `vision/api/app.py` — FastAPI app factory
- `vision/api/dependencies.py` — DI container stub
- `vision/infrastructure/database/connection.py` — SQLite engine + init_db
- `pyproject.toml` — all deps + ruff/mypy/pytest config
- `main.py` — updated to run uvicorn
- `tests/conftest.py` + `tests/api/test_health.py`

**Acceptance criteria:**
1. `uv sync` succeeds
2. `uv run ruff check .` passes clean
3. `uv run ruff format --check .` passes clean
4. `uv run mypy vision/` passes with zero errors
5. `uv run pytest` discovers and runs the health smoke test
6. `GET /health` returns `{"status": "ok"}`

**Verification:**
```bash
uv sync && uv run ruff check . && uv run mypy vision/ && uv run pytest tests/api/test_health.py -v
```

---

## Task 2: Market Data Context (Vertical Slice)

**Goal:** Complete market data bounded context — domain models, abstract repo, yfinance adapter, SQLite price cache, application service, API endpoint, tests.

**Key files:**
- `vision/domain/market_data/models.py` — `PriceHistory`, `AssetInfo` dataclasses
- `vision/domain/market_data/repository.py` — `MarketDataRepository` ABC
- `vision/domain/market_data/services.py` — `MarketDataService` (compute daily returns)
- `vision/infrastructure/market_data/yfinance_adapter.py` — concrete repo
- `vision/infrastructure/database/models.py` — `price_cache` table
- `vision/application/market_data_service.py` — cache-first orchestration
- `vision/api/routers/market_data.py` — `GET /api/market-data/{ticker}/prices`
- Tests: unit (models, services), integration (yfinance, database), API

**Acceptance criteria:**
1. `MarketDataService.get_daily_returns()` returns `(date, return)` tuples from price history
2. `validate_ticker("AAPL")` returns True; `validate_ticker("XYZNOTREAL123")` returns False
3. Cache-first: second call for same ticker+range reads from SQLite, not yfinance
4. `GET /api/market-data/AAPL/prices` returns JSON with dates and close prices
5. All unit tests pass without network access

**Verification:**
```bash
uv run pytest tests/unit/domain/test_market_data_models.py tests/unit/domain/test_market_data_services.py -v
uv run pytest tests/integration/test_database.py -v
uv run pytest tests/api/test_market_data_endpoints.py -v
```

---

## Task 3: Portfolio Domain + CRUD (Vertical Slice)

**Goal:** Portfolio construction — domain models, repo interface, SQLite repo, application service, full CRUD API, tests.

**Key files:**
- `vision/domain/portfolio/models.py` — `Portfolio`, `Holding` frozen dataclasses
- `vision/domain/portfolio/repository.py` — `PortfolioRepository` ABC
- `vision/domain/portfolio/services.py` — `PortfolioConstructionService` (weight validation, ticker validation)
- `vision/infrastructure/database/repositories.py` — `SQLitePortfolioRepository`
- `vision/infrastructure/database/models.py` — `portfolios`, `holdings` tables
- `vision/application/portfolio_service.py` — CRUD orchestration
- `vision/api/routers/portfolios.py` — `POST/GET/PUT/DELETE /api/portfolios`
- `vision/api/schemas/portfolio.py` — Pydantic request/response models
- Tests: unit (models, services, app service), integration (repo), API

**Acceptance criteria:**
1. Weights not summing to 1.0 raises domain validation error
2. Invalid ticker raises domain validation error
3. `POST /api/portfolios` → 201 with portfolio ID
4. `GET /api/portfolios/{id}` → portfolio with holdings
5. `GET /api/portfolios` → list of all portfolios
6. `PUT /api/portfolios/{id}` → 200, updated holdings
7. `DELETE /api/portfolios/{id}` → 204
8. `GET` on deleted portfolio → 404
9. Domain models are frozen dataclasses with no framework imports

**Verification:**
```bash
uv run pytest tests/unit/domain/test_portfolio_models.py tests/unit/domain/test_portfolio_services.py -v
uv run pytest tests/integration/test_portfolio_repository.py -v
uv run pytest tests/api/test_portfolio_endpoints.py -v
```

---

## Task 4: Portfolio Valuation (Vertical Slice)

**Goal:** Enrich portfolio retrieval with current market values — each holding shows price and market value.

**Key files:**
- `vision/domain/portfolio/models.py` — add `ValuedHolding`, `ValuedPortfolio`
- `vision/domain/portfolio/services.py` — add `value_portfolio(portfolio, prices)`
- `vision/application/portfolio_service.py` — add `get_portfolio_with_values(id)`
- `vision/api/routers/portfolios.py` — enrich `GET /api/portfolios/{id}?valued=true`
- Tests: unit + API

**Acceptance criteria:**
1. `GET /api/portfolios/{id}?valued=true` returns holdings with `current_price` and `market_value`
2. `ValuedPortfolio.total_value` = sum of all `holding.market_value`
3. Unavailable market data → holding price is `null`, endpoint still succeeds
4. `value_portfolio` is a pure domain function with no infrastructure deps

**Verification:**
```bash
uv run pytest tests/unit/domain/test_portfolio_valuation.py -v
uv run pytest tests/api/test_portfolio_valuation_endpoint.py -v
```

---

## Task 5: Risk Analytics Context (Vertical Slice)

**Goal:** Complete risk analytics — domain models, pure-Python calculation service, application service, two API endpoints, tests.

**Key files:**
- `vision/domain/risk/models.py` — `RiskMetrics`, `DrawdownAnalysis`, `CorrelationMatrix`
- `vision/domain/risk/services.py` — `RiskCalculationService` (pure functions: `compute_risk_metrics`, `compute_var`, `compute_drawdown`, `compute_correlation`)
- `vision/application/risk_service.py` — `RiskAppService`
- `vision/api/routers/risk.py` — `GET /api/risk/{portfolio_id}`, `POST /api/risk/analyze`
- `vision/api/schemas/risk.py` — Pydantic models
- Tests: unit (use known return series, verify against hand-calculated values), API

**Acceptance criteria:**
1. `compute_risk_metrics` with known series → Sharpe within 0.01 of expected
2. `compute_var` at 95% → matches expected quantile
3. `compute_drawdown` → correct max drawdown and duration
4. `GET /api/risk/{portfolio_id}` → all metrics from SPEC section 4.3
5. `POST /api/risk/analyze` → ad-hoc analysis (no saved portfolio needed)
6. Configurable lookback via `?lookback_years=3`
7. All domain risk functions are pure — no I/O, no framework imports

**Verification:**
```bash
uv run pytest tests/unit/domain/test_risk_services.py -v
uv run pytest tests/api/test_risk_endpoints.py -v
```

---

## Task 6: Optimization Context (Vertical Slice)

**Goal:** Portfolio optimization — domain models, abstract optimizer interface, Riskfolio-Lib adapter, application service, API endpoint, tests.

**Key files:**
- `vision/domain/optimization/models.py` — `OptimizationRequest`, `OptimizationResult`, `OptimizationObjective` (enum), `WeightConstraint`
- `vision/domain/optimization/optimizer.py` — `PortfolioOptimizer` ABC
- `vision/domain/optimization/services.py` — `OptimizationService`
- `vision/infrastructure/optimization/riskfolio_adapter.py` — `RiskfolioOptimizer`
- `vision/application/optimization_service.py` — `OptimizationAppService`
- `vision/api/routers/optimization.py` — `POST /api/optimize`
- `vision/api/schemas/optimization.py` — Pydantic models
- Tests: unit, integration (riskfolio with synthetic data), API

**Acceptance criteria:**
1. All four objectives (`MIN_VOLATILITY`, `MAX_SHARPE`, `MAX_RETURN`, `RISK_PARITY`) produce valid results
2. Resulting weights sum to 1.0 (within 1e-6)
3. Weight constraints respected (no weight below min or above max)
4. `POST /api/optimize` with tickers + objective → optimal weights + metrics
5. `POST /api/optimize` with `portfolio_id` → optimizes existing portfolio's tickers
6. Integration test uses synthetic covariance matrix (no network)

**Verification:**
```bash
uv run pytest tests/unit/domain/test_optimization_models.py tests/unit/domain/test_optimization_services.py -v
uv run pytest tests/integration/test_riskfolio_adapter.py -v
uv run pytest tests/api/test_optimization_endpoints.py -v
```

---

## Task 7: Factor Decomposition Context (Vertical Slice)

**Goal:** Factor analysis — domain models, OLS regression service, Fama-French data adapter, application service, API endpoint, tests.

**Key files:**
- `vision/domain/factor/models.py` — `FactorExposure`, `FactorDecomposition`
- `vision/domain/factor/services.py` — `FactorRegressionService` (pure: `regress(portfolio_returns, factor_returns)`)
- `vision/infrastructure/market_data/factor_data_adapter.py` — Fama-French data fetcher with bundled CSV fallback
- `vision/application/factor_service.py` — `FactorAppService`
- `vision/api/routers/factors.py` — `GET /api/factors/{portfolio_id}`
- `vision/api/schemas/factor.py` — Pydantic models
- Tests: unit (synthetic data with known betas), API

**Acceptance criteria:**
1. With synthetic data (known beta=1.2 for market), regression returns beta within 0.1
2. R-squared between 0.0 and 1.0
3. All five Fama-French factors (Mkt-RF, SMB, HML, RMW, CMA) in output
4. `GET /api/factors/{portfolio_id}` → factor loadings, t-stats, R-squared, alpha
5. Bundled CSV fallback so tests never need network
6. Domain regression service is pure (numpy arrays in, dataclass out)

**Verification:**
```bash
uv run pytest tests/unit/domain/test_factor_services.py -v
uv run pytest tests/api/test_factor_endpoints.py -v
```

---

## Task 8: Cross-Context Integration + Wiring

**Goal:** Complete DI wiring, end-to-end integration test, portfolio summary endpoint combining all contexts.

**Key files:**
- `vision/api/dependencies.py` — complete DI wiring
- `vision/api/routers/portfolios.py` — add `GET /api/portfolios/{id}/summary`
- `vision/api/schemas/portfolio.py` — add `PortfolioSummaryResponse`
- `tests/api/test_integration_flow.py` — create portfolio → optimize → risk → factors → summary
- `tests/conftest.py` — shared fixtures finalized

**Acceptance criteria:**
1. Full e2e test: create, optimize, risk, factors, summary — all pass
2. `GET /api/portfolios/{id}/summary` → combined JSON (holdings, key risk metrics, factor exposures)
3. All DI is explicit in `dependencies.py` — no service locator, no global state
4. `uv run pytest` — all tests across all contexts pass

**Verification:**
```bash
uv run pytest tests/api/test_integration_flow.py -v
uv run pytest --tb=short
```

---

## Task 9: Error Handling & API Polish

**Goal:** Structured error responses, input validation edge cases, request logging, OpenAPI enrichment.

**Key files:**
- `vision/api/middleware.py` — request logging, error handling
- `vision/api/errors.py` — custom exceptions + HTTP mapping
- `vision/api/app.py` — register handlers, OpenAPI metadata
- All routers — add `response_model`, `status_code`, `summary`
- `tests/api/test_error_handling.py`

**Acceptance criteria:**
1. `GET /api/portfolios/nonexistent` → 404 with `{"error": "portfolio_not_found", ...}`
2. `POST /api/portfolios` with weights=0.5 → 422 with clear message
3. `POST /api/optimize` with empty tickers → 422
4. All endpoints have OpenAPI summaries at `/docs`
5. Request logging: method, path, status, duration
6. No raw Python exceptions leak to client

**Verification:**
```bash
uv run pytest tests/api/test_error_handling.py -v
```

---

## Task 10: CI/CD + Docker + Deploy Config

**Goal:** Dockerfile, GitHub Actions CI, GCP Cloud Run config. Container builds and runs locally.

**Key files:**
- `Dockerfile` — multi-stage build
- `.dockerignore`
- `.github/workflows/ci.yml` — lint → typecheck → test → build → deploy
- `.env.example` — document env vars
- `vision/config.py` — `Settings` class (pydantic-settings)

**Acceptance criteria:**
1. `docker build -t vision .` succeeds
2. `docker run -p 8080:8080 vision` → `GET /health` returns 200
3. GitHub Actions YAML is valid
4. `Settings` reads from env vars with sensible defaults
5. `.env.example` documents all config vars

**Verification:**
```bash
docker build -t vision .
docker run --rm -d -p 8080:8080 --name vision-test vision
curl http://localhost:8080/health
docker stop vision-test
```

---

## Checkpoints

| After Task | Validate |
|---|---|
| **1** | `uv sync && ruff check && mypy && pytest` all pass; health endpoint works |
| **2** | Market data fetches, caches, serves via API; all tests green |
| **3** | Full portfolio CRUD works e2e; domain validation enforced |
| **4+5+6+7** | Each analytics context works independently; `pytest` all green |
| **8** | Full integration flow; all contexts wired; summary endpoint works |
| **9** | Error responses structured; no exceptions leak; OpenAPI complete |
| **10** | Docker runs; CI defined; ready for GCP deployment |
