from __future__ import annotations

from datetime import date
from typing import Optional

from .calendar import LunarAnchor, lunar_to_solar
from .models import GapRow


def safe_solar_anchor(year: int, month: int, day: int) -> Optional[date]:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def find_lunar_anchor(
    solar_anchor: date,
    lunar_month: int,
    lunar_day: int,
    is_leap: bool,
    same_gregorian_year: bool = False,
) -> tuple[Optional[date], Optional[int]]:
    candidates = []
    for ly in range(solar_anchor.year - 1, solar_anchor.year + 2):
        candidate = lunar_to_solar(LunarAnchor(ly, lunar_month, lunar_day, is_leap))
        if candidate is None:
            continue
        if same_gregorian_year and candidate.year != solar_anchor.year:
            continue
        candidates.append((abs((candidate - solar_anchor).days), candidate, ly))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][1], candidates[0][2]


def build_gap_series(
    solar_month: int,
    solar_day: int,
    lunar_anchor: LunarAnchor,
    start_year: int = 1901,
    end_year: int = 2100,
    same_gregorian_year: bool = False,
) -> list[GapRow]:
    if not (1901 <= start_year <= end_year <= 2100):
        raise ValueError("Recommended and supported fit range is 1901–2100.")
    match_mode = "same_gregorian_year" if same_gregorian_year else "nearest"
    rows: list[GapRow] = []
    for year in range(start_year, end_year + 1):
        solar_anchor = safe_solar_anchor(year, solar_month, solar_day)
        if solar_anchor is None:
            rows.append(
                GapRow(
                    year=year,
                    solar_anchor="",
                    lunar_match_date=None,
                    lunar_year_of_match=None,
                    lunar_month=lunar_anchor.month,
                    lunar_day=lunar_anchor.day,
                    lunar_is_leap=lunar_anchor.is_leap,
                    match_mode=match_mode,
                    gap_days=None,
                )
            )
            continue
        lunar_match, lunar_year = find_lunar_anchor(
            solar_anchor,
            lunar_anchor.month,
            lunar_anchor.day,
            lunar_anchor.is_leap,
            same_gregorian_year=same_gregorian_year,
        )
        gap = None if lunar_match is None else (lunar_match - solar_anchor).days
        rows.append(
            GapRow(
                year=year,
                solar_anchor=solar_anchor.isoformat(),
                lunar_match_date=lunar_match.isoformat() if lunar_match else None,
                lunar_year_of_match=lunar_year,
                lunar_month=lunar_anchor.month,
                lunar_day=lunar_anchor.day,
                lunar_is_leap=lunar_anchor.is_leap,
                match_mode=match_mode,
                gap_days=gap,
            )
        )
    return rows
