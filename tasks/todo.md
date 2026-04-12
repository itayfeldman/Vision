# Vision — Task List

> Frontend + backend extensions per SPEC.md §4.2, §4.3, §11. The v0.1 backend foundation is shipped.

## Phase 1: Backend Endpoints
- [x] **Task 1:** Efficient Frontier endpoint — `POST /api/optimize/frontier`
  - Domain models, Riskfolio frontier sweep, application service, route, tests
  - _Blocks: Task 4, Task 5_
- [x] **Task 2:** Benchmark Comparison endpoint — `GET /api/portfolios/{id}/benchmark`
  - Domain `BenchmarkComparison`, regression service, app service, route, tests
  - _Blocks: Task 4, Task 7_

### Checkpoint: Backend Endpoints
- [x] All tests pass; ruff + mypy clean
- [x] Both endpoints visible in `/docs` with correct schemas
- [ ] Manual curl verification of both
- [ ] Human review of endpoint shapes before frontend consumes them

## Phase 2: Frontend Foundation
- [x] **Task 3:** Chart wrapper layer + TradingView Lightweight Charts
  - Install `lightweight-charts`; create `PerformanceChart`, `AllocationPie`, `FactorBars`; refactor portfolio detail page to use them
  - _Depends on: none_
- [x] **Task 4:** API client + types + sidebar refactor
  - Add `api.optimize.frontier`, `api.risk.benchmark`; new types; extract `Sidebar` component
  - _Depends on: Tasks 1, 2_

### Checkpoint: Foundation
- [x] Existing screens still work
- [x] `npm run build` succeeds
- [x] Tasks 5–8 can now run in parallel

## Phase 3: New Screens (parallelizable)
- [x] **Task 5:** `/frontier` page — efficient frontier explorer
  - Inputs + scatter chart + named-portfolio highlights + weights table + sidebar nav
  - _Depends on: Tasks 1, 3, 4_
- [x] **Task 6:** `/compare` page — multi-portfolio comparison
  - Multi-select, KPI grid with best/worst coloring, factor + performance overlays, sidebar nav
  - _Depends on: Tasks 3, 4_
- [x] **Task 7:** `/benchmark/[id]` page — portfolio vs benchmark
  - Benchmark selector, KPI strip, cumulative-return overlay, spread chart, link from detail page
  - _Depends on: Tasks 2, 3, 4_
- [x] **Task 8:** Holdings drill-down on portfolio detail
  - Expandable rows with per-ticker price chart (Lightweight Charts)
  - _Depends on: Tasks 3, 4_

### Checkpoint: All Screens
- [ ] All four new screens render against running backend
- [x] Sidebar contains: Dashboard, New Portfolio, Optimizer, Frontier, Compare
- [x] `npm run build` and `npm run lint` clean
- [ ] Manual smoke of every screen
- [ ] Human review before deploying

## Phase 4: Production
- [x] **Task 9:** Frontend Dockerfile + Cloud Run config
  - Multi-stage Dockerfile, env-driven `VISION_API_URL`, `.dockerignore`, local container verified
  - _Depends on: Tasks 5–8_
  - _Note: local `docker build` not verified (daemon unavailable in session); CI smoke-test covers it_
- [x] **Task 10:** CI extension for frontend
  - New `frontend` job in `.github/workflows/ci.yml` (lint + typecheck + build + deploy on `main`)
  - _Depends on: Task 9_
  - _Note: gcloud deploy deferred to match existing backend `docker` job pattern_

### Checkpoint: Production
- [ ] CI green on feature branch
- [ ] Frontend deployed to Cloud Run, talking to backend
- [ ] SPEC §11.11 success criteria all checked

## Phase 5: Review Follow-Ups

> From the five-axis review of commits d2b6ec4..ca7e93e.

### Critical
- [x] **Task 11:** Benchmark endpoint silently drops holdings with no data
  - `vision/application/risk_service.py:158-187` — holdings skipped from `frame` while weight remains nominally applied; builds non-unit-sum portfolio with no warning
  - Fix: reject when any holding is missing, or re-normalize and surface it; add test
