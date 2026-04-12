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

**Models:** OptimizationRequest (tickers, constraints, objective), OptimizationResult (optimal weights, metrics), FrontierPoint (return, volatility, sharpe, weights)

**Endpoints:**
- `POST /api/optimize` — Run optimization on a set of tickers, returning a single optimal portfolio for the chosen objective
- `POST /api/optimize/frontier` — Sweep the efficient frontier, returning N points and three named portfolios (min-vol, max-sharpe, equal-weight)

**Optimization objectives (via Riskfolio-Lib):**
- Minimum volatility
- Maximum Sharpe ratio
- Maximum return for a given risk level
- Risk parity (equal risk contribution)

**Constraints:**
- Min/max weight per asset
- Sector constraints (future)

**Frontier request shape:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOG"],
  "constraints": [{"ticker": "AAPL", "min_weight": 0.0, "max_weight": 0.4}],
  "lookback_years": 3,
  "points": 50
}
```

**Frontier response shape:**
```json
{
  "points": [
    {"expected_return": 0.12, "expected_volatility": 0.18, "sharpe_ratio": 0.55, "weights": {"AAPL": 0.3, ...}}
  ],
  "min_volatility": { /* FrontierPoint */ },
  "max_sharpe":     { /* FrontierPoint */ },
  "equal_weight":   { /* FrontierPoint */ }
}
```

**Rationale:** `/optimize` and `/optimize/frontier` are kept distinct because the response shapes differ structurally — overloading one endpoint with a `mode` flag would force every caller to discriminate at runtime.

**Acceptance criteria:**
- `/optimize` returns optimal weights, expected return, expected volatility, Sharpe ratio
- `/optimize/frontier` returns ≥20 points by default, with the three named portfolios always populated
- Supports at least 4 optimization objectives
- Uses historical returns (configurable lookback period, default 3 years)

### 4.3 Risk Analytics

**Models:** RiskMetrics, DrawdownAnalysis, BenchmarkComparison (tracking_error, beta, alpha, up_capture, down_capture)

**Endpoints:**
- `GET /api/risk/{portfolio_id}` — Full risk report for a portfolio
- `POST /api/risk/analyze` — Ad-hoc risk analysis for arbitrary weights
- `GET /api/portfolios/{id}/benchmark?ticker=SPY&lookback_years=3` — Portfolio vs benchmark comparison

**Metrics:**
- Annualized return, annualized volatility
- Sharpe ratio, Sortino ratio
- Maximum drawdown, drawdown duration
- Value-at-Risk (VaR) — historical and parametric (95%, 99%)
- Conditional VaR (CVaR / Expected Shortfall)
- Correlation matrix of holdings

**Benchmark metrics** (for the new endpoint):
- Tracking error (annualized)
- Beta (regression of portfolio returns on benchmark returns)
- Alpha (Jensen's alpha)
- Up-capture / down-capture ratios
- Cumulative return spread series (portfolio vs benchmark, aligned dates)

**Benchmark data source:** The existing `market_data` adapter (yfinance) already supports arbitrary tickers — SPY, QQQ, IWM, AGG and any other liquid ETF work without a new adapter. The benchmark service treats the benchmark ticker as just another `PriceHistory` fetch and runs the comparison in the application layer.

**Acceptance criteria:**
- All metrics computed from historical daily returns
- Configurable lookback period
- Results include both portfolio-level and per-holding metrics
- Benchmark endpoint accepts any ticker the `market_data` adapter can resolve, defaulting to SPY

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

## 11. Frontend

The frontend lives in `frontend/` as a separate Next.js application that consumes the FastAPI backend over HTTP. It is now in scope for v0.1 (was previously deferred to v0.3).

### 11.1 Objective

Deliver a dense, institutional-feel analytics UI for portfolio construction, risk inspection, and optimization. Visual language draws from:

- **Invesco Vision** — portfolio-vs-portfolio comparison, benchmark overlays, factor exposure panels
- **BlackRock Aladdin** — risk-first dashboards, dense tables, multi-portfolio summary grids
- **Koyfin** — clean dark theme, financial-grade charts, low chrome
- **Portfolio Visualizer** — explicit optimization workflows, efficient frontier visualization
- **Morningstar** — factor X-ray, holdings drill-down, percentile coloring

The product feel is "Bloomberg-lite": dense, monospaced numbers, dark by default, charts everywhere, minimal animations.

### 11.2 Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Framework | Next.js 16 (App Router) | SSR, file-based routing, React Server Components |
| Language | TypeScript (strict) | Type safety end-to-end |
| UI runtime | React 19 | Latest stable, concurrent features |
| Styling | Tailwind CSS v4 (vanilla, no component lib) | Direct utility classes; theme tokens via `@theme inline` |
| Charts (analytical) | Recharts | Pie, bar, factor exposures, correlation, allocation |
| Charts (time series) | TradingView Lightweight Charts | Cumulative performance, candlesticks, drawdown timelines, benchmark overlays |
| Data fetching | `fetch` + `useEffect` (v0.1) | Standardize on SWR (already in deps) in a follow-up; keep simple for now |
| Linting | ESLint + `eslint-config-next` | Default Next.js config |
| Package manager | npm | Default; lockfile committed |

> **Note:** Next.js 16 has breaking changes from older versions. Per `frontend/AGENTS.md`, consult `node_modules/next/dist/docs/` before writing routing/data-fetching code rather than relying on training-data conventions.

### 11.3 Project Structure

```
frontend/
├── src/
│   ├── app/                          # App Router pages
│   │   ├── layout.tsx                # Root layout with sidebar nav
│   │   ├── page.tsx                  # Dashboard (portfolio grid)
│   │   ├── globals.css               # Tailwind v4 + theme tokens
│   │   ├── portfolios/
│   │   │   ├── new/page.tsx          # Create portfolio
│   │   │   └── [id]/
│   │   │       ├── page.tsx          # Portfolio detail (risk, factors, allocation)
│   │   │       └── edit/page.tsx     # Edit holdings
│   │   ├── optimizer/page.tsx        # Standalone optimizer
│   │   ├── frontier/page.tsx         # NEW: efficient frontier explorer
│   │   ├── compare/page.tsx          # NEW: side-by-side portfolio comparison
│   │   └── benchmark/[id]/page.tsx   # NEW: portfolio vs benchmark overlay
│   ├── components/
│   │   ├── metric-card.tsx           # KPI tile
│   │   ├── charts/                   # NEW: chart wrappers
│   │   │   ├── performance-chart.tsx # Lightweight Charts wrapper
│   │   │   ├── allocation-pie.tsx    # Recharts pie wrapper
│   │   │   └── factor-bars.tsx       # Recharts horizontal bars
│   │   └── layout/
│   │       └── sidebar.tsx           # Extracted from layout.tsx
│   └── lib/
│       ├── api.ts                    # Typed API client (one method per endpoint)
│       ├── types.ts                  # Mirrors backend Pydantic models
│       └── chart-utils.ts            # Color palette, formatters, tooltip styles
├── public/
├── next.config.ts                    # /api/* rewrite to backend
├── package.json
└── tsconfig.json
```

### 11.4 Screens

#### Existing (already implemented)

| Route | Purpose | Key elements |
|---|---|---|
| `/` | Dashboard — list of portfolios | Grid of cards, ticker chips, holding count |
| `/portfolios/new` | Create portfolio | Form: name + ticker/weight rows |
| `/portfolios/[id]` | Portfolio detail | Risk KPI strip, performance area chart, volume bars, holdings table, allocation pie, factor bars, risk-detail panel, correlation heatmap |
| `/portfolios/[id]/edit` | Edit holdings | Same as create, prefilled |
| `/optimizer` | Standalone optimizer | Ticker chips, objective select, lookback select, results: weights chart + KPI tiles + "save as portfolio" |

#### New screens (v0.1 scope)

1. **`/frontier` — Efficient Frontier Explorer** *(Portfolio Visualizer-inspired)*
   - Inputs: tickers, lookback, constraints (min/max per asset)
   - Output: scatter plot of (volatility, return) sampled along the frontier; click a point to see weights
   - Highlight Min-Vol, Max-Sharpe, Equal-Weight portfolios
   - Backend: extend `/api/optimize` or add `/api/optimize/frontier` returning N points (out-of-scope decision tracked separately)

2. **`/compare` — Portfolio Comparison** *(Aladdin / Invesco Vision-inspired)*
   - Multi-select 2–4 portfolios
   - Side-by-side columns: KPIs (return, vol, Sharpe, max DD, VaR), factor exposures bar overlay, cumulative performance overlay
   - Diff coloring: best value in each row highlighted green, worst red

3. **`/benchmark/[id]` — Portfolio vs Benchmark** *(Koyfin-inspired)*
   - Default benchmark: SPY (configurable: QQQ, IWM, AGG)
   - Cumulative performance overlay (Lightweight Charts), tracking error, beta, up/down capture, rolling 3M return spread bar

4. **Holdings drill-down** *(Morningstar X-ray, lightweight)*
   - Inline expansion on `/portfolios/[id]` table rows: per-holding price chart (Lightweight Charts), per-holding factor exposures
   - No new route — modal or expanded row

### 11.5 Design System

Theme tokens defined once in `src/app/globals.css` via `@theme inline`. Components reference semantic class names (`bg-bg-card`, `text-text-secondary`, `text-accent`, `text-green`, `text-red`) — never raw hex.

| Token | Value | Usage |
|---|---|---|
| `bg-primary` | `#0b0e11` | Page background |
| `bg-secondary` | `#131720` | Sidebar |
| `bg-card` | `#1a1f2e` | Panels, cards |
| `bg-hover` | `#242b3d` | Row/button hover |
| `border` | `#2a3142` | Dividers, panel borders |
| `text-primary` | `#e1e4e8` | Body text |
| `text-secondary` | `#8b95a5` | Labels, metadata |
| `text-muted` | `#5a6577` | De-emphasized |
| `accent` | `#4f8ff7` | Links, primary actions, charts |
| `green` / `red` / `yellow` | `#34d399` / `#f87171` / `#fbbf24` | P&L, alerts, sharpe |
| `chart-1..5` | accent + green + red + yellow + violet | Categorical chart series |

