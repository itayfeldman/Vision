from datetime import date

from vision.domain.market_data.models import AssetInfo, PriceHistory


def test_price_history_creation() -> None:
    ph = PriceHistory(
        ticker="AAPL",
        dates=[date(2024, 1, 2), date(2024, 1, 3)],
        close_prices=[150.0, 152.0],
        volumes=[1000000, 1100000],
    )
    assert ph.ticker == "AAPL"
    assert len(ph.dates) == 2
    assert ph.close_prices[1] == 152.0


def test_price_history_is_frozen() -> None:
    ph = PriceHistory(
        ticker="AAPL",
        dates=[date(2024, 1, 2)],
        close_prices=[150.0],
        volumes=[1000000],
    )
    try:
        ph.ticker = "GOOGL"  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except AttributeError:
        pass


def test_asset_info_creation() -> None:
    info = AssetInfo(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        currency="USD",
    )
    assert info.ticker == "AAPL"
    assert info.sector == "Technology"
