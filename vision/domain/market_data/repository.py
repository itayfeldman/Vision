from abc import ABC, abstractmethod
from datetime import date

from vision.domain.market_data.models import AssetInfo, PriceHistory


class MarketDataRepository(ABC):
    @abstractmethod
    def get_price_history(
        self, ticker: str, start: date, end: date
    ) -> PriceHistory: ...

    @abstractmethod
    def get_asset_info(self, ticker: str) -> AssetInfo: ...

    @abstractmethod
    def validate_ticker(self, ticker: str) -> bool: ...