**Typography:** Geist Sans for UI, **Geist Mono for all numbers** (prices, weights, ratios). Numbers right-aligned in tables. Percentages always to 2 decimals via `pct()`. Ratios to 2 decimals via `fmt()`.

**Layout:** Fixed 224px sidebar + scrollable main pane with `max-w-7xl` content column. Cards: `rounded-lg` + 1px border, no shadows.

### 11.6 Code Style

- **Functional components only**, hooks for state. No class components.
- **`"use client"`** at the top of every interactive page; server components only when no client hooks needed.
- **One screen per file** under `src/app/<route>/page.tsx`. Extract reusable pieces into `src/components/`.
- **API access only via `src/lib/api.ts`** — pages never call `fetch` directly.
- **Types mirror the backend** in `src/lib/types.ts`. Hand-written for v0.1; consider OpenAPI codegen later.
- **No inline hex colors** — use Tailwind theme tokens.
- **No emojis in UI** unless explicitly part of a feature.
- Two-space indent, double quotes, semicolons (Next.js default).

**Example (the canonical pattern):**

```tsx
"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RiskReport } from "@/lib/types";

export default function RiskPanel({ portfolioId }: { portfolioId: string }) {
  const [risk, setRisk] = useState<RiskReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.risk.get(portfolioId).then(setRisk).catch((e) => setError(e.message));
  }, [portfolioId]);

  if (error) return <div className="text-red text-sm">{error}</div>;
  if (!risk) return <div className="text-text-muted text-sm">Loading…</div>;

  return (
    <div className="bg-bg-card border border-border rounded-lg p-5">
      <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
        Risk Detail
      </h2>
      {/* ... */}
    </div>
  );
}
```

