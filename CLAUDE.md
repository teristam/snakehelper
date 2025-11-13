# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**snakehelper** is a Python library that enables seamless development of Snakemake workflow scripts both inside and outside of the Snakemake environment. It allows developers to extract input/output file information from Snakemake workflows without running the full workflow, making it possible to develop and debug scripts in Jupyter notebooks, VS Code interactive cells, or as standalone scripts.

### Core Architecture

The library provides a dual-mode execution pattern:
- **Snakemake mode**: When running inside a Snakemake workflow, it extracts I/O from the injected `snakemake` object
- **Standalone mode**: When running outside Snakemake, it compiles the workflow using `snakemake.api` to extract I/O information

Key component:
- `src/snakehelper/SnakeIOHelper.py` - Contains all core logic:
  - `getSnake()`: Main entry point that detects execution mode and returns input/output dictionaries
  - `IOParser`: Compiles workflows using Snakemake API (>= 9.0) to build DAG and extract I/O
  - `makeFolders()`: Creates output directories as needed

The detection mechanism uses `locals()` dictionary inspection to determine if the `snakemake` object exists, automatically switching between modes without code changes.

## Development Commands

### Setup and Installation
```bash
# Install in development mode
pip install -e .

# Using uv (preferred for CI/testing)
uv sync --frozen
```

### Testing
```bash
# Run all tests
pytest

# Run all tests (via uv)
uv run pytest -q

# Run a specific test
pytest tests/test_snakehelper.py::test_parse_workflow

# Run tests with verbose output
pytest -v
```

### Test Structure
Tests are in `tests/test_snakehelper.py` and use a sample Snakefile at `tests/make_files/workflow_common.smk` with a `sort_spikes` rule that demonstrates wildcard-based I/O patterns.

## Important Technical Details

### Snakemake API Version
This project requires **Snakemake >= 9.0.0** and uses the public `snakemake.api` module. Previous versions used private APIs. The compilation process in `IOParser.compileWorkflow()` uses:
- `SnakemakeApi` context manager
- `workflow()` with resource settings and snakefile path
- `dag()` with DAG settings including targets
- Dry-run executor to materialize the DAG without executing rules

### Working Directory Handling
When developing in VS Code interactive cells, the working directory may differ from project root. The library supports:
- `SNAKEMAKE_DEBUG_ROOT` environment variable to auto-switch to project root
- `.env` file loading in VS Code (not loaded outside VS Code)
- `change_working_dir` parameter in `getSnake()` to disable auto-switching

### Missing Input Handling
If Snakemake reports missing input files during DAG compilation, `IOParser.compileWorkflow()` automatically creates placeholder files/directories and retries the dry-run once. This is critical for workflows where intermediate files don't exist yet.

### Cross-Platform Path Handling
Tests use `Path()` comparisons to handle Windows vs POSIX path separator differences. When working with file paths from Snakemake output objects, convert to `Path` for comparisons.

## Windows-Specific Requirements

The `datrie` package (Snakemake dependency) requires Microsoft C++ Build Tools on Windows. Users need to install Visual Studio Build Tools with C++ development tools before running `pip install`.
