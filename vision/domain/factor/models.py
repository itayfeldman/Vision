from dataclasses import dataclass


@dataclass(frozen=True)
class FactorExposure:
    factor_name: str
    beta: float
    t_statistic: float
    p_value: float


@dataclass(frozen=True)
class FactorDecomposition:
    exposures: list[FactorExposure]
    r_squared: float
    alpha: float
    alpha_t_stat: float
    residual_risk: float
