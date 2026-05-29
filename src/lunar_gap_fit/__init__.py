"""Lunar Gap Fit: Fourier modeling for Gregorian-lunar date gaps."""

__version__ = "0.1.0"

from .calendar import LunarAnchor, LunarDate, lunar_to_solar, solar_to_lunar
from .fitting import fit_fourier, fitted_value
from .models import FitResult, GapRow
from .series import build_gap_series

__all__ = [
    "LunarAnchor",
    "LunarDate",
    "GapRow",
    "FitResult",
    "solar_to_lunar",
    "lunar_to_solar",
    "build_gap_series",
    "fit_fourier",
    "fitted_value",
]
