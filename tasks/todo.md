# Vision — Task List

## Phase 1: Foundation
- [ ] **Task 1:** Project Scaffolding + Dev Tooling
  - Directory structure, dependencies, ruff/mypy/pytest config, FastAPI app factory, `GET /health` smoke test
  - _Blocks: everything_

## Phase 2: Core Data Layer
- [ ] **Task 2:** Market Data Context (Vertical Slice)
  - Domain models, abstract repo, yfinance adapter, SQLite cache, API endpoint, tests
  - _Blocks: Tasks 3-7_
  - _Depends on: Task 1_

## Phase 3: Portfolio Foundation
- [ ] **Task 3:** Portfolio Domain + CRUD (Vertical Slice)
  - Domain models, repo interface, SQLite repo, CRUD API, tests
  - _Blocks: Tasks 4-7_
  - _Depends on: Task 2_

## Phase 4: Analytics (parallelizable)
- [ ] **Task 4:** Portfolio Valuation (Vertical Slice)
  - Enrich portfolio with market values, `?valued=true` query param
  - _Depends on: Tasks 2, 3_

- [ ] **Task 5:** Risk Analytics Context (Vertical Slice)
  - Risk metrics (Sharpe, VaR, CVaR, drawdown), two API endpoints, tests
  - _Depends on: Tasks 2, 3_

- [ ] **Task 6:** Optimization Context (Vertical Slice)
  - Mean-variance optimization, 4 objectives, Riskfolio-Lib adapter, tests
  - _Depends on: Tasks 2, 3_

- [ ] **Task 7:** Factor Decomposition Context (Vertical Slice)
  - Fama-French 5-factor regression, factor data adapter, tests
  - _Depends on: Tasks 2, 3_

## Phase 5: Integration
- [ ] **Task 8:** Cross-Context Integration + Wiring
  - Complete DI, portfolio summary endpoint, end-to-end integration test
  - _Depends on: Tasks 5, 6, 7_

## Phase 6: Production Readiness
- [ ] **Task 9:** Error Handling & API Polish
  - Structured errors, request logging, OpenAPI enrichment
  - _Depends on: Task 8_

- [ ] **Task 10:** CI/CD + Docker + Deploy Config
  - Dockerfile, GitHub Actions, GCP Cloud Run config, Settings class
  - _Depends on: Task 9_
