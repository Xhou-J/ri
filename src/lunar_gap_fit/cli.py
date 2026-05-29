from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
from lunardate import LunarDate as _LunarDate


@dataclass(frozen=True)
class LunarAnchor:
    year: int
    month: int
    day: int
    is_leap: bool = False


@dataclass
class GapRow:
    year: int
    solar_anchor: str
    lunar_match_date: Optional[str]
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
    lunar_anchor: dict
    match_mode: str
    start_year: int
    end_year: int
    selected_period: float
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


def _is_leap(lunar: _LunarDate) -> bool:
    return bool(getattr(lunar, "isLeapMonth", False))


def solar_to_lunar(d: date) -> LunarAnchor:
    lunar = _LunarDate.fromSolarDate(d.year, d.month, d.day)
    return LunarAnchor(lunar.year, lunar.month, lunar.day, _is_leap(lunar))


def lunar_to_solar(anchor: LunarAnchor) -> Optional[date]:
    try:
        lunar = _LunarDate(anchor.year, anchor.month, anchor.day, anchor.is_leap)
        return lunar.toSolarDate()
    except Exception:
        return None


def parse_gregorian_date(value: str) -> date:
    m = re.fullmatch(r"\s*(\d{4})[-./](\d{1,2})[-./](\d{1,2})\s*", value)
    if not m:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD, YYYY/M/D, or YYYY.M.D format, e.g. 2004-07-24.")
    year, month, day = map(int, m.groups())
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def parse_mmdd(value: str) -> tuple[int, int]:
    m = re.fullmatch(r"\s*(\d{1,2})[-./](\d{1,2})\s*", value.strip())
    if not m:
        raise argparse.ArgumentTypeError("Use MM-DD, MM/DD, or MM.DD format, e.g. 05-08.")
    month, day = int(m.group(1)), int(m.group(2))
    try:
        date(2000, month, day)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return month, day


def parse_candidates(value: str, cast=float) -> list:
    out = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parsed = cast(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"Invalid candidate: {item!r}") from exc
        if parsed <= 0:
            raise argparse.ArgumentTypeError("Candidates must be positive.")
        out.append(parsed)
    if not out:
        raise argparse.ArgumentTypeError("Candidate list cannot be empty.")
    return out


def safe_solar_anchor(year: int, month: int, day: int) -> Optional[date]:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def find_lunar_date(
    solar_anchor: date,
    lunar_month: int,
    lunar_day: int,
    lunar_is_leap: bool,
    same_gregorian_year: bool,
) -> Optional[date]:
    candidates = []
    for lunar_year in range(solar_anchor.year - 1, solar_anchor.year + 2):
        d = lunar_to_solar(LunarAnchor(lunar_year, lunar_month, lunar_day, lunar_is_leap))
        if d is None:
            continue
        if same_gregorian_year and d.year != solar_anchor.year:
            continue
        candidates.append((abs((d - solar_anchor).days), d))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][1]


def build_gap_series(
    solar_month: int,
    solar_day: int,
    lunar_anchor: LunarAnchor,
    start_year: int = 1901,
    end_year: int = 2100,
    same_gregorian_year: bool = False,
) -> list[GapRow]:
    if start_year > end_year:
        raise ValueError("start year must be <= end year")
    mode = "same_gregorian_year" if same_gregorian_year else "nearest"
    rows = []
    for year in range(start_year, end_year + 1):
        solar_anchor = safe_solar_anchor(year, solar_month, solar_day)
        if solar_anchor is None:
            rows.append(GapRow(year, "", None, lunar_anchor.month, lunar_anchor.day, lunar_anchor.is_leap, mode, None))
            continue
        match = find_lunar_date(solar_anchor, lunar_anchor.month, lunar_anchor.day, lunar_anchor.is_leap, same_gregorian_year)
        gap = None if match is None else (match - solar_anchor).days
        rows.append(GapRow(year, solar_anchor.isoformat(), match.isoformat() if match else None, lunar_anchor.month, lunar_anchor.day, lunar_anchor.is_leap, mode, gap))
    return rows


