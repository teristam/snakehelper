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
  - `prepare_logger()`: Sets up loguru-based logging with stderr redirection
  - `StreamToLogger`: Class that redirects stderr writes to the log file

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

### Error Logging and Stderr Capture
The library includes a comprehensive logging mechanism that captures errors and stderr output to Snakemake log files:

**Key Features:**
- **Automatic Log Setup**: When `redirect_error=True` (default) in `getSnake()` and a log file is defined in the Snakemake rule, logging is automatically configured using loguru
- **Stderr Redirection**: The `StreamToLogger` class redirects all stderr writes to the log file while maintaining ERROR-level output to the terminal
- **Compilation Error Capture**: During workflow compilation, stderr is captured and can be written to log files if errors occur
- **Error Logging**: The `IOParser._write_error_to_log()` method writes exception tracebacks, error messages, and captured stderr to the appropriate log file

**How It Works:**
1. When `getSnake()` is called with `redirect_error=True` and a log file exists, it calls `prepare_logger(logfile)`
2. `prepare_logger()` configures loguru to write to the log file with full backtrace and diagnostic info
3. `sys.stderr` is replaced with a `StreamToLogger` instance that writes to both the log file and terminal stderr
4. If exceptions occur during compilation or execution, they're caught and written to the rule's log file with full context
5. The `IOParser` extracts log file paths from the DAG during compilation via `_extract_log_files()`

**Testing:**
- `test_stderr_capture_and_logging`: Verifies stderr output is captured to log files
- `test_error_logging_mechanism`: Tests that exceptions are properly logged with tracebacks
- `test_cli_execution_error_logfile`: Tests log creation when running via Snakemake CLI (workflow with errors)
- `test_cli_execution_normal_logfile`: Tests log creation when running via Snakemake CLI (normal execution)

## Windows-Specific Requirements

The `datrie` package (Snakemake dependency) requires Microsoft C++ Build Tools on Windows. Users need to install Visual Studio Build Tools with C++ development tools before running `pip install`.
