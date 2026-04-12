# Implementation Plan: Frontend + Backend Extensions

> Scope: the new work introduced by SPEC.md sections 4.2 (frontier endpoint), 4.3 (benchmark endpoint), and 11 (frontend). The v0.1 backend foundation (CRUD, risk, optimize, factors) is already shipped — this plan does not re-cover it.

## Overview

Two backend endpoints need to land first because three of the four new frontend screens depend on them. Then the frontend is refactored to introduce a chart-component layer and TradingView Lightweight Charts, after which the four new screens can be built mostly in parallel. Finally, a frontend Dockerfile and CI extension complete the Cloud Run deployment story.

## Architecture Decisions

- **Backend before frontend** for endpoints — frontend screens are blocked on data shapes; defining the API contract first prevents thrash.
- **Vertical slices everywhere we can** — Tasks 5 and 7 each pair one new screen with the endpoint built in Phase 1; that endpoint is verified twice (backend test + frontend exercise).
- **Chart wrapper layer** introduced in Task 3 — every screen that uses Recharts or Lightweight Charts goes through `src/components/charts/*` so we can swap libraries later without touching pages.
- **TradingView Lightweight Charts is client-only** — must be rendered behind a `useEffect` or `next/dynamic({ ssr: false })`. SSR will crash otherwise. Captured as a risk.
- **Riskfolio efficient frontier**: use Riskfolio's built-in frontier computation rather than manually sweeping target returns. Faster, well-tested, single library call.
- **Benchmark comparison reuses `market_data`** — no new adapter; the benchmark ticker is just another `PriceHistory` fetch.
- **Comparison page** will fan out N parallel `GET` calls per portfolio rather than introduce a batch `/compare` endpoint. Avoids new backend surface area; can be added later if latency becomes a problem.
- **Existing `useEffect + fetch` pattern stays** for new screens (per SPEC 11.12 — SWR migration deferred to v0.3).

## Dependency Graph

```
Task 1: Efficient Frontier endpoint
       │
       ├──────────────────┐
       │                  │
Task 2: Benchmark endpoint │
       │                  │
       └────┬─────────────┘
            v
Task 3: Chart wrapper layer + Lightweight Charts
            │
            v
Task 4: API client + types + sidebar refactor
            │
   ┌────────┼────────┬──────────┐
   v        v        v          v
Task 5    Task 6   Task 7    Task 8
Frontier  Compare  Benchmark Holdings
 page      page     page    drill-down
   │        │        │          │
   └────────┴────┬───┴──────────┘
                 v
       Task 9: Frontend Dockerfile + Cloud Run config
                 │
                 v
       Task 10: CI extension for frontend
```

- **Task 1, 2** independent of each other; can run in parallel
- **Task 3** depends only on package install; technically parallel with 1/2 but logically grouped after
- **Task 4** depends on Tasks 1, 2 (needs the new endpoint shapes for typed client)
- **Tasks 5–8** all depend on Tasks 3 + 4; mutually independent → parallelizable
- **Task 9** depends on Tasks 5–8 only because we want the Docker image to ship the full app
- **Task 10** depends on Task 9

---

## Phase 1: Backend Endpoints

### Task 1: Efficient Frontier Endpoint

**Description:** Add `POST /api/optimize/frontier` that sweeps the efficient frontier and returns N points plus three named portfolios (min-vol, max-sharpe, equal-weight). Reuses existing market data fetching and Riskfolio adapter.

**Acceptance criteria:**
- [ ] `POST /api/optimize/frontier` accepts the request shape from SPEC §4.2 and returns `points`, `min_volatility`, `max_sharpe`, `equal_weight`
- [ ] Default `points=50`, configurable, capped at 200 to bound latency
- [ ] Each `FrontierPoint` has `expected_return`, `expected_volatility`, `sharpe_ratio`, `weights` (dict summing to ~1.0)
- [ ] Weight constraints from the request are honored
- [ ] Domain layer remains framework-free; Riskfolio call lives in the infrastructure adapter

**Verification:**
- [ ] `uv run pytest tests/unit/domain/test_optimization_services.py -v` (new tests for frontier sweep with synthetic 3-asset covariance)
- [ ] `uv run pytest tests/api/test_optimization_endpoints.py -v` (new test posting AAPL/MSFT/GOOG, asserting 50 points + three named)
- [ ] Manual: `curl -X POST localhost:8080/api/optimize/frontier -d '{"tickers":["AAPL","MSFT","GOOG"]}' -H 'content-type: application/json'`

