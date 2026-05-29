from __future__ import annotations

import math
from dataclasses import asdict
from datetime import date
from typing import Optional

import numpy as np

from .calendar import LunarAnchor
from .models import FitResult, GapRow


def fourier_design(years: np.ndarray, period: float, harmonics: int, y0: int) -> np.ndarray:
    t = years - y0
    cols = [np.ones_like(t, dtype=float)]
    for k in range(1, harmonics + 1):
        angle = 2 * np.pi * k * t / period
        cols.append(np.cos(angle))
        cols.append(np.sin(angle))
    return np.column_stack(cols)


def fit_single(years: np.ndarray, gaps: np.ndarray, period: float, harmonics: int, y0: int):
    x = fourier_design(years, period, harmonics, y0)
    coef, *_ = np.linalg.lstsq(x, gaps, rcond=None)
    pred = x @ coef
    resid = gaps - pred
    rss = float(np.sum(resid ** 2))
    n = len(gaps)
    p = 1 + 2 * harmonics
    mae = float(np.mean(np.abs(resid)))
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    denom = float(np.sum((gaps - np.mean(gaps)) ** 2))
    r2 = float(1 - rss / denom) if denom else float("nan")
    bic = float(n * math.log(max(rss / n, 1e-12)) + p * math.log(n))
    return coef, mae, rmse, r2, bic


def default_harmonic_candidates(n: int) -> list[int]:
    raw = [1, 2, 3, 5, 8, 12, 16, 24, 32, 40]
    max_h = max(1, (n - 2) // 2)
    return sorted({h for h in raw if 1 <= h <= max_h})


def fit_fourier(
    rows: list[GapRow],
    mode: str,
    input_date: Optional[date],
    solar_month: int,
    solar_day: int,
    lunar_anchor: LunarAnchor,
    same_gregorian_year: bool,
    period_arg: str = "auto",
    harmonics_arg: str = "auto",
    candidate_periods: Optional[list[float]] = None,
) -> FitResult:
    usable = [r for r in rows if r.gap_days is not None]
    skipped = len(rows) - len(usable)
    if len(usable) < 5:
        raise ValueError("Too few usable data points to fit.")

    years = np.array([r.year for r in usable], dtype=float)
    gaps = np.array([r.gap_days for r in usable], dtype=float)
    y0 = int(years.min())
    n = len(usable)

    period_mode = "auto" if period_arg.lower() == "auto" else "manual"
    if period_mode == "auto":
        periods = candidate_periods or [8, 11, 19, 38, 57, 76, 95, 114, 133, 152, 171, 190]
    else:
        periods = [float(period_arg)]

    harmonics_mode = "auto" if harmonics_arg.lower() == "auto" else "manual"
    if harmonics_mode == "auto":
        harmonic_candidates = default_harmonic_candidates(n)
    else:
        h = int(harmonics_arg)
        if h < 1:
            raise ValueError("--harmonics must be at least 1.")
        max_h = max(1, (n - 2) // 2)
        harmonic_candidates = [min(h, max_h)]

    best = None
    evaluated = 0
    for period in periods:
        if period <= 0:
            continue
        for harmonics in harmonic_candidates:
            if 1 + 2 * harmonics >= n:
                continue
            coef, mae, rmse, r2, bic = fit_single(years, gaps, period, harmonics, y0)
            evaluated += 1
            record = (bic, period, harmonics, coef, mae, rmse, r2)
            if best is None or record[0] < best[0]:
                best = record

    if best is None:
        raise ValueError("No valid Fourier model could be fit.")

    bic, selected_period, selected_harmonics, coef, mae, rmse, r2 = best
    return FitResult(
        mode=mode,
        input_date=input_date.isoformat() if input_date else None,
        solar_month=solar_month,
        solar_day=solar_day,
        input_lunar=asdict(lunar_anchor),
        match_mode="same_gregorian_year" if same_gregorian_year else "nearest",
        start_year=int(years.min()),
        end_year=int(years.max()),
        period_mode=period_mode,
        selected_period=float(selected_period),
        harmonics_mode=harmonics_mode,
        selected_harmonics=int(selected_harmonics),
        intercept=float(coef[0]),
        cos_coefficients=[float(coef[1 + 2 * i]) for i in range(selected_harmonics)],
        sin_coefficients=[float(coef[2 + 2 * i]) for i in range(selected_harmonics)],
        mae=float(mae),
        rmse=float(rmse),
        r2=float(r2),
        bic=float(bic),
        usable_points=n,
        skipped_points=skipped,
        period_candidates=[float(x) for x in periods],
        harmonic_candidates=[int(x) for x in harmonic_candidates],
        candidates_evaluated=int(evaluated),
    )


def fitted_value(year: float, result: FitResult) -> float:
    total = result.intercept
    for k in range(1, result.selected_harmonics + 1):
        angle = 2 * math.pi * k * (year - result.start_year) / result.selected_period
        total += result.cos_coefficients[k - 1] * math.cos(angle)
        total += result.sin_coefficients[k - 1] * math.sin(angle)
    return total