def design_matrix(years: np.ndarray, period: float, harmonics: int, y0: int) -> np.ndarray:
    cols = [np.ones_like(years, dtype=float)]
    t = years - y0
    for k in range(1, harmonics + 1):
        angle = 2 * np.pi * k * t / period
        cols.append(np.cos(angle))
        cols.append(np.sin(angle))
    return np.column_stack(cols)


def fit_one(years: np.ndarray, gaps: np.ndarray, period: float, harmonics: int, y0: int):
    x = design_matrix(years, period, harmonics, y0)
    coef, *_ = np.linalg.lstsq(x, gaps, rcond=None)
    pred = x @ coef
    resid = gaps - pred
    n = len(gaps)
    p = 1 + 2 * harmonics
    rss = float(np.sum(resid ** 2))
    mae = float(np.mean(np.abs(resid)))
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    denom = float(np.sum((gaps - np.mean(gaps)) ** 2))
    r2 = float(1 - rss / denom) if denom else float("nan")
    bic = float(n * math.log(max(rss / n, 1e-12)) + p * math.log(n))
    return coef, mae, rmse, r2, bic


def default_harmonics(n: int) -> list[int]:
    max_h = max(1, (n - 2) // 2)
    return [h for h in [1, 2, 3, 5, 8, 12, 16, 24, 32, 40] if h <= max_h]


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
    if len(usable) < 5:
        raise ValueError("Too few usable points to fit.")
    years = np.array([r.year for r in usable], dtype=float)
    gaps = np.array([r.gap_days for r in usable], dtype=float)
    y0 = int(years.min())

    periods = candidate_periods or [8, 11, 19, 38, 57, 76, 95, 114, 133, 152, 171, 190]
    if period_arg != "auto":
        periods = [float(period_arg)]
    harmonics = default_harmonics(len(usable)) if harmonics_arg == "auto" else [int(harmonics_arg)]

    best = None
    for period in periods:
        for h in harmonics:
            if 1 + 2 * h >= len(usable):
                continue
            coef, mae, rmse, r2, bic = fit_one(years, gaps, period, h, y0)
            item = (bic, period, h, coef, mae, rmse, r2)
            if best is None or item[0] < best[0]:
                best = item
    if best is None:
        raise ValueError("No valid Fourier model could be fit.")

    bic, period, h, coef, mae, rmse, r2 = best
    return FitResult(
        mode=mode,
        input_date=input_date.isoformat() if input_date else None,
        solar_month=solar_month,
        solar_day=solar_day,
        lunar_anchor=asdict(lunar_anchor),
        match_mode="same_gregorian_year" if same_gregorian_year else "nearest",
        start_year=int(years.min()),
        end_year=int(years.max()),
        selected_period=float(period),
        selected_harmonics=int(h),
        intercept=float(coef[0]),
        cos_coefficients=[float(coef[1 + 2 * i]) for i in range(h)],
        sin_coefficients=[float(coef[2 + 2 * i]) for i in range(h)],
        mae=mae,
        rmse=rmse,
        r2=r2,
        bic=bic,
        usable_points=len(usable),
        skipped_points=len(rows) - len(usable),
    )


def fitted_value(year: float, result: FitResult) -> float:
    total = result.intercept
    for k in range(1, result.selected_harmonics + 1):
        angle = 2 * math.pi * k * (year - result.start_year) / result.selected_period
        total += result.cos_coefficients[k - 1] * math.cos(angle)
        total += result.sin_coefficients[k - 1] * math.sin(angle)
    return total


def find_next_exact_year(rows: list[GapRow], after_year: int) -> Optional[int]:
    for row in rows:
        if row.gap_days == 0 and row.year > after_year:
            return row.year
    return None


def get_row_for_year(rows: list[GapRow], year: int) -> Optional[GapRow]:
    for row in rows:
        if row.year == year:
            return row
    return None


def write_csv(rows: list[GapRow], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_formula(result: FitResult, path: Path) -> None:
    content = f'''import math\n\nSELECTED_PERIOD = {result.selected_period!r}\nSELECTED_HARMONICS = {result.selected_harmonics!r}\nY0 = {result.start_year!r}\nINTERCEPT = {result.intercept!r}\nCOS = {result.cos_coefficients!r}\nSIN = {result.sin_coefficients!r}\n\ndef gap_fit(year: float) -> float:\n    total = INTERCEPT\n    for k in range(1, SELECTED_HARMONICS + 1):\n        angle = 2 * math.pi * k * (year - Y0) / SELECTED_PERIOD\n        total += COS[k - 1] * math.cos(angle)\n        total += SIN[k - 1] * math.sin(angle)\n    return total\n\ndef gap_fit_rounded(year: float) -> int:\n    return round(gap_fit(year))\n'''
    path.write_text(content, encoding="utf-8")


def write_report(result: FitResult, rows: list[GapRow], path: Path) -> None:
    exact = [r.year for r in rows if r.gap_days == 0]
    text = f"""# Lunar Gap Fit Report

Mode: `{result.mode}`

Solar anchor: `{result.solar_month:02d}-{result.solar_day:02d}`

Lunar anchor: `{result.lunar_anchor['month']}-{result.lunar_anchor['day']}`

Match mode: `{result.match_mode}`

Selected period: `{result.selected_period:g}`

Selected harmonics: `{result.selected_harmonics}`

MAE: `{result.mae:.4f}` days  
RMSE: `{result.rmse:.4f}` days  
R²: `{result.r2:.6f}`  
BIC: `{result.bic:.4f}`

Exact coincidence years:

{', '.join(map(str, exact)) if exact else 'None'}
"""
    path.write_text(text, encoding="utf-8")


def write_plot(rows: list[GapRow], result: FitResult, path: Path) -> None:
    import matplotlib.pyplot as plt

    usable = [r for r in rows if r.gap_days is not None]
    years = np.array([r.year for r in usable], dtype=float)
    gaps = np.array([r.gap_days for r in usable], dtype=float)
    xfit = np.linspace(years.min(), years.max(), 1000)
    yfit = np.array([fitted_value(x, result) for x in xfit])
    plt.figure(figsize=(11, 5.8))
    plt.scatter(years, gaps, s=14, label="actual gap")
    plt.plot(xfit, yfit, linewidth=1.8, label=f"fit: P={result.selected_period:g}, N={result.selected_harmonics}")
    plt.axhline(0, linewidth=1)
    plt.xlabel("Year")
    plt.ylabel("Gap in days")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def resolve_mode(args):
    manual = [args.solar is not None, args.lunar_month is not None, args.lunar_day is not None]
    if any(manual):
        if not all(manual):
            raise ValueError("Manual mode requires --solar, --lunar-month, and --lunar-day together.")
        if args.date:
            raise ValueError("Use either auto mode date OR manual mode, not both.")
        sm, sd = args.solar
        anchor = LunarAnchor(0, args.lunar_month, args.lunar_day, args.lunar_leap)
        return "manual", None, sm, sd, anchor
    if not args.date:
        raise ValueError("Provide a date, or use manual mode.")
    d = parse_gregorian_date(args.date)
    anchor = solar_to_lunar(d)
    return "auto", d, d.month, d.day, anchor


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit Gregorian-lunar date gaps with a Fourier model.")
    parser.add_argument("date", nargs="?", help="Gregorian date, e.g. 2004-07-24, 2004/7/24, or 2004.7.24")
    parser.add_argument("--solar", type=parse_mmdd, help="Manual solar anchor, MM-DD, MM/DD, or MM.DD")
    parser.add_argument("--lunar-month", type=int, help="Manual lunar month, 1..12")
    parser.add_argument("--lunar-day", type=int, help="Manual lunar day, 1..30")
    parser.add_argument("--lunar-leap", action="store_true", help="Use leap lunar month")
    parser.add_argument("--match-same-gregorian-year", action="store_true")
    parser.add_argument("--start", type=int, default=1901)
    parser.add_argument("--end", type=int, default=2100)
    parser.add_argument("--period", default="auto")
    parser.add_argument("--harmonics", default="auto")
    parser.add_argument("--candidate-periods", default="8,11,19,38,57,76,95,114,133,152,171,190")
    parser.add_argument("--out", default=None)
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--predict-year", type=int, help="Print fitted and actual gap for a target year")
    parser.add_argument("--find-next-coincidence", action="store_true", help="Find the next exact Gregorian-lunar coincidence year")
    parser.add_argument("--after-year", type=int, help="Search for next coincidence after this year")
    parser.add_argument("--birthday-mode", action="store_true", help="Find the next birthday coincidence after the input birth year")
    args = parser.parse_args()

    mode, input_date, sm, sd, anchor = resolve_mode(args)
    out = Path(args.out or (f"out_{input_date.isoformat()}" if input_date else f"out_{sm:02d}_{sd:02d}"))
    out.mkdir(parents=True, exist_ok=True)
    rows = build_gap_series(sm, sd, anchor, args.start, args.end, args.match_same_gregorian_year)
    result = fit_fourier(rows, mode, input_date, sm, sd, anchor, args.match_same_gregorian_year, args.period, args.harmonics, parse_candidates(args.candidate_periods, float))
    write_csv(rows, out / "gap_series.csv")
    (out / "coefficients.json").write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    write_formula(result, out / "formula.py")
    write_report(result, rows, out / "report.md")
    if not args.no_plot:
        write_plot(rows, result, out / "fit.png")

    exact = [r.year for r in rows if r.gap_days == 0]
    print("Done.")
    print(f"Mode: {mode}")
    if input_date:
        print(f"Input Gregorian date: {input_date.isoformat()}")
        print(f"Auto lunar anchor: {anchor.year}年{anchor.month}月{anchor.day}日")
    else:
        print(f"Manual solar anchor: {sm:02d}-{sd:02d}")
        print(f"Manual lunar anchor: {anchor.month}月{anchor.day}日")
    print(f"Match mode: {result.match_mode}")
    print(f"Selected period: {result.selected_period:g}")
    print(f"Selected harmonics: {result.selected_harmonics}")
    print(f"MAE={result.mae:.4f}, RMSE={result.rmse:.4f}, R^2={result.r2:.6f}, BIC={result.bic:.4f}")
    print(f"Exact coincidence years: {exact if exact else 'None'}")

    if args.predict_year is not None:
        predicted = fitted_value(args.predict_year, result)
        print(f"Predicted fitted gap for {args.predict_year}: {predicted:.4f} days, rounded {round(predicted)} days")
        row = get_row_for_year(rows, args.predict_year)
        if row and row.gap_days is not None:
            print(f"Actual gap for {args.predict_year}: {row.gap_days} days; matched lunar date: {row.lunar_match_date}")
        else:
            print(f"Actual gap for {args.predict_year}: unavailable in generated range {args.start}-{args.end}")

    if args.find_next_coincidence or args.birthday_mode:
        if args.after_year is not None:
            after_year = args.after_year
        elif args.birthday_mode and input_date is not None:
            after_year = input_date.year
        else:
            after_year = args.start - 1
        next_year = find_next_exact_year(rows, after_year)
        label = "Next birthday coincidence year" if args.birthday_mode else "Next exact coincidence year"
        if next_year is None:
            print(f"{label}: not found in generated range {args.start}-{args.end} after {after_year}")
        else:
            next_row = get_row_for_year(rows, next_year)
            print(f"{label}: {next_year}")
            if input_date is not None:
                print(f"Years after input date: {next_year - input_date.year}")
            if next_row and next_row.solar_anchor:
                print(f"Coincidence date: {next_row.solar_anchor}")


if __name__ == "__main__":
    main()
