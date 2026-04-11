import pytest

from vision.domain.portfolio.models import Holding
from vision.domain.portfolio.services import (
    InvalidTickerError,
    InvalidWeightsError,
    PortfolioConstructionService,
)


def test_validate_weights_valid() -> None:
    holdings = [
        Holding(ticker="AAPL", weight=0.6),
        Holding(ticker="GOOGL", weight=0.4),
    ]
    PortfolioConstructionService.validate_weights(holdings)


def test_validate_weights_not_summing_to_one() -> None:
    holdings = [
        Holding(ticker="AAPL", weight=0.5),
        Holding(ticker="GOOGL", weight=0.3),
    ]
    with pytest.raises(InvalidWeightsError, match="sum to 1.0"):
        PortfolioConstructionService.validate_weights(holdings)


def test_validate_weights_empty() -> None:
    with pytest.raises(InvalidWeightsError, match="at least one holding"):
        PortfolioConstructionService.validate_weights([])


def test_validate_weights_negative() -> None:
    holdings = [
        Holding(ticker="AAPL", weight=-0.2),
        Holding(ticker="GOOGL", weight=1.2),
    ]
    with pytest.raises(InvalidWeightsError, match="non-negative"):
        PortfolioConstructionService.validate_weights(holdings)


def test_validate_tickers_valid() -> None:
    def validator(ticker: str) -> bool:
        return ticker in {"AAPL", "GOOGL"}

    holdings = [
        Holding(ticker="AAPL", weight=0.5),
        Holding(ticker="GOOGL", weight=0.5),
    ]
    PortfolioConstructionService.validate_tickers(holdings, validator)


def test_validate_tickers_invalid() -> None:
    def validator(ticker: str) -> bool:
        return ticker == "AAPL"

    holdings = [
        Holding(ticker="AAPL", weight=0.5),
        Holding(ticker="INVALID", weight=0.5),
    ]
    with pytest.raises(InvalidTickerError, match="INVALID"):
        PortfolioConstructionService.validate_tickers(holdings, validator)
