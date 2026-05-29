from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from .calendar import LunarAnchor, lunar_label, solar_to_lunar
from .export import write_csv, write_formula_py, write_json, write_plot, write_report
from .features import (
    birthday_age,
    exact_years,
    find_next_exact_row,
    find_next_exact_row_after_date,
    format_pretty_summary,
    predict_line,
    years_and_days_between,
)
from .fitting import fit_fourier
from .series import build_gap_series


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
    m = re.fullmatch(r"\s*(\d{1,2})[-./](\d{1,2})\s*", value)
    if not m:
        raise argparse.ArgumentTypeError("Use MM-DD, MM/DD, or MM.DD format, e.g. 05-08.")
    month, day = int(m.group(1)), int(m.group(2))
    try:
        date(2000, month, day)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return month, day


def parse_number_list(value: str, cast=float) -> list:
    items = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parsed = cast(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"Invalid numeric candidate: {item!r}") from exc
        if parsed <= 0:
            raise argparse.ArgumentTypeError("Candidate values must be positive.")
        items.append(parsed)
    if not items:
        raise argparse.ArgumentTypeError("Candidate list cannot be empty.")
    return items


def resolve_mode(args: argparse.Namespace):
    manual_fields = [args.solar is not None, args.lunar_month is not None, args.lunar_day is not None]
    if any(manual_fields):
        if not all(manual_fields):
            raise ValueError("Manual mode requires --solar, --lunar-month, and --lunar-day together.")
        if args.date:
            raise ValueError("Use either auto mode date OR manual mode, not both.")
        solar_month, solar_day = args.solar
        if not (1 <= args.lunar_month <= 12):
            raise ValueError("--lunar-month must be 1..12.")
        if not (1 <= args.lunar_day <= 30):
            raise ValueError("--lunar-day must be 1..30.")
        lunar_anchor = LunarAnchor(0, args.lunar_month, args.lunar_day, bool(args.lunar_leap))
        return "manual", None, solar_month, solar_day, lunar_anchor

    if not args.date:
        raise ValueError("Provide a Gregorian date, or use manual mode with --solar --lunar-month --lunar-day.")
    input_dt = parse_gregorian_date(args.date)
    input_lunar = solar_to_lunar(input_dt)
    return "auto", input_dt, input_dt.month, input_dt.day, input_lunar


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fit lunar/Gregorian day-gap sequence with Fourier series.")
    parser.add_argument("date", nargs="?", help="Auto mode Gregorian date, e.g. 2004-07-24, 2004/7/24, 2004.7.24")
    parser.add_argument("--solar", type=parse_mmdd, help="Manual mode solar anchor in MM-DD, MM/DD, or MM.DD format")
    parser.add_argument("--lunar-month", type=int, help="Manual mode lunar month, 1..12")
    parser.add_argument("--lunar-day", type=int, help="Manual mode lunar day, 1..30")
    parser.add_argument("--lunar-leap", action="store_true", help="Manual mode: use leap lunar month")
    parser.add_argument("--match-same-gregorian-year", action="store_true", help="Force matched lunar date to be in the same Gregorian year as the solar anchor.")
    parser.add_argument("--start", type=int, default=1901, help="start year, default 1901")
    parser.add_argument("--end", type=int, default=2100, help="end year, default 2100")
    parser.add_argument("--period", default="auto", help="Fourier period, number or 'auto'. Default: auto")
    parser.add_argument("--candidate-periods", default="8,11,19,38,57,76,95,114,133,152,171,190", help="Comma-separated periods scanned when --period auto.")
    parser.add_argument("--harmonics", default="auto", help="Number of harmonics, integer or 'auto'. Default: auto")
    parser.add_argument("--predict-year", type=int, help="Print fitted gap prediction for a target year.")
    parser.add_argument("--find-next-coincidence", action="store_true", help="Find the next exact coincidence year where gap_days == 0.")
    parser.add_argument("--after-year", type=int, help="Start next-coincidence search after this year.")
    parser.add_argument("--birthday-mode", action="store_true", help="Auto-mode birthday helper: find the next solar/lunar birthday coincidence.")
    parser.add_argument("--pretty", action="store_true", help="Print an additional human-friendly summary block.")
    parser.add_argument("--out", default=None, help="output directory")
    parser.add_argument("--no-plot", action="store_true", help="Skip fit.png generation for faster batch tests.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    mode, input_dt, solar_month, solar_day, lunar_anchor = resolve_mode(args)

    if args.birthday_mode and mode != "auto":
        raise ValueError("--birthday-mode requires auto mode with a Gregorian birth date.")

    if args.out:
        out_dir = Path(args.out)
    elif mode == "auto":
        out_dir = Path(f"out_{input_dt.isoformat()}")
    else:
        leap = "leap_" if lunar_anchor.is_leap else ""
        out_dir = Path(f"out_solar_{solar_month:02d}_{solar_day:02d}_lunar_{leap}{lunar_anchor.month:02d}_{lunar_anchor.day:02d}")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = build_gap_series(
        solar_month=solar_month,
        solar_day=solar_day,
        lunar_anchor=lunar_anchor,
        start_year=args.start,
        end_year=args.end,
        same_gregorian_year=args.match_same_gregorian_year,
    )
    result = fit_fourier(
        rows=rows,
        mode=mode,
        input_date=input_dt,
        solar_month=solar_month,
        solar_day=solar_day,
        lunar_anchor=lunar_anchor,
        same_gregorian_year=args.match_same_gregorian_year,
        period_arg=args.period,
        harmonics_arg=args.harmonics,
        candidate_periods=parse_number_list(args.candidate_periods, float),
    )

    write_csv(rows, out_dir / "gap_series.csv")
    write_json(result, out_dir / "coefficients.json")
    write_formula_py(result, out_dir / "formula.py")
    write_report(result, rows, out_dir / "report.md")
    if not args.no_plot:
        write_plot(rows, result, out_dir / "fit.png")

    hits = exact_years(rows)
    print("Done.")
    print(f"Mode: {mode}")
    if input_dt:
        print(f"Input Gregorian date: {input_dt.isoformat()}")
        print(f"Auto lunar anchor: {lunar_label(lunar_anchor)}")
    else:
        print(f"Manual solar anchor: {solar_month:02d}-{solar_day:02d}")
        print(f"Manual lunar anchor: {lunar_label(lunar_anchor, include_year=False)}")
    print(f"Match mode: {result.match_mode}")
    print(f"Selected period: {result.selected_period:g} ({result.period_mode})")
    print(f"Selected harmonics: {result.selected_harmonics} ({result.harmonics_mode})")
    print(f"Output directory: {out_dir}")
    print(f"MAE={result.mae:.4f} days, RMSE={result.rmse:.4f} days, R^2={result.r2:.6f}, BIC={result.bic:.4f}")
    print(f"Exact coincidence years: {hits if hits else 'None'}")

    prediction_row = None
    if args.predict_year is not None:
        text, prediction_row = predict_line(args.predict_year, result, rows)
        print(text)

    next_row = None
    if args.find_next_coincidence:
        if args.after_year is not None:
            after_year = args.after_year
        elif input_dt is not None:
            after_year = input_dt.year
        else:
            after_year = args.start - 1
        next_row = find_next_exact_row(rows, after_year)
        if next_row is None:
            print("Next exact coincidence year: not found")
        else:
            print(f"Next exact coincidence year: {next_row.year}")
            print(f"Coincidence date: {next_row.lunar_match_date or next_row.solar_anchor}")

    birthday_row = None
    today = date.today()
    if args.birthday_mode:
        if args.after_year is not None:
            birthday_row = find_next_exact_row(rows, args.after_year)
        else:
            birthday_row = find_next_exact_row_after_date(rows, today)
        if birthday_row is None:
            print("Next birthday coincidence year: not found")
        else:
            target_text = birthday_row.lunar_match_date or birthday_row.solar_anchor
            target_date = date.fromisoformat(target_text)
            years, days, total = years_and_days_between(today, target_date)
            print(f"Next birthday coincidence year: {birthday_row.year}")
            print(f"Coincidence date: {target_text}")
            print(f"Age on that day: {birthday_age(input_dt, target_date)}")
            if target_date >= today:
                print(f"Time from today: {years} years and {days} days ({total} days total)")

    if args.pretty:
        print(
            format_pretty_summary(
                result=result,
                rows=rows,
                out_dir=str(out_dir),
                prediction_year=args.predict_year,
                prediction_row=prediction_row,
                next_row=next_row,
                birthday_row=birthday_row,
                birth_date=input_dt,
                today=today,
            )
        )


if __name__ == "__main__":
    main()
