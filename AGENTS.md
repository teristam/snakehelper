# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/snakehelper/` (core logic in `SnakeIOHelper.py`).
- Tests: `tests/` (e.g., `tests/test_snakehelper.py`; sample Snakefile in `tests/make_files/`).
- Docs & examples: `docs/`, `examples/`.
- Build/config: `pyproject.toml`, `.coveragerc`, `uv.lock`.

## Build, Test, and Development Commands
- Environment: Python 3.11+.
- Install (editable): `pip install -e .` (or `uv pip install -e .`).
- Run tests: `pytest -q` from repo root.
- Coverage: `pytest -q --cov=snakehelper` (honors `.coveragerc`; requires `pytest-cov`).
- Clean caches: remove `__pycache__/`, `.pytest_cache/`, and `.snakemake/` if needed.

## Coding Style & Naming Conventions
- Style: PEP 8; 4‑space indents; add type hints where practical.
- Naming: functions/variables `snake_case`, classes `CapWords`, modules `lower_snake_case`.
- Imports: stdlib → third‑party → local, grouped and alphabetized.
- Docstrings: concise, imperative summaries; include Args/Returns when helpful.

## Testing Guidelines
- Framework: `pytest`.
- Layout: tests live in `tests/`; files named `test_*.py`; functions `test_*`.
- Example: validate `getSnake` with `tests/make_files/workflow_common.smk` targets.
- Coverage focus: core package `snakehelper`; prefer unit tests over heavyweight integration.

## Commit & Pull Request Guidelines
- Commits: short, imperative summaries (e.g., "add option to skip working dir change"); optional tags like `[feature]`, `[doc]` as seen in history.
- PRs: describe change, rationale, and scope; link issues; include updated tests and relevant logs/screens.
- Expectations: PRs pass `pytest` locally; keep diffs minimal and focused.

## Security & Configuration Tips
- Windows builds: Snakemake may require Microsoft C++ Build Tools (see README screenshots).
- Interactive dev: set `SNAKEMAKE_DEBUG_ROOT` (or add to `.env`) to auto‑switch working dir when exploring in notebooks/VS Code.
- Secrets: never commit credentials; `.env` is for local use only and should not contain production secrets.
