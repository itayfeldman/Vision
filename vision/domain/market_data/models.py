from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PriceHistory:
    ticker: str
    dates: list[date]
    close_prices: list[float]
    volumes: list[int]


@dataclass(frozen=True)
class AssetInfo:
    ticker: str
    name: str
    sector: str
    currency: str