- [x] **Task 12:** `_compute_performance` assumes all tickers share a trading calendar
  - `vision/application/risk_service.py:120-134` — sums returns index-wise against one arbitrary ticker's dates; mismatched calendars produce wrong portfolio returns; `volumes[1:min_len+1]` has the same assumption
  - Fix: align via `pd.DataFrame` + `dropna` like `compare_to_benchmark`; add test with mismatched-length series
- [x] **Task 13:** Holdings drill-down unmount / rapid-click race
  - `frontend/src/components/holdings-row.tsx:39-51` — no `AbortController`; `setPrices`/`setLoading` fire on stale/unmounted rows; toggling many holdings queues orphan requests
  - Fix: attach `AbortSignal` scoped to the row; cancel on unmount / re-fetch; guard state setters behind an `alive` ref

### Important
- [x] **Task 14:** Frontier alignment uses `[:min_len]` instead of date intersection
  - `vision/application/optimization_service.py:42-44` — trims from the end, comparing AAPL's oldest 600 days against a newer ticker's full 600 days
  - Fix: align on dates via `pd.DataFrame`; add test with differing series lengths
- [x] **Task 15:** Frontier weight-constraint coverage missing
  - `_apply_constraints` assigns `port.upperlng`/`port.lowerlng` but no test asserts solved weights obey the bounds
  - Fix: add test with `max_weight=0.3` asserting `<= 0.30 + eps` on frontier sweep, min-vol, and max-sharpe
- [x] **Task 16:** `PerformanceOverlay` destroys all series on every prop update
  - `frontend/src/components/charts/performance-overlay.tsx:69-93` — removes and re-adds all lines on every `series` change; blows away zoom/auto-fit in `/compare`
  - Fix: memoize by `series.name`, reuse existing `ISeriesApi` handles with `setData`
- [x] **Task 17:** API client mis-renders FastAPI validation errors
  - `frontend/src/lib/api.ts:24-27` — `body.detail` may be an array (422 responses); current code stringifies `[object Object]`
  - Fix: `Array.isArray(body.detail) ? body.detail.map(d => d.msg).join(", ") : body.detail`
- [x] **Task 18:** CI docker smoke tests gated on `main` only
  - `.github/workflows/ci.yml:63,91` — PRs never smoke-test the Docker image; broken Dockerfiles land post-merge
  - Fix: drop the `if:` gate for `docker-frontend` (at minimum) so PRs catch it
- [x] **Task 19:** `except ValueError` too broad on benchmark route
  - `vision/api/routers/portfolios.py` — conflates "no overlap", "<60 overlapping days", and degenerate variance into one 422
  - Fix: split into distinct exception types
- [x] **Task 20:** Move local imports in `_compute_performance` to module level
  - `vision/application/risk_service.py:99-100` — `PriceHistory`/`MarketDataService` imported inside the function
- [x] **Task 21:** Benchmark endpoint test gaps
  - No coverage for `BenchmarkUnresolvableError` from the fetcher, `<60` overlapping days, or "no overlap" path
  - Fix: backfill these in `tests/api/test_risk_endpoints.py`

### Suggestions (nice-to-have)
- [x] Drop dead `dates_data` in `vision/application/optimization_service.py:38-44`
- [ ] Extract a `useLightweightChart(containerRef, options)` hook; the three chart wrappers duplicate ~40 lines
- [ ] Consolidate points-cap validation in one layer in `vision/api/routers/optimization.py`
- [ ] Document `_capture_ratio` formula (mean-based, not Morningstar-compounded) in `vision/domain/risk/services.py`
- [ ] Use `URLSearchParams` consistently in `frontend/src/lib/api.ts`
- [ ] Re-evaluate `_point_metrics` in `riskfolio_adapter.py` — re-annualized realized stats drift from Riskfolio's mean-variance frontier numbers