### 11.7 Commands

```bash
# from frontend/
npm install            # Install deps
npm run dev            # Dev server on http://localhost:3000 (proxies /api -> 127.0.0.1:8080)
npm run build          # Production build
npm run start          # Serve production build
npm run lint           # ESLint
```

The Next.js dev server proxies `/api/*` to the FastAPI backend via `next.config.ts` `rewrites()`. Both servers must be running for end-to-end work: `uv run main.py` in one terminal, `npm run dev` in another.

### 11.8 Testing Strategy

v0.1 frontend testing is **lightweight**:

- **Manual smoke testing** via dev server is the primary verification — every PR touching the frontend must be exercised in a browser, golden path + the obvious edge cases.
- **Type checking** — `tsc --noEmit` runs in CI; treat type errors as build failures.
- **Lint** — `npm run lint` in CI.
- **Unit tests** for `lib/chart-utils.ts` and any pure helpers (Vitest, added when first non-trivial helper appears).
- **Component tests** (React Testing Library) — deferred until interaction logic warrants it.
- **E2E** (Playwright) — deferred to v0.2 alongside auth.

### 11.9 Deployment

**Recommendation: deploy the frontend as a separate Cloud Run service** in the same GCP project as the backend.

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Cloud Run (separate service)** | Single GCP project (one bill, one IAM, one logging stack); same Docker workflow as backend; scales to zero; HTTPS + custom domain free | Slightly more setup than Vercel | **Chosen** |
| Vercel | Best Next.js DX; instant deploys; global CDN | Splits infra across two vendors; separate billing/secrets/auth boundary | Rejected for v0.1 |
| Cloud Run sidecar | Single container | Couples release cycles; harder to scale independently | Rejected |