**Dependencies:** None (extends existing optimization stack)

**Files likely touched:**
- `vision/domain/optimization/models.py` — add `FrontierPoint`, `FrontierRequest`, `FrontierResult` dataclasses
- `vision/domain/optimization/optimizer.py` — add abstract `compute_frontier` method
- `vision/infrastructure/optimization/riskfolio_adapter.py` — implement frontier sweep via Riskfolio
- `vision/application/optimization_service.py` — `compute_frontier(request)` orchestration
- `vision/api/routers/optimization.py` — new route + Pydantic schemas
- `tests/unit/domain/test_optimization_services.py` and `tests/api/test_optimization_endpoints.py`

**Estimated scope:** Medium (5–6 files)

---

### Task 2: Benchmark Comparison Endpoint

**Description:** Add `GET /api/portfolios/{id}/benchmark?ticker=SPY&lookback_years=3` returning `BenchmarkComparison` (tracking error, beta, alpha, up/down capture, cumulative return spread series).

**Acceptance criteria:**
- [ ] Endpoint accepts any ticker the `market_data` adapter resolves; defaults to SPY
- [ ] Returns `tracking_error`, `beta`, `alpha`, `up_capture`, `down_capture`, and a `spread_series` of `{date, portfolio_cum, benchmark_cum, spread}`
- [ ] Aligns portfolio returns and benchmark returns by intersection of dates before computing
- [ ] Pure-domain regression function (numpy in, dataclass out); reuses existing `RiskCalculationService` style
- [ ] Returns 404 when portfolio not found, 422 when benchmark ticker unresolvable

**Verification:**
- [ ] `uv run pytest tests/unit/domain/test_risk_services.py -v` (new test: synthetic returns with known beta=1.2 → assert recovered beta within 0.05)
- [ ] `uv run pytest tests/api/test_risk_endpoints.py -v` (new test for benchmark endpoint)
- [ ] Manual: `curl 'localhost:8080/api/portfolios/<id>/benchmark?ticker=SPY'`

**Dependencies:** None

**Files likely touched:**
- `vision/domain/risk/models.py` — add `BenchmarkComparison`, `SpreadPoint`
- `vision/domain/risk/services.py` — add `compute_benchmark_comparison(portfolio_returns, benchmark_returns)` pure function
- `vision/application/risk_service.py` — `compare_to_benchmark(portfolio_id, benchmark_ticker, lookback_years)`
- `vision/api/routers/risk.py` — register on the existing risk router or `portfolios.py` (decision: keep on `risk.py` to colocate with other risk endpoints, but mount under `/api/portfolios/{id}/benchmark` via `APIRouter` prefix)
- `tests/unit/domain/test_risk_services.py` and `tests/api/test_risk_endpoints.py`

**Estimated scope:** Medium (5 files)

---

### Checkpoint: Backend Endpoints

- [ ] `uv run pytest` — all tests pass
- [ ] `uv run ruff check . && uv run mypy vision/` — clean
- [ ] Both new endpoints visible in `/docs` with correct schemas
- [ ] Manual curl against both works
- [ ] Human review of endpoint shapes before frontend consumes them

---

## Phase 2: Frontend Foundation

### Task 3: Chart Wrapper Layer + TradingView Lightweight Charts

**Description:** Add `lightweight-charts` to dependencies. Create a `src/components/charts/` directory and extract the existing inline Recharts usage into reusable wrappers. Add a Lightweight Charts wrapper for time-series rendering with SSR-safe initialization.

**Acceptance criteria:**
- [ ] `lightweight-charts` installed and committed in `package-lock.json`
- [ ] `PerformanceChart` component renders a Lightweight Charts area series; mounts only on the client (uses `useEffect` + ref)
- [ ] `AllocationPie` component encapsulates the existing pie-chart usage from `portfolios/[id]/page.tsx`
- [ ] `FactorBars` component encapsulates the horizontal factor-exposure bar chart
- [ ] `portfolios/[id]/page.tsx` updated to use the three new components (no behavior change)
- [ ] All chart components accept theme tokens via Tailwind classes; no hardcoded hex outside `chart-utils.ts`
- [ ] `npm run build` succeeds; no SSR errors

