from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_gap_fit.calendar import (
    CALENDAR_SOURCE_NAME,
    CALENDAR_SOURCE_URL,
    LUNAR_INFO,
    LUNAR_INFO_SHA256,
    LunarAnchor,
    solar_to_lunar,
    lunar_to_solar,
)
from lunar_gap_fit.cli import (
    parse_gregorian_date,
    parse_mmdd,
    parse_number_list,
    resolve_output_dir,
    validate_harmonics,
    validate_period,
)
from lunar_gap_fit.features import birthday_age, find_next_exact_row, years_and_days_between
from lunar_gap_fit.fitting import fit_fourier
from lunar_gap_fit.export import compute_interactive_fit, days_in_year
from lunar_gap_fit.series import build_gap_series


def run_cli(*args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path if not existing else os.pathsep.join([src_path, existing])
    return subprocess.run(
        [sys.executable, "-m", "lunar_gap_fit", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def test_flexible_gregorian_date_parsing():
    assert parse_gregorian_date("2005-02-04") == date(2005, 2, 4)
    assert parse_gregorian_date("2005-2-4") == date(2005, 2, 4)
    assert parse_gregorian_date("2005/02/04") == date(2005, 2, 4)
    assert parse_gregorian_date("2005/2/4") == date(2005, 2, 4)
    assert parse_gregorian_date("2005.02.04") == date(2005, 2, 4)
    assert parse_gregorian_date("2005.2.4") == date(2005, 2, 4)


def test_flexible_mmdd_parsing():
    assert parse_mmdd("05-08") == (5, 8)
    assert parse_mmdd("5-8") == (5, 8)
    assert parse_mmdd("05/08") == (5, 8)
    assert parse_mmdd("5/8") == (5, 8)
    assert parse_mmdd("05.08") == (5, 8)
    assert parse_mmdd("5.8") == (5, 8)


def test_cli_candidate_validation_helpers():
    assert validate_period("auto") == "auto"
    assert validate_period("19") == "19"
    assert validate_harmonics("auto") == "auto"
    assert validate_harmonics("3") == "3"
    assert parse_number_list("8, 19,38") == [8.0, 19.0, 38.0]


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


def test_calendar_source_metadata_and_fixture_samples():
    encoded = ",".join(str(item) for item in LUNAR_INFO).encode("ascii")
    assert hashlib.sha256(encoded).hexdigest() == LUNAR_INFO_SHA256
    assert "Hong Kong Observatory" in CALENDAR_SOURCE_NAME
    assert CALENDAR_SOURCE_URL == "https://www.hko.gov.hk/en/gts/time/conversion.htm"

    samples = [
        ("2004-01-22", LunarAnchor(2004, 1, 1, False), "Chinese New Year 2004"),
        ("2004-07-24", LunarAnchor(2004, 6, 8, False), "project anchor sample"),
        ("2020-01-25", LunarAnchor(2020, 1, 1, False), "Chinese New Year 2020"),
        ("2023-01-22", LunarAnchor(2023, 1, 1, False), "Chinese New Year 2023"),
        ("2024-02-10", LunarAnchor(2024, 1, 1, False), "Chinese New Year 2024"),
        ("2042-07-24", LunarAnchor(2042, 6, 8, False), "documented coincidence sample"),
        ("2100-02-09", LunarAnchor(2100, 1, 1, False), "Chinese New Year 2100"),
        ("2100-12-31", LunarAnchor(2100, 12, 1, False), "HKO range end sample"),
    ]
    for solar_text, lunar, note in samples:
        solar = date.fromisoformat(solar_text)
        assert solar_to_lunar(solar) == lunar, note
        assert lunar_to_solar(lunar) == solar, note


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
    next_row = find_next_exact_row(rows, 2004)
    assert next_row is not None
    assert next_row.year == 2042
    assert next_row.solar_anchor == "2042-07-24"


def test_birthday_age_and_countdown():
    assert birthday_age(date(2004, 7, 24), date(2042, 7, 24)) == 38
    years, days, total = years_and_days_between(date(2026, 5, 29), date(2042, 7, 24))
    assert years == 16
    assert days == 56
    assert total == 5900


def test_cli_auto_success_writes_expected_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "auto"
        result = run_cli("2004-07-24", "--no-plot", "--out", str(out_dir))
        assert result.returncode == 0, result.stderr
        assert "Done." in result.stdout
        for filename in ["gap_series.csv", "coefficients.json", "formula.py", "report.md", "interactive.html"]:
            assert (out_dir / filename).exists()
        assert not (out_dir / "fit.png").exists()


def test_cli_no_interactive_skips_html():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "auto"
        result = run_cli("2004-07-24", "--no-plot", "--no-interactive", "--out", str(out_dir))
        assert result.returncode == 0, result.stderr
        assert (out_dir / "gap_series.csv").exists()
        assert not (out_dir / "interactive.html").exists()


def test_interactive_html_is_offline_and_precise():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "interactive"
        result = run_cli("2004-07-24", "--no-plot", "--out", str(out_dir))
        assert result.returncode == 0, result.stderr

        html = (out_dir / "interactive.html").read_text(encoding="utf-8")
        assert "Lunar Gap Interactive Fit" in html
        assert "yearSelect" in html
        assert "daySlider" in html
        assert "zoomSlider" in html
        assert "panSlider" in html
        assert "new Worker" in html
        assert "Hong Kong Observatory" in html
        assert '<script src="' not in html
        assert "<script src='" not in html
        assert '<link href="' not in html
        assert "<link href='" not in html

        payload_match = re.search(
            r'<script id="payload" type="application/json">(.*?)</script>',
            html,
            flags=re.DOTALL,
        )
        assert payload_match is not None
        payload = json.loads(payload_match.group(1))
        assert payload["calendar"]["sourceUrl"] == CALENDAR_SOURCE_URL
        assert payload["calendar"]["lunarInfoSha256"] == LUNAR_INFO_SHA256
        assert len(payload["calendar"]["lunarInfo"]) == 201
        assert payload["initial"]["date"] == "2004-07-24"
        assert payload["initial"]["daysInYear"] == 366
        assert days_in_year(2005) == 365

        direct = compute_interactive_fit(
            date(2004, 7, 24),
            start_year=1901,
            end_year=2100,
            same_gregorian_year=False,
            period_arg="auto",
            harmonics_arg="auto",
            candidate_periods=[8, 11, 19, 38, 57, 76, 95, 114, 133, 152, 171, 190],
        )
        assert payload["initial"]["lunar"] == direct["lunar"]
        assert payload["initial"]["fit"]["selected_period"] == direct["fit"]["selected_period"]
        assert payload["initial"]["fit"]["selected_harmonics"] == direct["fit"]["selected_harmonics"]
        assert payload["initial"]["fit"]["cos_coefficients"] == direct["fit"]["cos_coefficients"]


def test_cli_slash_date_and_manual_success():
    with tempfile.TemporaryDirectory() as tmp:
        slash_out = Path(tmp) / "slash"
        manual_out = Path(tmp) / "manual"

        slash = run_cli("2005/2/4", "--no-plot", "--out", str(slash_out))
        assert slash.returncode == 0, slash.stderr
        assert "Input Gregorian date: 2005-02-04" in slash.stdout

        manual = run_cli("--solar", "5-8", "--lunar-month", "3", "--lunar-day", "23", "--no-plot", "--out", str(manual_out))
        assert manual.returncode == 0, manual.stderr
        assert "Mode: manual" in manual.stdout


def test_cli_helper_flags_success():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "helper"
        result = run_cli(
            "2004-07-24",
            "--predict-year",
            "2042",
            "--find-next-coincidence",
            "--after-year",
            "2026",
            "--birthday-mode",
            "--pretty",
            "--no-plot",
            "--out",
            str(out_dir),
        )
        assert result.returncode == 0, result.stderr
        assert "== Lunar Gap Fit Summary ==" in result.stdout
        assert "Prediction 2042" in result.stdout
        assert "Next birthday hit" in result.stdout


def assert_cli_usage_error(*args: str, expected: str) -> None:
    result = run_cli(*args)
    assert result.returncode == 2
    assert "usage:" in result.stderr
    assert expected in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_usage_errors_are_friendly():
    assert_cli_usage_error("not-a-date", expected="Use YYYY-MM-DD")
    assert_cli_usage_error("--solar", "5-8", "--lunar-month", "3", expected="Manual mode requires")
    assert_cli_usage_error("2004-07-24", "--solar", "5-8", "--lunar-month", "3", "--lunar-day", "23", expected="Use either auto mode")
    assert_cli_usage_error("2004-07-24", "--period", "abc", expected="--period must be")
    assert_cli_usage_error("2004-07-24", "--harmonics", "abc", expected="--harmonics must be")
    assert_cli_usage_error("2004-07-24", "--candidate-periods", ",,,", expected="Candidate list cannot be empty")
    assert_cli_usage_error("1900-02-01", "--no-plot", expected="Interactive output supports Gregorian dates")


if __name__ == "__main__":
    test_flexible_gregorian_date_parsing()
    test_flexible_mmdd_parsing()
    test_cli_candidate_validation_helpers()
    test_round_trip_known_dates()
    test_calendar_source_metadata_and_fixture_samples()
    test_auto_fit()
    test_manual_fit()
    test_find_next_exact_year()
    test_birthday_age_and_countdown()
    test_cli_auto_success_writes_expected_outputs()
    test_cli_no_interactive_skips_html()
    test_interactive_html_is_offline_and_precise()
    test_cli_slash_date_and_manual_success()
    test_cli_helper_flags_success()
    test_cli_usage_errors_are_friendly()
    print("basic tests passed")
