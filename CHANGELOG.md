# Changelog

## 0.2.1 (2025-09-04)
- Fix: Add compatibility with Snakemake 9 API using `snakemake.api` with a legacy fallback.
- Fix: Robust DAG construction by handling missing raw inputs during dry-run (create minimal placeholders and retry once).
- Tests: Confirmed all tests pass against Snakemake 9.0.0.

## 0.2.0
- Initial version in this repo layout.

