# Security Policy

## Supported versions

Security updates are considered for the current `main` branch and the latest tagged release.

| Version | Supported |
| --- | --- |
| `main` | Yes |
| `0.1.x` | Yes |

## Reporting a vulnerability

If you find a security issue, please do not open a public issue with exploit details.

Instead, contact the maintainer privately through the GitHub profile linked from this repository, or open a minimal public issue that states there is a security concern without sensitive details.

Please include:

- the affected version or commit;
- a short description of the issue;
- steps to reproduce, if safe to share;
- the potential impact;
- any suggested fix.

## Scope

This project is a local command-line tool for Gregorian and Chinese lunar date analysis. Security-sensitive reports are most likely to involve unsafe file handling, unexpected code execution, dependency issues, or generated-output behavior.

## Response expectations

The maintainer will review reports on a best-effort basis. Confirmed issues will be fixed in `main` and included in the next release when appropriate.
