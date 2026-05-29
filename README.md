# Lunar Gap Fit

A small Python tool for studying how a Gregorian date and its corresponding Chinese lunar date drift across years.

It can:

- convert a Gregorian date to a Chinese lunar month/day;
- generate a 1901–2100 year-by-year day-gap sequence;
- manually compare a Gregorian anchor such as `05-08` with a lunar anchor such as lunar `3/23`;
- fit the gap sequence with a Fourier model;
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

The input date must use hyphens:

```text
YYYY-MM-DD
```

For example:

```bash
lunar-gap-fit 2008-07-10 --out out_2008_07_10
```

## Manual anchor mode

Use this when you want to compare a chosen Gregorian month/day with a chosen lunar month/day.

Example: Gregorian May 8 vs lunar March 23.

```bash
lunar-gap-fit --solar 05-08 --lunar-month 3 --lunar-day 23 --out out_0508_lunar_0323
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

## Notes

This is a modeling and fitting tool, not an official almanac. The built-in lunar table covers 1900–2100, with 1901–2100 recommended for fitting.