**Verification:**
- [ ] `cd frontend && npm run build` — clean
- [ ] `cd frontend && npm run lint` — clean
- [ ] Manual: visit `/portfolios/<id>` in dev — performance chart renders identically (or visually upgraded), allocation pie + factor bars unchanged

**Dependencies:** None

**Files likely touched:**
- `frontend/package.json`, `frontend/package-lock.json`
- `frontend/src/components/charts/performance-chart.tsx` (new — Lightweight Charts wrapper)
- `frontend/src/components/charts/allocation-pie.tsx` (new — Recharts wrapper)
- `frontend/src/components/charts/factor-bars.tsx` (new — Recharts wrapper)
- `frontend/src/app/portfolios/[id]/page.tsx` (refactor to consume wrappers)

**Estimated scope:** Medium (5 files)

---

### Task 4: API Client + Types + Sidebar Refactor

**Description:** Extend `src/lib/api.ts` and `src/lib/types.ts` with the new endpoint shapes from Tasks 1 and 2. Extract sidebar nav from `layout.tsx` into its own component to make adding new nav items cleaner for Tasks 5–8.

**Acceptance criteria:**
- [ ] `api.optimize.frontier(req)` exists and is fully typed against `FrontierResult`
- [ ] `api.risk.benchmark(portfolioId, ticker?, lookbackYears?)` exists
- [ ] `types.ts` has `FrontierPoint`, `FrontierRequest`, `FrontierResult`, `BenchmarkComparison`, `SpreadPoint`
- [ ] `Sidebar` component lives in `src/components/layout/sidebar.tsx`; `layout.tsx` imports it
- [ ] Nav items defined in a single `navItems` array; `Sidebar` renders them
- [ ] `tsc --noEmit` clean
- [ ] All existing pages still render

**Verification:**
- [ ] `cd frontend && npm run build` — clean
- [ ] Manual: every existing route loads, sidebar nav still works

**Dependencies:** Tasks 1, 2 (needs the response shapes to type correctly)

