from __future__ import annotations

from datetime import date
from typing import Optional

from .fitting import fitted_value
from .models import FitResult, GapRow


def exact_years(rows: list[GapRow]) -> list[int]:
    return [row.year for row in rows if row.gap_days == 0]


def row_for_year(rows: list[GapRow], year: int) -> Optional[GapRow]:
    for row in rows:
        if row.year == year:
            return row
    return None


def find_next_exact_row(rows: list[GapRow], after_year: int) -> Optional[GapRow]:
    for row in rows:
        if row.year > after_year and row.gap_days == 0:
            return row
    return None


def find_next_exact_row_after_date(rows: list[GapRow], after_date: date) -> Optional[GapRow]:
    for row in rows:
        if row.gap_days != 0 or not row.solar_anchor:
            continue
        try:
            solar = date.fromisoformat(row.solar_anchor)
        except ValueError:
            continue
        if solar >= after_date:
            return row
    return None


def birthday_age(birth_date: date, target_date: date) -> int:
    years = target_date.year - birth_date.year
    try:
        birthday_this_year = birth_date.replace(year=target_date.year)
    except ValueError:
        birthday_this_year = date(target_date.year, 2, 28)
    if target_date < birthday_this_year:
        years -= 1
    return years


def add_years_safe(dt: date, years: int) -> date:
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return date(dt.year + years, 2, 28)


def years_and_days_between(start: date, end: date) -> tuple[int, int, int]:
    total = (end - start).days
    if total < 0:
        return 0, total, total
    years = end.year - start.year
    anniversary = add_years_safe(start, years)
    if anniversary > end:
        years -= 1
        anniversary = add_years_safe(start, years)
    days = (end - anniversary).days
    return years, days, total


def predict_line(year: int, result: FitResult, rows: list[GapRow]) -> tuple[str, Optional[GapRow]]:
    fitted = fitted_value(year, result)
    row = row_for_year(rows, year)
    if row is not None and row.gap_days is not None:
        return (
            f"Predicted fitted gap for {year}: {fitted:.4f} days, rounded {round(fitted)} days\n"
            f"Actual gap for {year}: {row.gap_days} days; matched lunar date: {row.lunar_match_date}",
            row,
        )
    return (
        f"Predicted fitted gap for {year}: {fitted:.4f} days, rounded {round(fitted)} days\n"
        f"Actual gap for {year}: unavailable outside selected rows",
        row,
    )


def format_years(years: list[int], limit: int = 12) -> str:
    if not years:
        return "None"
    shown = years[:limit]
    text = ", ".join(str(y) for y in shown)
    rest = len(years) - len(shown)
    if rest > 0:
        text += f" ... (+{rest} more)"
    return text


def format_pretty_summary(
    *,
    result: FitResult,
    rows: list[GapRow],
    out_dir: str,
    prediction_year: Optional[int] = None,
    prediction_row: Optional[GapRow] = None,
    next_row: Optional[GapRow] = None,
    birthday_row: Optional[GapRow] = None,
    birth_date: Optional[date] = None,
    today: Optional[date] = None,
) -> str:
    lines = [
        "== Lunar Gap Fit Summary ==",
        f"Solar anchor      : {result.solar_month:02d}-{result.solar_day:02d}",
        f"Lunar anchor      : {result.input_lunar.get('month')}/{result.input_lunar.get('day')}",
        f"Match mode        : {result.match_mode}",
        f"Best Fourier fit  : period={result.selected_period:g}, harmonics={result.selected_harmonics}",
        f"Fit error         : MAE={result.mae:.2f} days, RMSE={result.rmse:.2f} days",
        f"Exact years       : {format_years(exact_years(rows))}",
    ]

    if prediction_year is not None:
        fitted = fitted_value(prediction_year, result)
        if prediction_row is not None and prediction_row.gap_days is not None:
            actual = f"actual {prediction_row.gap_days} days"
        else:
            actual = "actual unavailable"
        lines.append(
            f"Prediction {prediction_year}   : fitted gap {fitted:.2f} days, rounded {round(fitted)} days; {actual}"
        )

    if next_row is not None:
        lines.append(f"Next exact hit   : {next_row.lunar_match_date or next_row.solar_anchor}")

    if birthday_row is not None:
        hit_text = birthday_row.lunar_match_date or birthday_row.solar_anchor
        if birth_date is not None and hit_text:
            target = date.fromisoformat(hit_text)
            lines.append(f"Next birthday hit : {hit_text} (age {birthday_age(birth_date, target)})")
            if today is not None and target >= today:
                years, days, total = years_and_days_between(today, target)
                lines.append(f"Time from today   : {years} years and {days} days ({total} days total)")
        else:
            lines.append(f"Next birthday hit : {hit_text}")

    lines.extend([
        f"Output folder     : {out_dir}",
        "=============================",
    ])
    return "\n".join(lines)
