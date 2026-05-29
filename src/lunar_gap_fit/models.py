from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GapRow:
    year: int
    solar_anchor: str
    lunar_match_date: Optional[str]
    lunar_year_of_match: Optional[int]
    lunar_month: int
    lunar_day: int
    lunar_is_leap: bool
    match_mode: str
    gap_days: Optional[int]


@dataclass
class FitResult:
    mode: str
    input_date: Optional[str]
    solar_month: int
    solar_day: int
    input_lunar: dict
    match_mode: str
    start_year: int
    end_year: int
    period_mode: str
    selected_period: float
    harmonics_mode: str
    selected_harmonics: int
    intercept: float
    cos_coefficients: list[float]
    sin_coefficients: list[float]
    mae: float
    rmse: float
    r2: float
    bic: float
    usable_points: int
    skipped_points: int
    period_candidates: list[float]
    harmonic_candidates: list[int]
    candidates_evaluated: int
