# Vision — Portfolio Construction & Analytics Platform

## 1. Objective

Build a SaaS portfolio construction and analytics platform inspired by Invesco Vision. The platform enables users to construct portfolios, run mean-variance optimization, analyze risk metrics, and decompose factor exposures — starting with US equities and ETFs.

**Target users:** Financial advisors, portfolio managers, and sophisticated retail investors.

**v0.1 goal:** A working API-driven platform with three core modules — portfolio construction & optimization, risk analytics, and factor decomposition — backed by SQLite and sourcing market data from yfinance.

---

## 2. Architecture

### UI Recommendation: FastAPI + Next.js

For a SaaS product, **FastAPI (backend) + Next.js (frontend)** is the right choice:

- **FastAPI** — async Python, auto-generated OpenAPI docs, dependency injection fits naturally with DDD/SOLID, excellent for financial computation APIs.
- **Next.js** — industry-standard SaaS frontend, SSR for SEO/performance, component ecosystem for charts (Recharts, Plotly.js, Lightweight Charts).
- **Why not Streamlit/Dash** — No multi-tenant auth, no custom URL routing, limited layout control, not suitable for a production SaaS with paying users.

### Minimum Implementation Strategy

Phase 1 (this spec): **Backend API only**. Build the full domain layer, application services, and REST API with FastAPI. Test via OpenAPI docs and automated tests. No frontend yet.

Phase 2 (future): Next.js frontend consuming the API.

This lets us validate the domain model, optimization logic, and data pipeline before investing in UI.

### Domain-Driven Design Structure

```
vision/
├── domain/                  # Core business logic (no framework dependencies)
│   ├── portfolio/           # Portfolio aggregate
│   │   ├── models.py        # Portfolio, Holding, Weight entities
│   │   ├── repository.py    # Abstract repository interface
│   │   └── services.py      # Portfolio construction & validation
│   ├── optimization/        # Optimization bounded context
│   │   ├── models.py        # OptimizationRequest, OptimizationResult, Constraints
│   │   ├── optimizer.py     # Abstract optimizer interface
│   │   └── services.py      # Optimization orchestration
│   ├── risk/                # Risk analytics bounded context
│   │   ├── models.py        # RiskMetrics, DrawdownAnalysis, VaRResult
│   │   └── services.py      # Risk calculation logic
│   ├── factor/              # Factor decomposition bounded context
│   │   ├── models.py        # FactorExposure, FactorDecomposition
│   │   └── services.py      # Factor regression logic
│   └── market_data/         # Market data bounded context
│       ├── models.py        # PriceHistory, AssetInfo
│       ├── repository.py    # Abstract market data interface
│       └── services.py      # Data retrieval & caching
├── infrastructure/          # Framework & external adapters
│   ├── database/
│   │   ├── connection.py    # SQLite connection management
│   │   ├── models.py        # SQLAlchemy/SQL table definitions
│   │   └── repositories.py  # Concrete repository implementations
│   ├── market_data/
│   │   └── yfinance_adapter.py  # yfinance implementation of market data repo
│   └── optimization/
│       └── riskfolio_adapter.py # Riskfolio-Lib optimizer implementation
├── application/             # Use cases / application services
│   ├── portfolio_service.py # Orchestrates portfolio CRUD + optimization
│   ├── risk_service.py      # Orchestrates risk analysis
│   └── factor_service.py    # Orchestrates factor decomposition
├── api/                     # FastAPI HTTP layer
│   ├── app.py               # FastAPI app factory
│   ├── dependencies.py      # DI container / dependency wiring
│   └── routers/
│       ├── portfolios.py    # /api/portfolios endpoints
│       ├── optimization.py  # /api/optimize endpoints
│       ├── risk.py          # /api/risk endpoints
│       └── factors.py       # /api/factors endpoints
└── tests/
    ├── unit/
    │   ├── domain/          # Pure domain logic tests
    │   └── application/     # Application service tests (mocked infra)
    ├── integration/
    │   ├── test_database.py # Repository + SQLite tests
    │   └── test_yfinance.py # Market data adapter tests
    └── api/
        └── test_endpoints.py # FastAPI TestClient tests
```

### Key Design Principles

- **SOLID**: Each class has one reason to change. Domain depends on nothing; infrastructure depends on domain abstractions.
- **DDD**: Bounded contexts (portfolio, optimization, risk, factor, market_data) with clear aggregate roots. Domain models are plain Python dataclasses — no ORM leakage.
- **Dependency Inversion**: Domain defines abstract repository interfaces; infrastructure provides concrete implementations. Swapping SQLite for Postgres or yfinance for a paid API requires zero domain changes.
- **TDD**: Tests written before implementation. Domain logic has 100% unit test coverage. Integration tests validate adapters.

---

## 3. Commands

