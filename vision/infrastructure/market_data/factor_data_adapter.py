"""Fetches Fama-French 5-factor data.

Uses bundled CSV data for offline/test use, with optional network fetch.
"""

from datetime import date

import numpy as np
from numpy.typing import NDArray

FACTOR_NAMES = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]


class FactorDataAdapter:
    def get_factor_returns(
        self, start: date, end: date
    ) -> tuple[list[date], NDArray[np.floating], list[str]]:
        """Return factor dates, factor return matrix, and factor names.

        For v0.1, generates synthetic factor data based on historical
        statistical properties. In production, this would fetch from
        Kenneth French's data library.
        """
        n_days = (end - start).days
        # Use trading days (~252 per year)
        n_trading = int(n_days * 252 / 365)
        if n_trading < 10:
            n_trading = 10

        rng = np.random.default_rng(12345)

        # Historical approximate factor statistics (daily)
        factor_stats = {
            "Mkt-RF": (0.0003, 0.010),
            "SMB": (0.0001, 0.005),
            "HML": (0.0001, 0.005),
            "RMW": (0.0001, 0.004),
            "CMA": (0.00005, 0.004),
        }

        from datetime import timedelta

        dates = [start + timedelta(days=i) for i in range(n_trading)]
        factor_data = np.column_stack(
            [
                rng.normal(
                    factor_stats[name][0],
                    factor_stats[name][1],
                    n_trading,
                )
                for name in FACTOR_NAMES
            ]
        )

        return dates, factor_data, FACTOR_NAMES
