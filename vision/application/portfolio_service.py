import uuid
from datetime import date, timedelta

from vision.domain.market_data.repository import MarketDataRepository
from vision.domain.portfolio.models import Holding, Portfolio, ValuedPortfolio
from vision.domain.portfolio.repository import PortfolioRepository
from vision.domain.portfolio.services import PortfolioConstructionService


class PortfolioNotFoundError(Exception):
    pass


class PortfolioAppService:
    def __init__(
        self,
        portfolio_repo: PortfolioRepository,
        market_data_repo: MarketDataRepository,
    ) -> None:
        self._portfolio_repo = portfolio_repo
        self._market_data_repo = market_data_repo

    def create_portfolio(
        self, name: str, holdings: list[Holding]
    ) -> Portfolio:
        PortfolioConstructionService.validate_weights(holdings)
        PortfolioConstructionService.validate_tickers(
            holdings, self._market_data_repo.validate_ticker
        )
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            name=name,
            holdings=holdings,
        )
        self._portfolio_repo.save(portfolio)
        return portfolio

    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")
        return portfolio

    def list_portfolios(self) -> list[Portfolio]:
        return self._portfolio_repo.list_all()

    def update_portfolio(
        self, portfolio_id: str, name: str, holdings: list[Holding]
    ) -> Portfolio:
        existing = self._portfolio_repo.get_by_id(portfolio_id)
        if not existing:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")
        PortfolioConstructionService.validate_weights(holdings)
        PortfolioConstructionService.validate_tickers(
            holdings, self._market_data_repo.validate_ticker
        )
        updated = Portfolio(id=portfolio_id, name=name, holdings=holdings)
        self._portfolio_repo.save(updated)
        return updated

    def delete_portfolio(self, portfolio_id: str) -> None:
        deleted = self._portfolio_repo.delete(portfolio_id)
        if not deleted:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")

    def get_portfolio_with_values(
        self, portfolio_id: str, total_investment: float = 10000.0
    ) -> ValuedPortfolio:
        portfolio = self.get_portfolio(portfolio_id)
        end = date.today()
        start = end - timedelta(days=7)

        prices: dict[str, float] = {}
        for h in portfolio.holdings:
            try:
                history = self._market_data_repo.get_price_history(
                    h.ticker, start, end
                )
                if history.close_prices:
                    prices[h.ticker] = history.close_prices[-1]
            except Exception:
                continue

        return PortfolioConstructionService.value_portfolio(
            portfolio, prices, total_investment
        )
