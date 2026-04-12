# Vision — Task List

> Frontend + backend extensions per SPEC.md §4.2, §4.3, §11. The v0.1 backend foundation is shipped.

## Phase 1: Backend Endpoints
- [ ] **Task 1:** Efficient Frontier endpoint — `POST /api/optimize/frontier`
  - Domain models, Riskfolio frontier sweep, application service, route, tests
  - _Blocks: Task 4, Task 5_
- [ ] **Task 2:** Benchmark Comparison endpoint — `GET /api/portfolios/{id}/benchmark`
  - Domain `BenchmarkComparison`, regression service, app service, route, tests
  - _Blocks: Task 4, Task 7_

### Checkpoint: Backend Endpoints
- [ ] All tests pass; ruff + mypy clean
- [ ] Both endpoints visible in `/docs` with correct schemas
- [ ] Manual curl verification of both
- [ ] Human review of endpoint shapes before frontend consumes them

## Phase 2: Frontend Foundation
- [ ] **Task 3:** Chart wrapper layer + TradingView Lightweight Charts
  - Install `lightweight-charts`; create `PerformanceChart`, `AllocationPie`, `FactorBars`; refactor portfolio detail page to use them
  - _Depends on: none_
- [ ] **Task 4:** API client + types + sidebar refactor
  - Add `api.optimize.frontier`, `api.risk.benchmark`; new types; extract `Sidebar` component
  - _Depends on: Tasks 1, 2_

### Checkpoint: Foundation
- [ ] Existing screens still work
- [ ] `npm run build` succeeds
- [ ] Tasks 5–8 can now run in parallel

## Phase 3: New Screens (parallelizable)
- [ ] **Task 5:** `/frontier` page — efficient frontier explorer
  - Inputs + scatter chart + named-portfolio highlights + weights table + sidebar nav
  - _Depends on: Tasks 1, 3, 4_
- [ ] **Task 6:** `/compare` page — multi-portfolio comparison
  - Multi-select, KPI grid with best/worst coloring, factor + performance overlays, sidebar nav
  - _Depends on: Tasks 3, 4_
- [ ] **Task 7:** `/benchmark/[id]` page — portfolio vs benchmark
  - Benchmark selector, KPI strip, cumulative-return overlay, spread chart, link from detail page
  - _Depends on: Tasks 2, 3, 4_
- [ ] **Task 8:** Holdings drill-down on portfolio detail
  - Expandable rows with per-ticker price chart (Lightweight Charts)
  - _Depends on: Tasks 3, 4_

### Checkpoint: All Screens
- [ ] All four new screens render against running backend
- [ ] Sidebar contains: Dashboard, New Portfolio, Optimizer, Frontier, Compare
- [ ] `npm run build` and `npm run lint` clean
- [ ] Manual smoke of every screen
- [ ] Human review before deploying

## Phase 4: Production
- [ ] **Task 9:** Frontend Dockerfile + Cloud Run config
  - Multi-stage Dockerfile, env-driven `VISION_API_URL`, `.dockerignore`, local container verified
  - _Depends on: Tasks 5–8_
- [ ] **Task 10:** CI extension for frontend
  - New `frontend` job in `.github/workflows/ci.yml` (lint + typecheck + build + deploy on `main`)
  - _Depends on: Task 9_

### Checkpoint: Production
- [ ] CI green on feature branch
- [ ] Frontend deployed to Cloud Run, talking to backend
- [ ] SPEC §11.11 success criteria all checked
