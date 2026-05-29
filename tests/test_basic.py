from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_gap_fit.cli import (
    LunarAnchor,
    solar_to_lunar,
    lunar_to_solar,
    build_gap_series,
    fit_fourier,
    parse_gregorian_date,
    parse_mmdd,
    find_next_exact_year,
)


def test_flexible_gregorian_date_parsing():
    assert parse_gregorian_date("2005-02-04") == date(2005, 2, 4)
    assert parse_gregorian_date("2005-2-4") == date(2005, 2, 4)
    assert parse_gregorian_date("2005/2/4") == date(2005, 2, 4)
    assert parse_gregorian_date("2005.2.4") == date(2005, 2, 4)


def test_flexible_mmdd_parsing():
    assert parse_mmdd("05-08") == (5, 8)
    assert parse_mmdd("5/8") == (5, 8)
    assert parse_mmdd("5.8") == (5, 8)


def test_round_trip_known_dates():
    for d in [
        date(1901, 1, 1),
        date(2004, 7, 24),
        date(2005, 2, 4),
        date(2008, 7, 10),
        date(2026, 5, 8),
        date(2099, 12, 31),
    ]:
        lunar = solar_to_lunar(d)
        assert lunar_to_solar(lunar) == d


def test_auto_fit():
    d = date(2004, 7, 24)
    lunar = solar_to_lunar(d)
    rows = build_gap_series(d.month, d.day, lunar, 1901, 2100, False)
    result = fit_fourier(
        rows=rows,
        mode="auto",
        input_date=d,
        solar_month=d.month,
        solar_day=d.day,
        lunar_anchor=lunar,
        same_gregorian_year=False,
        period_arg="auto",
        harmonics_arg="auto",
        candidate_periods=[8, 11, 19, 38, 57, 76, 95],
    )
    assert result.usable_points >= 190
    assert result.selected_period > 0
    assert result.selected_harmonics >= 1


def test_manual_fit():
    rows = build_gap_series(5, 8, LunarAnchor(0, 3, 23, False), 1901, 2100, False)
    result = fit_fourier(
        rows=rows,
        mode="manual",
        input_date=None,
        solar_month=5,
        solar_day=8,
        lunar_anchor=LunarAnchor(0, 3, 23, False),
        same_gregorian_year=False,
        period_arg="auto",
        harmonics_arg="auto",
        candidate_periods=[8, 11, 19, 38, 57, 76, 95],
    )
    assert result.usable_points >= 190
    assert result.selected_period > 0


def test_find_next_exact_year():
    d = date(2004, 7, 24)
    lunar = solar_to_lunar(d)
    rows = build_gap_series(d.month, d.day, lunar, 1901, 2100, False)
    assert find_next_exact_year(rows, 2004) == 2042


if __name__ == "__main__":
    test_flexible_gregorian_date_parsing()
    test_flexible_mmdd_parsing()
    test_round_trip_known_dates()
    test_auto_fit()
    test_manual_fit()
    test_find_next_exact_year()
    print("basic tests passed")
