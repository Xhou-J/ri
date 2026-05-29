from __future__ import annotations

from datetime import date


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


def age_on_date(birth_date: date, target_date: date) -> int:
    years = target_date.year - birth_date.year
    birthday_this_year = add_years_safe(birth_date, years)
    if target_date < birthday_this_year:
        years -= 1
    return years


def next_annual_date_on_or_after(anchor: date, today: date) -> date:
    candidate = add_years_safe(anchor, today.year - anchor.year)
    if candidate < today:
        candidate = add_years_safe(anchor, today.year - anchor.year + 1)
    return candidate


def format_countdown(anchor: date, target: date, today: date) -> str:
    years, days, total = years_and_days_between(today, target)
    age = age_on_date(anchor, target)
    if target < today:
        return f"{target.isoformat()} (age {age}); already passed by {-total} days"
    return f"{target.isoformat()} (age {age}); {years} years and {days} days away ({total} days total)"
