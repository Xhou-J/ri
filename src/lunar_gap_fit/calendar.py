from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from typing import Optional

BASE_SOLAR = date(1900, 1, 31)
MAX_SOLAR = date(2100, 12, 31)

LUNAR_INFO = [int(x) for x in "19416,19168,42352,21717,53856,55632,91476,22176,39632,21970,19168,42422,42192,53840,119381,46400,54944,44450,38320,84343,18800,42160,46261,27216,27968,109396,11104,38256,21234,18800,25958,54432,59984,28309,23248,11104,100067,37600,116951,51536,54432,120998,46416,22176,107956,9680,37584,53938,43344,46423,27808,46416,86869,19872,42448,83315,21168,43432,59728,27296,44710,43856,19296,43748,42352,21088,62051,55632,23383,22176,38608,19925,19152,42192,54484,53840,54616,46400,46496,103846,38320,18864,43380,42160,45690,27216,27968,44870,43872,38256,19189,18800,25776,29859,59984,27480,23232,43872,38613,37600,51552,55636,54432,55888,30034,22176,43959,9680,37584,51893,43344,46240,47780,44368,21977,19360,42416,86390,21168,43312,31060,27296,44368,23378,19296,42726,42208,53856,60005,54576,23200,30371,38608,19195,19152,42192,118966,53840,54560,56645,46496,22224,21938,18864,42359,42160,43600,111189,27936,44448,84835,37744,18936,18800,25776,92326,59984,27296,108228,43744,37600,53987,51552,54615,54432,55888,23893,22176,42704,21972,21200,43448,43344,46240,46758,44368,21920,43940,42416,21168,45683,26928,29495,27296,44368,84821,19296,42352,21732,53600,59752,54560,55968,92838,22224,19168,43476,41680,53584,62034,54560".split(",")]


@dataclass(frozen=True)
class LunarAnchor:
    year: int
    month: int
    day: int
    is_leap: bool = False


LunarDate = LunarAnchor


def _check_lunar_year(year: int) -> None:
    if not 1900 <= year <= 2100:
        raise ValueError("This built-in table supports lunar years 1900–2100 only.")


@lru_cache(maxsize=None)
def leap_month(year: int) -> int:
    _check_lunar_year(year)
    return LUNAR_INFO[year - 1900] & 0xF


@lru_cache(maxsize=None)
def leap_days(year: int) -> int:
    lm = leap_month(year)
    if not lm:
        return 0
    return 30 if (LUNAR_INFO[year - 1900] & 0x10000) else 29


@lru_cache(maxsize=None)
def month_days(year: int, month: int) -> int:
    _check_lunar_year(year)
    if not 1 <= month <= 12:
        raise ValueError("Lunar month must be 1..12.")
    return 30 if (LUNAR_INFO[year - 1900] & (0x10000 >> month)) else 29


@lru_cache(maxsize=None)
def year_days(year: int) -> int:
    _check_lunar_year(year)
    total = 348
    info = LUNAR_INFO[year - 1900]
    bit = 0x8000
    while bit > 0x8:
        if info & bit:
            total += 1
        bit >>= 1
    return total + leap_days(year)


@lru_cache(maxsize=None)
def year_start_offset(year: int) -> int:
    if not 1900 <= year <= 2101:
        raise ValueError("Year out of supported cached offset range.")
    return sum(year_days(y) for y in range(1900, year))


@lru_cache(maxsize=None)
def solar_to_lunar(dt: date) -> LunarAnchor:
    if dt < BASE_SOLAR or dt > MAX_SOLAR:
        raise ValueError("Supported solar date range is 1900-01-31 through 2100-12-31.")

    offset = (dt - BASE_SOLAR).days
    year = 1900

    while year <= 2100:
        yd = year_days(year)
        if offset < yd:
            break
        offset -= yd
        year += 1

    lm = leap_month(year)
    for month in range(1, 13):
        md = month_days(year, month)
        if offset < md:
            return LunarAnchor(year, month, offset + 1, False)
        offset -= md

        if month == lm:
            ld = leap_days(year)
            if offset < ld:
                return LunarAnchor(year, month, offset + 1, True)
            offset -= ld

    raise RuntimeError("Failed to convert solar date to lunar date.")


@lru_cache(maxsize=None)
def lunar_to_solar(lunar: LunarAnchor) -> Optional[date]:
    if not 1900 <= lunar.year <= 2100:
        return None
    if not 1 <= lunar.month <= 12:
        return None
    if not 1 <= lunar.day <= 30:
        return None

    lm = leap_month(lunar.year)
    if lunar.is_leap and lm != lunar.month:
        return None

    max_day = leap_days(lunar.year) if lunar.is_leap else month_days(lunar.year, lunar.month)
    if lunar.day > max_day:
        return None

    offset = year_start_offset(lunar.year)

    for m in range(1, lunar.month):
        offset += month_days(lunar.year, m)
        if leap_month(lunar.year) == m:
            offset += leap_days(lunar.year)

    if lunar.is_leap:
        offset += month_days(lunar.year, lunar.month)

    offset += lunar.day - 1
    solar = BASE_SOLAR + timedelta(days=offset)
    return solar if solar <= MAX_SOLAR else None


def lunar_label(lunar: LunarAnchor, include_year: bool = True) -> str:
    leap = "闰" if lunar.is_leap else ""
    if include_year and lunar.year:
        return f"{lunar.year}年{leap}{lunar.month}月{lunar.day}日"
    return f"{leap}{lunar.month}月{lunar.day}日"


def clear_conversion_caches() -> None:
    for fn in [leap_month, leap_days, month_days, year_days, year_start_offset, solar_to_lunar, lunar_to_solar]:
        if hasattr(fn, "cache_clear"):
            fn.cache_clear()
