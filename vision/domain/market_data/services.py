from datetime import date

from vision.domain.market_data.models import PriceHistory


class MarketDataService:
    @staticmethod
    def compute_daily_returns(
        price_history: PriceHistory,
    ) -> list[tuple[date, float]]:
        prices = price_history.close_prices
        dates = price_history.dates
        if len(prices) < 2:
            return []
        return [
            (dates[i], (prices[i] - prices[i - 1]) / prices[i - 1])
            for i in range(1, len(prices))
        ]
