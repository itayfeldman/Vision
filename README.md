# Vision

Portfolio Construction & Analytics Platform. FastAPI backend providing portfolio management, risk analytics, optimization, and Fama-French factor decomposition for US equities and ETFs.

## Quick Start

```bash
uv sync
uv run main.py
```

The API is available at `http://localhost:8080`. Interactive docs at `/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/market-data/{ticker}/prices` | Historical prices |
| POST | `/api/portfolios` | Create portfolio |
| GET | `/api/portfolios` | List portfolios |
| GET | `/api/portfolios/{id}` | Get portfolio (`?valued=true` for market values) |
| GET | `/api/portfolios/{id}/summary` | Portfolio summary with risk & factor data |
| PUT | `/api/portfolios/{id}` | Update portfolio |
| DELETE | `/api/portfolios/{id}` | Delete portfolio |
| GET | `/api/risk/{id}` | Risk report (VaR, Sharpe, drawdown, etc.) |
| POST | `/api/risk/analyze` | Ad-hoc risk analysis |
| POST | `/api/optimize` | Portfolio optimization (min vol, max Sharpe, etc.) |
| GET | `/api/factors/{id}` | Fama-French 5-factor decomposition |

## Development

```bash
uv run pytest                # Run tests
uv run ruff check .          # Lint
uv run mypy vision/          # Type check
```

## Docker

```bash
docker build -t vision .
docker run -p 8080:8080 vision
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port |
| `VISION_HOST` | `0.0.0.0` | Bind address |
| `VISION_DB_PATH` | `vision.db` | SQLite database path |
| `VISION_LOG_LEVEL` | `INFO` | Log level |

## Architecture

Layered DDD architecture with 5 bounded contexts:

```
API (FastAPI routers + Pydantic schemas)
  -> Application (orchestration services)
    -> Domain (models, business logic, repository interfaces)
      -> Infrastructure (SQLite, yfinance, riskfolio-lib)
```

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: SQLite via SQLAlchemy 2.0 Core
- **Market Data**: yfinance
- **Optimization**: riskfolio-lib
- **Factor Analysis**: statsmodels OLS (Fama-French 5-factor)
- **Risk Metrics**: empyrical-reloaded
