# Contributing

Contributions are welcome. Please keep changes focused, documented, and easy to review.

## Local setup

```bash
python -m pip install --upgrade pip
pip install -e .
python tests/test_basic.py
```

## Development guidelines

- Keep the command-line interface simple and predictable.
- Avoid adding heavy dependencies unless they are clearly necessary.
- Prefer small, reviewable changes over large rewrites.
- Add or update tests when changing date conversion, gap-series generation, fitting behavior, or exported files.
- Keep README examples aligned with actual command output.

## Calendar accuracy

This project uses a built-in Chinese lunar calendar table for 1900-2100. If you change calendar conversion logic or table data, please add known-date tests, round-trip tests, and a note explaining the data source or correction.

## Reports and generated output

Generated files such as `gap_series.csv`, `coefficients.json`, `formula.py`, `fit.png`, and `report.md` should remain deterministic for the same inputs, except when an option intentionally depends on today's date.

## Security

Please see `SECURITY.md` for vulnerability reporting guidance.
