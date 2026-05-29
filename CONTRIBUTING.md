# Contributing

Contributions are welcome.

## Local setup

```bash
pip install -e .
python tests/test_basic.py
```

## Style

Please keep the command-line interface simple and avoid adding heavy dependencies unless necessary.

## Calendar accuracy

This online version uses the `lunardate` package for Chinese lunar conversion. If you change the calendar conversion logic, please add round-trip tests and document the data source.