**Files likely touched:**
- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`
- `frontend/src/components/layout/sidebar.tsx` (new)
- `frontend/src/app/layout.tsx`

**Estimated scope:** Small (4 files)

---

### Checkpoint: Foundation

- [ ] All existing screens still work
- [ ] `npm run build` succeeds
- [ ] Chart wrappers ready, API client ready — Tasks 5–8 can run in parallel

---

## Phase 3: New Screens (Parallelizable)

### Task 5: `/frontier` — Efficient Frontier Explorer

**Description:** New page where the user enters tickers + constraints + lookback, calls `api.optimize.frontier`, and visualizes the result as a scatter chart in (volatility, return) space with the three named portfolios highlighted. Clicking a point shows its weights.

**Acceptance criteria:**
- [ ] Inputs: ticker chips (reuse pattern from `/optimizer`), lookback select, points slider (10–100), per-ticker min/max constraint rows
- [ ] On submit, calls `api.optimize.frontier` and renders a Recharts scatter (volatility on X, return on Y)
- [ ] Min-vol, max-sharpe, equal-weight points styled distinctly (different colors + labels)
- [ ] Selecting a point shows its weights table on the right
- [ ] Loading + error states match the existing pattern
- [ ] New nav item "Frontier" added to sidebar

**Verification:**
- [ ] Manual: enter `AAPL, MSFT, GOOG, AMZN`, lookback 3y, submit → 50 points appear in scatter; the three named portfolios highlighted
- [ ] Manual: click min-vol point → weights table shows weights summing to ~100%
- [ ] Manual: enter only 1 ticker → error message
- [ ] `npm run build` clean

**Dependencies:** Tasks 1, 3, 4

**Files likely touched:**
- `frontend/src/app/frontier/page.tsx` (new)
- `frontend/src/components/charts/frontier-scatter.tsx` (new — Recharts scatter wrapper)
- `frontend/src/components/layout/sidebar.tsx` (add nav item)

**Estimated scope:** Small-Medium (3 files)

---

### Task 6: `/compare` — Portfolio Comparison

**Description:** Multi-select 2–4 portfolios. Render side-by-side columns: KPI rows (return, vol, Sharpe, max DD, VaR), factor exposure bars overlaid, cumulative performance overlaid on one Lightweight Charts instance. Best/worst values per row colored green/red.

**Acceptance criteria:**
- [ ] Multi-select dropdown lists existing portfolios (uses `api.portfolios.list`)
- [ ] Per portfolio: parallel fetches for `summary`, `risk`, `factors`, `performance`
- [ ] KPI table: rows = metrics, columns = portfolios; best in row colored green, worst red
- [ ] Factor exposure: grouped horizontal bar chart with one series per portfolio
- [ ] Cumulative performance: one Lightweight Charts area chart with N overlaid series
- [ ] Disabled "Compare" button until ≥2 portfolios selected
- [ ] New nav item "Compare" in sidebar

**Verification:**
- [ ] Manual: create 2 portfolios via UI, navigate to `/compare`, select both, verify columns + chart overlay render
- [ ] Manual: try with 4 portfolios — chart legend readable, table fits
- [ ] `npm run build` clean

**Dependencies:** Tasks 3, 4

**Files likely touched:**
- `frontend/src/app/compare/page.tsx` (new)
- `frontend/src/components/layout/sidebar.tsx` (add nav item)

**Estimated scope:** Medium (2–3 files)

---

### Task 7: `/benchmark/[id]` — Portfolio vs Benchmark

**Description:** New page for a single portfolio comparing it against a configurable benchmark (default SPY). Shows beta, alpha, tracking error, up/down capture in a KPI strip, plus an overlaid Lightweight Charts cumulative-return chart and a rolling spread bar chart. Linked from the portfolio detail page.

**Acceptance criteria:**
- [ ] Reads `[id]` from URL, fetches `api.risk.benchmark(id, ticker)`
- [ ] Benchmark selector: SPY (default), QQQ, IWM, AGG
- [ ] KPI strip: beta, alpha (annualized), tracking error, up-capture, down-capture
- [ ] Cumulative-return overlay (portfolio vs benchmark) via `PerformanceChart` (Lightweight Charts)
- [ ] Spread bar chart underneath via Recharts
- [ ] "Benchmark" link added to the portfolio detail page header
- [ ] Loading + error states

**Verification:**
- [ ] Manual: from `/portfolios/<id>`, click "Benchmark" → page loads with SPY by default
- [ ] Manual: switch benchmark to QQQ → metrics + charts update
- [ ] `npm run build` clean

**Dependencies:** Tasks 2, 3, 4

**Files likely touched:**
- `frontend/src/app/benchmark/[id]/page.tsx` (new)
- `frontend/src/app/portfolios/[id]/page.tsx` (add link in header)
- `frontend/src/components/charts/spread-bars.tsx` (new — Recharts spread wrapper)

**Estimated scope:** Medium (3 files)

---

### Task 8: Holdings Drill-Down on Portfolio Detail

**Description:** Make rows in the holdings table on `/portfolios/[id]` expandable. Expanded row shows a per-ticker price chart (Lightweight Charts) using the existing `/api/market-data/{ticker}/prices` endpoint. No new backend.

**Acceptance criteria:**
- [ ] Each holdings-table row has a chevron toggle
- [ ] Clicking toggles an expansion below the row containing a price chart for that ticker
- [ ] Price chart spans 3 years by default
- [ ] Only one row expanded at a time (or multiple — pick whichever is simpler)
- [ ] Loads price data lazily on expand
- [ ] Loading + error states inline in the expansion

**Verification:**
- [ ] Manual: open `/portfolios/<id>`, click a holding row → price chart appears
- [ ] Manual: collapse, expand a different row → that ticker loads
- [ ] `npm run build` clean

**Dependencies:** Tasks 3, 4

**Files likely touched:**
- `frontend/src/app/portfolios/[id]/page.tsx`
- `frontend/src/components/holdings-row.tsx` (new — extract row + expansion logic)

**Estimated scope:** Small (2 files)

---

### Checkpoint: All Screens

- [ ] All four new screens render against a running backend
- [ ] Sidebar nav contains: Dashboard, New Portfolio, Optimizer, Frontier, Compare
- [ ] `npm run build` and `npm run lint` clean
- [ ] Manual smoke test of every screen (golden path + obvious edge cases)
- [ ] Human review before deploying

---

## Phase 4: Production

### Task 9: Frontend Dockerfile + Cloud Run Config

**Description:** Add a multi-stage `frontend/Dockerfile` (per SPEC §11.9), an env-driven API URL, and a `.dockerignore`. Verify the container runs locally and can talk to a separately running backend.

**Acceptance criteria:**
- [ ] `frontend/Dockerfile` builds the production Next.js app in three stages (deps → build → runtime)
- [ ] `VISION_API_URL` env var read at build/runtime; defaults to `http://127.0.0.1:8080` for local dev
- [ ] `next.config.ts` rewrite uses the env var so dev still proxies correctly
- [ ] `frontend/.dockerignore` excludes `node_modules`, `.next`, `.git`, env files
- [ ] `docker build -t vision-frontend frontend/` succeeds
- [ ] `docker run -p 3000:3000 -e VISION_API_URL=http://host.docker.internal:8080 vision-frontend` serves the app at `localhost:3000`

