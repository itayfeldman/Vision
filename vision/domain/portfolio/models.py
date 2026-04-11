from dataclasses import dataclass


@dataclass(frozen=True)
class Holding:
    ticker: str
    weight: float


@dataclass(frozen=True)
class Portfolio:
    id: str
    name: str
    holdings: list[Holding]

    @property
    def total_weight(self) -> float:
        return sum(h.weight for h in self.holdings)


@dataclass(frozen=True)
class ValuedHolding:
    ticker: str
    weight: float
    current_price: float
    shares: float

    @property
    def market_value(self) -> float:
        return self.current_price * self.shares


@dataclass(frozen=True)
class ValuedPortfolio:
    id: str
    name: str
    holdings: list[ValuedHolding]

    @property
    def total_value(self) -> float:
        return sum(h.market_value for h in self.holdings)
