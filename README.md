# Lunar Gap Fit

A small Python tool for studying how a Gregorian date and its corresponding Chinese lunar date drift across years.

It can:

- convert a Gregorian date to a Chinese lunar month/day;
- generate a 1901–2100 year-by-year day-gap sequence;
- manually compare a Gregorian anchor such as `05-08` with a lunar anchor such as lunar `3/23`;
- fit the gap sequence with a Fourier model;
- predict fitted gaps for a target year;
- find the next year when the Gregorian and lunar anchors exactly coincide;
- provide birthday-style coincidence summaries;
- export CSV data, model coefficients, a standalone fitted function, a plot, and a Markdown report.

## Why this exists

Some Gregorian-lunar date pairs appear to repeat near a 19-year rhythm, but the actual sequence is not a simple sine wave. It behaves more like a sawtooth-like quasi-periodic sequence with calendar corrections, leap months, and slow envelope changes.

This tool turns that intuition into data.

## Install

```bash
git clone https://github.com/Xhou-J/ri.git
cd ri
pip install -e .
```

Or install requirements only:

```bash
pip install -r requirements.txt
```

## Quick start

Auto mode:

```bash
python -m lunar_gap_fit 2004-07-24 --out out_2004_07_24
```

After installation, the console command also works:

```bash
lunar-gap-fit 2004-07-24 --out out_2004_07_24
```

The input date can use hyphens, slashes, or dots. Single-digit month/day values are supported:

```text
YYYY-MM-DD
YYYY-M-D
YYYY/MM/DD
YYYY/M/D
YYYY.MM.DD
YYYY.M.D
```

Examples:

```bash
lunar-gap-fit 2008-07-10 --out out_2008_07_10
lunar-gap-fit 2008/7/10 --out out_2008_07_10
lunar-gap-fit 2008.7.10 --out out_2008_07_10
```

## Manual anchor mode

Use this when you want to compare a chosen Gregorian month/day with a chosen lunar month/day.

Example: Gregorian May 8 vs lunar March 23.

```bash
lunar-gap-fit --solar 05-08 --lunar-month 3 --lunar-day 23 --out out_0508_lunar_0323
```

The `--solar` value supports:

```text
MM-DD
M-D
MM/DD
M/D
MM.DD
M.D
```

Examples:

```bash
lunar-gap-fit --solar 5-8 --lunar-month 3 --lunar-day 23
lunar-gap-fit --solar 5/8 --lunar-month 3 --lunar-day 23
lunar-gap-fit --solar 5.8 --lunar-month 3 --lunar-day 23
```

Leap lunar month example:

```bash
lunar-gap-fit --solar 05-23 --lunar-month 4 --lunar-day 1 --lunar-leap --out out_leap_0401
```

## Matching modes

Default matching chooses the lunar date nearest to the Gregorian anchor.

```bash
lunar-gap-fit 2004-07-24
```

Force the matched lunar date to be inside the same Gregorian year:

```bash
lunar-gap-fit 2004-07-24 --match-same-gregorian-year
```

## Helper options

Predict the fitted gap for a target year:

```bash
lunar-gap-fit 2004-07-24 --predict-year 2042
```

Find the next exact coincidence year after the input year:

```bash
lunar-gap-fit 2004-07-24 --find-next-coincidence
```

Search after a specific year:

```bash
lunar-gap-fit 2004-07-24 --find-next-coincidence --after-year 2026
```

Birthday shortcut:

```bash
lunar-gap-fit 2004-07-24 --birthday-mode
```

Print an additional human-friendly summary block:

```bash
lunar-gap-fit 2004-07-24 --birthday-mode --predict-year 2042 --pretty --no-plot
```

Common helper flags:

```text
--predict-year YEAR
--find-next-coincidence
--after-year YEAR
--birthday-mode
--pretty
```

Example pretty output:

```text
== Lunar Gap Fit Summary ==
Solar anchor      : 07-24
Lunar anchor      : 6/8
Match mode        : nearest
Best Fourier fit  : period=76, harmonics=1
Fit error         : MAE=9.40 days, RMSE=26.31 days
Exact years       : 1909, 1928, 1939, 1958, 2004, 2042, 2061, 2080
Prediction 2042   : fitted gap 0.12 days, rounded 0 days; actual 0 days
Next birthday hit : 2042-07-24 (age 38)
Time from today   : 16 years and 56 days (5900 days total)
Output folder     : out_2004-07-24
=============================
```

## Period selection

By default, the model does not assume one fixed period.

```bash
--period auto
--harmonics auto
```

Default candidate periods:

```text
8, 11, 19, 38, 57, 76, 95, 114, 133, 152, 171, 190
```

Use a fixed period and harmonic count if you want a specific model:

```bash
lunar-gap-fit 2004-07-24 --period 95 --harmonics 40
```

## Outputs

Each run creates:

```text
gap_series.csv       # year-by-year gap data
coefficients.json    # selected model, coefficients, and error metrics
formula.py           # standalone fitted function
fit.png              # plot, unless --no-plot is used
report.md            # short Markdown report
```

## Gap definition

```text
gap(Y) = matched lunar-anchor date - date(Y, solar_month, solar_day)
```

Positive means the lunar date is later.  
Negative means the lunar date is earlier.  
Zero means exact coincidence.

## Development

Run tests:

```bash
python tests/test_basic.py
```

Manual smoke commands:

```bash
python -m lunar_gap_fit 2004-07-24 --no-plot
python -m lunar_gap_fit 2005.2.4 --no-plot
python -m lunar_gap_fit 2005/2/4 --no-plot
python -m lunar_gap_fit 2004-07-24 --predict-year 2042 --no-plot
python -m lunar_gap_fit 2004-07-24 --find-next-coincidence --after-year 2026 --no-plot
python -m lunar_gap_fit 2004-07-24 --birthday-mode --no-plot
python -m lunar_gap_fit 2004-07-24 --birthday-mode --predict-year 2042 --pretty --no-plot
```

## Notes

This is a modeling and fitting tool, not an official almanac. The built-in lunar table covers 1900–2100, with 1901–2100 recommended for fitting.
