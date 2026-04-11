from collections.abc import Callable

from vision.domain.portfolio.models import (
    Holding,
    Portfolio,
    ValuedHolding,
    ValuedPortfolio,
)


class InvalidWeightsError(ValueError):
    pass


class InvalidTickerError(ValueError):
    pass


class PortfolioConstructionService:
    @staticmethod
    def validate_weights(holdings: list[Holding]) -> None:
        if not holdings:
            raise InvalidWeightsError("Portfolio must have at least one holding")
        for h in holdings:
            if h.weight < 0:
                raise InvalidWeightsError(
                    f"Weight for {h.ticker} must be non-negative, got {h.weight}"
                )
        total = sum(h.weight for h in holdings)
        if abs(total - 1.0) > 1e-6:
            raise InvalidWeightsError(
                f"Weights must sum to 1.0, got {total:.6f}"
            )

    @staticmethod
    def validate_tickers(
        holdings: list[Holding],
        ticker_validator: Callable[[str], bool],
    ) -> None:
        for h in holdings:
            if not ticker_validator(h.ticker):
                raise InvalidTickerError(f"Invalid ticker: {h.ticker}")

    @staticmethod
    def value_portfolio(
        portfolio: Portfolio,
        prices: dict[str, float],
        total_investment: float = 10000.0,
    ) -> ValuedPortfolio:
        valued_holdings: list[ValuedHolding] = []
        for h in portfolio.holdings:
            if h.ticker in prices:
                price = prices[h.ticker]
                allocation = h.weight * total_investment
                shares = allocation / price
                valued_holdings.append(
                    ValuedHolding(
                        ticker=h.ticker,
                        weight=h.weight,
                        current_price=price,
                        shares=shares,
                    )
                )
        return ValuedPortfolio(
            id=portfolio.id,
            name=portfolio.name,
            holdings=valued_holdings,
        )