**Topology:**

```
[Cloud Run: vision-frontend]  --(HTTPS, server-side fetch)-->  [Cloud Run: vision-api]
       (public)                                                   (public, will become private in v0.2)
```

In production the frontend talks to the API via an env var (`VISION_API_URL`) instead of the dev rewrite. Pages do server-side fetches where possible to keep the API origin out of the browser.

**Frontend Dockerfile** (to be added):

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "run", "start"]
```

CI extends the existing GitHub Actions workflow with a parallel `frontend` job (lint, typecheck, build) and a deploy step that pushes to Artifact Registry and updates the `vision-frontend` Cloud Run service on `main`.

### 11.10 Boundaries

**Always:**
- Route all backend calls through `src/lib/api.ts`
- Use theme tokens, never raw hex
- Use `Geist Mono` for numeric values
- Run `npm run lint` and `tsc --noEmit` before committing
- Consult `node_modules/next/dist/docs/` for Next.js 16 conventions before writing routing or data-fetching code

**Ask first:**
- Adding any UI dependency (component library, icon set, animation lib, state lib)
- Replacing `useEffect + fetch` with SWR/TanStack Query (planned, but coordinate the migration)
- Adding new top-level routes beyond those in section 11.4
- Switching deployment target away from Cloud Run
- Touching the theme palette in `globals.css`

**Never:**
- Put business logic or computation in components — the backend owns the math
- Hardcode the backend URL — use the rewrite (dev) or env var (prod)
- Inline `<style>` blocks or raw CSS files outside `globals.css`
- Commit `.next/`, `node_modules/`, or `.env*` files
- Add emojis to the UI

### 11.11 Success Criteria

- [ ] All five existing screens render without errors against a running backend
- [ ] All four new screens (frontier, compare, benchmark, holdings drill-down) implemented and manually verified
- [ ] TradingView Lightweight Charts powers all time-series visualizations
- [ ] `npm run build` succeeds with zero TypeScript or ESLint errors
- [ ] Frontend deployed to Cloud Run as `vision-frontend`, talking to `vision-api`
- [ ] CI runs lint + typecheck + build on every PR touching `frontend/`

### 11.12 Resolved Decisions

- **Efficient frontier endpoint** — added as `POST /api/optimize/frontier` (separate from `/api/optimize`). See section 4.2 for the request/response shape.
- **Benchmark data source** — reuses the existing `market_data` adapter (yfinance) with no new infrastructure. Comparison logic lives in the risk application service. See section 4.3.
- **`useEffect + fetch` → SWR migration** — deferred to v0.3. v0.1 keeps the simple pattern; do not pre-emptively introduce SWR in new screens.
- **Frontend deployment** — Cloud Run as a separate service (`vision-frontend`). Vercel was rejected to keep infra inside one GCP project. See section 11.9.

---

## 12. Future Phases (Out of Scope for v0.1)

- **v0.2**: Authentication (JWT), multi-tenant support, user-owned portfolios; lock down the API origin
- **v0.3**: Frontend polish — SWR migration, component tests (RTL), E2E (Playwright)
- **v0.4**: Scenario analysis / stress testing
- **v0.5**: PDF report generation, watchlists, additional benchmarks
- **v0.6**: Multi-asset support (bonds, commodities, international equities)
