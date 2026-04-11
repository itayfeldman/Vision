from abc import ABC, abstractmethod

from vision.domain.portfolio.models import Portfolio


class PortfolioRepository(ABC):
    @abstractmethod
    def save(self, portfolio: Portfolio) -> None: ...

    @abstractmethod
    def get_by_id(self, portfolio_id: str) -> Portfolio | None: ...

    @abstractmethod
    def list_all(self) -> list[Portfolio]: ...

    @abstractmethod
    def delete(self, portfolio_id: str) -> bool: ...