**Verification:**
- [ ] `docker build -t vision-frontend frontend/`
- [ ] Run backend locally (`uv run main.py`); run frontend container; visit `http://localhost:3000` and confirm dashboard loads
- [ ] `docker stop` cleans up

**Dependencies:** Tasks 5–8

**Files likely touched:**
- `frontend/Dockerfile` (new)
- `frontend/.dockerignore` (new)
- `frontend/next.config.ts`
- `frontend/src/lib/api.ts` (read env var)

**Estimated scope:** Small-Medium (4 files)

---

### Task 10: CI Extension for Frontend

**Description:** Add a `frontend` job to `.github/workflows/ci.yml` that installs Node, runs lint + typecheck + build, and (on `main`) builds and pushes the Docker image to Artifact Registry, then updates the `vision-frontend` Cloud Run service.

**Acceptance criteria:**
- [ ] `frontend` job runs in parallel with the existing backend job
- [ ] Steps: checkout → setup Node 22 → `npm ci` → `npm run lint` → `tsc --noEmit` → `npm run build`
- [ ] Deploy step gated on `github.ref == 'refs/heads/main'`
- [ ] Deploy: `docker build` → push to Artifact Registry → `gcloud run deploy vision-frontend`
- [ ] Workflow YAML validates (`actionlint` or GitHub web validator)
- [ ] Cache `node_modules` for faster CI runs

**Verification:**
- [ ] Push the branch and confirm the new job appears + passes
- [ ] On a `main` merge, confirm the deploy step runs and the Cloud Run revision updates

**Dependencies:** Task 9

**Files likely touched:**
- `.github/workflows/ci.yml`

**Estimated scope:** XS (1 file)

---

### Checkpoint: Production

- [ ] CI green on a feature branch
- [ ] Frontend deployed to Cloud Run, talking to backend Cloud Run service
- [ ] All SPEC §11.11 success criteria checked off
- [ ] Spec marked as v0.1 complete

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Lightweight Charts crashes during SSR | High | Render only inside `useEffect`; gate with a `mounted` flag or use `next/dynamic({ ssr: false })`. Verify in Task 3. |
| Riskfolio frontier sweep is slow for large N | Medium | Cap `points` at 200 server-side; use Riskfolio's native frontier function rather than manual sweep. Add a perf test in Task 1. |
| Benchmark date alignment loses too many days when portfolio holdings have different histories | Medium | Intersect dates explicitly in the application service; reject windows shorter than 60 days with a clear 422. |
| Next.js 16 breaking changes vs training-data conventions | Medium | `frontend/AGENTS.md` already flags this. Before writing routing code in Tasks 5/7/8, consult `node_modules/next/dist/docs/`. |
| Comparison page latency from N×4 parallel calls | Low | Acceptable for v0.1 (small N, local backend). If it bites, add `POST /api/portfolios/compare` later. |
| Cloud Run cold-start on a Node container | Low | Set min-instances=0 for v0.1 (cost over latency); revisit for v0.2 if user-facing. |
| `host.docker.internal` doesn't work on Linux for local Docker testing | Low | Document `--add-host=host.docker.internal:host-gateway` in Task 9 verification. |

## Open Questions

- **Frontier sweep API in Riskfolio**: confirm the exact function name and signature during Task 1 (`Portfolio.efficient_frontier()` vs `riskfolio.RiskFunctions`). Verify before writing the test.
- **Spread series cadence** for the benchmark endpoint: daily by default, but should we down-sample for >5 year windows? Defer until we see chart density in Task 7.
- **GCP project + Artifact Registry setup**: Task 10 assumes a project exists. If it doesn't, treat that as a one-time prerequisite outside this plan.