```bash
# Development
uv run main.py                    # Start FastAPI dev server
uv run pytest                     # Run all tests
uv run pytest tests/unit          # Run unit tests only
uv run pytest tests/integration   # Run integration tests only
uv run pytest --cov=vision        # Run tests with coverage

# Dependencies
uv add <package>                  # Add a dependency
uv sync                           # Sync environment

# Database
uv run python -m vision.infrastructure.database.connection init  # Initialize SQLite DB

# Code quality
uv run ruff check .               # Lint
uv run ruff format .              # Format
uv run mypy vision/               # Type check
```

---

## 4. Core Features (v0.1 Scope)

### 4.1 Portfolio Construction

**Entities:** Portfolio, Holding (ticker + weight + shares)

**Endpoints:**
- `POST /api/portfolios` — Create a portfolio with name and holdings
- `GET /api/portfolios` — List all portfolios
- `GET /api/portfolios/{id}` — Get portfolio details with current market values
- `PUT /api/portfolios/{id}` — Update holdings/weights
- `DELETE /api/portfolios/{id}` — Delete a portfolio

**Acceptance criteria:**
- Weights must sum to 1.0 (or 100%)
- Tickers validated against yfinance before saving
- Portfolio persisted to SQLite

### 4.2 Portfolio Optimization

**Models:** OptimizationRequest (tickers, constraints, objective), OptimizationResult (optimal weights, metrics)

**Endpoints:**
- `POST /api/optimize` — Run optimization on a set of tickers or existing portfolio

**Optimization objectives (via Riskfolio-Lib):**
- Minimum volatility
- Maximum Sharpe ratio
- Maximum return for a given risk level
- Risk parity (equal risk contribution)

**Constraints:**
- Min/max weight per asset
- Sector constraints (future)

**Acceptance criteria:**
- Returns optimal weights, expected return, expected volatility, Sharpe ratio
- Supports at least 4 optimization objectives
- Uses historical returns (configurable lookback period, default 3 years)

### 4.3 Risk Analytics

**Models:** RiskMetrics, DrawdownAnalysis

**Endpoints:**
- `GET /api/risk/{portfolio_id}` — Full risk report for a portfolio
- `POST /api/risk/analyze` — Ad-hoc risk analysis for arbitrary weights

**Metrics:**
- Annualized return, annualized volatility
- Sharpe ratio, Sortino ratio
- Maximum drawdown, drawdown duration
- Value-at-Risk (VaR) — historical and parametric (95%, 99%)
- Conditional VaR (CVaR / Expected Shortfall)
- Correlation matrix of holdings

**Acceptance criteria:**
- All metrics computed from historical daily returns
- Configurable lookback period
- Results include both portfolio-level and per-holding metrics

### 4.4 Factor Decomposition

**Models:** FactorExposure, FactorDecomposition

**Endpoints:**
- `GET /api/factors/{portfolio_id}` — Factor exposures for a portfolio

**Factor model:**
- Fama-French 5-factor model (Market, SMB, HML, RMW, CMA)
- Regression of portfolio returns against factor returns
- Output: factor betas, R-squared, alpha, residual risk

**Data source:** Kenneth French data library (via `pandas-datareader` or direct download)

**Acceptance criteria:**
- Returns factor loadings (betas) with t-statistics
- Returns R-squared and alpha
- Rolling factor exposure over configurable window (optional in v0.1)

---

## 5. Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.13+ | Project requirement |
| Package manager | uv | Project requirement |
| Web framework | FastAPI | Async, auto-docs, DI-friendly |
| Database | SQLite (via aiosqlite) | Lightweight, specified requirement |
| ORM | SQLAlchemy 2.0 (Core, not ORM) | SQL builder without domain model pollution |
| Optimization | Riskfolio-Lib | Most comprehensive portfolio optimization library |
| Risk metrics | empyrical + numpy | Lightweight, well-tested |
| Factor model | statsmodels | Standard for OLS regression |
| Market data | yfinance | Free, specified requirement |
| Validation | Pydantic v2 | FastAPI native, strict validation |
| Testing | pytest + pytest-cov | Standard, with coverage tracking |
| Linting | ruff | Fast, replaces flake8 + isort + black |
| Type checking | mypy (strict) | Catches bugs early, fits SOLID approach |

---

## 6. Code Style

- **Type hints everywhere** — all function signatures fully annotated, `mypy --strict` clean.
- **Pydantic for API models**, plain `dataclasses` for domain models — domain stays framework-free.
- **No business logic in API layer** — routers call application services, application services call domain services.
- **Repository pattern** — abstract base classes in domain, concrete implementations in infrastructure.
- **Immutable domain models** — use `frozen=True` dataclasses where possible.
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants.
- **No wildcard imports.** Explicit imports only.
- **Max line length**: 88 (ruff default).

---

## 7. Testing Strategy

### TDD Workflow
1. Write a failing test for the behavior
2. Write the minimum code to make it pass
3. Refactor while keeping tests green

### Test Layers

| Layer | What | Mocked? | Speed |
|---|---|---|---|
| **Unit (domain)** | Domain models, services, calculations | No mocks needed — pure logic | < 1s |
| **Unit (application)** | Application service orchestration | Repositories & adapters mocked | < 1s |
| **Integration (database)** | Repository implementations | Real SQLite (in-memory) | < 5s |
| **Integration (market data)** | yfinance adapter | Real API calls (marked slow) | Network |
| **API** | Endpoint request/response | Full app with in-memory SQLite | < 5s |

### Coverage Target
- Domain layer: 100%
- Application layer: 95%+
- API layer: 90%+
- Infrastructure: 80%+

### Test Markers
```python
@pytest.mark.unit        # Fast, no I/O
@pytest.mark.integration # Uses real database or network
@pytest.mark.slow        # Network calls (yfinance)
```

---

## 8. Boundaries

### Always Do
- Validate all inputs at the API boundary with Pydantic
- Keep domain models free of framework dependencies
- Write tests before implementation
- Use dependency injection — no hard-coded dependencies in domain/application layers
- Return proper HTTP status codes and error responses
- Cache yfinance data in SQLite to avoid redundant API calls

### Ask First
- Adding new bounded contexts beyond the four defined
- Changing the database from SQLite
- Adding authentication/authorization (planned for v0.2)
- Adding WebSocket support for real-time data
- Integrating paid data sources

### Never Do
- Put business logic in the API layer or infrastructure layer
- Let domain models depend on SQLAlchemy, FastAPI, or any framework
- Store secrets in code
- Skip tests for domain logic
- Use `SELECT *` or unparameterized SQL
- Return raw exceptions to the API client

---

## 9. Infrastructure & Deployment

### Source Control: GitHub

- **Repository:** GitHub (private repo)
- **Branch strategy:** `main` (production) + feature branches with PRs
- **CI/CD:** GitHub Actions

### GitHub Actions Pipeline

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]

jobs:
  test:
    - Checkout + setup Python 3.13 + uv
    - uv sync
    - uv run ruff check .
    - uv run ruff format --check .
    - uv run mypy vision/
    - uv run pytest --cov=vision

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    - Build Docker image
    - Push to Artifact Registry
    - Deploy to Cloud Run
```

### GCP Deployment: Cloud Run

**Why Cloud Run:**
- Serverless — scales to zero, no infra management
- Containerized — same image locally and in production
- Pay-per-request — ideal for early-stage SaaS with variable traffic
- Built-in HTTPS, custom domains, IAM integration
- Handles concurrent requests well for compute-heavy optimization endpoints

**GCP Services Used:**

| Service | Purpose |
|---|---|
| **Cloud Run** | Hosts the FastAPI container |
| **Artifact Registry** | Stores Docker images |
| **Cloud Storage** | SQLite DB file persistence (mounted via GCS FUSE) |
| **Secret Manager** | API keys, future auth secrets |
| **Cloud Logging** | Structured logging from the app |
| **Cloud Monitoring** | Health checks, latency, error rate alerts |

**Note on SQLite + Cloud Run:** Cloud Run instances are stateless. SQLite works for v0.1 by mounting a Cloud Storage bucket via GCS FUSE for persistence. For v0.2+, migrate to Cloud SQL (PostgreSQL) — the repository pattern makes this a single-adapter swap with zero domain changes.

### Dockerfile

```dockerfile
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY vision/ vision/
COPY main.py .

EXPOSE 8080
CMD ["uv", "run", "uvicorn", "vision.api.app:create_app", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Configuration

```bash
# .env (local development)
VISION_ENV=development
VISION_DB_PATH=./data/vision.db
VISION_LOG_LEVEL=debug

# Cloud Run (set via Secret Manager / env vars)
VISION_ENV=production
VISION_DB_PATH=/mnt/gcs/vision.db
VISION_LOG_LEVEL=info
```

### Project Structure (updated with infra files)

```
vision/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI/CD
├── Dockerfile                   # Container definition
├── .dockerignore
├── vision/                      # Application code (unchanged)
│   ├── domain/
│   ├── infrastructure/
│   ├── application/
│   └── api/
├── tests/
├── pyproject.toml
├── main.py
└── SPEC.md
```

---

## 10. Implementation Order

Build in this sequence — each step is independently testable and shippable:

1. **Project scaffolding** — directory structure, dependencies, pytest config, ruff/mypy config
2. **CI/CD setup** — Dockerfile, GitHub Actions workflow, GCP project + Cloud Run service
3. **Domain: Market data** — models + abstract repo + yfinance adapter + caching
4. **Domain: Portfolio** — models + repo interface + SQLite repo + CRUD endpoints
5. **Domain: Risk analytics** — risk calculation services + API endpoints
6. **Domain: Optimization** — Riskfolio-Lib adapter + optimization service + API endpoints
7. **Domain: Factor decomposition** — factor regression service + API endpoints
8. **Integration** — wire everything together, end-to-end tests, deploy to Cloud Run

---

## 11. Future Phases (Out of Scope for v0.1)

- **v0.2**: Authentication (JWT), multi-tenant support, user-owned portfolios
- **v0.3**: Next.js frontend with interactive charts
- **v0.4**: Scenario analysis / stress testing
- **v0.5**: PDF report generation, benchmarking against indices
- **v0.6**: Multi-asset support (bonds, commodities, international equities)
