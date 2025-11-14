"""Helper utilities for working with Snakemake I/O in scripts (Snakemake >= 9)."""

import os
from pathlib import Path
from types import SimpleNamespace

from snakemake.api import DAGSettings as _SMDAGSettings
from snakemake.api import SnakemakeApi as _SMSnakemakeApi
from snakemake.settings.types import ResourceSettings as _SMResourceSettings
from loguru import logger
import sys


def _apply_jupyter_asyncio_patch():
    """Apply nest_asyncio patch if running in Jupyter environment.

    This allows Snakemake's asyncio code to run inside Jupyter notebooks,
    which already have an active event loop.
    """
    try:
        # Check if we're in an IPython/Jupyter environment
        get_ipython()  # This will raise NameError if not in IPython

        # Check if there's already a running event loop
        import asyncio
        try:
            asyncio.get_running_loop()
            # If we got here, there's a running loop - apply the patch
            import nest_asyncio
            nest_asyncio.apply()
        except RuntimeError:
            # No running loop, no need to patch
            pass
    except (NameError, ImportError):
        # Not in IPython/Jupyter or nest_asyncio not available
        pass

def makeFolders(output):
    """Create folders for output paths if they do not exist.

    Supports Snakemake ``Namedlist``/``OutputFiles`` across versions, simple
    iterables, dict-like objects, and simple namespaces.
    """

    def _iter_output_values(obj):
        # Prefer mapping-style APIs when available
        if hasattr(obj, 'items'):
            for _, v in obj.items():
                yield v
            return
        if hasattr(obj, 'values'):
            for v in obj.values():
                yield v
            return
        # Fallback: iterate if it behaves like a sequence (but not a string)
        try:
            from collections.abc import Iterable  # py311 stdlib
            if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
                for v in obj:
                    yield v
                return
        except Exception:
            pass
        # Simple namespace objects
        if hasattr(obj, '__dict__'):
            for v in obj.__dict__.values():
                yield v
            return
        # Last resort: treat the object itself as a single path value
        yield obj

    for v in _iter_output_values(output):
        p = Path(str(v))
        if p.suffix == '':  # looks like a directory
            if not os.path.exists(p):
                os.makedirs(p)
                print('Created folder:' + str(p))
        else:
            parent = p.parent
            if not os.path.exists(parent):
                os.makedirs(parent)
                print('Created folder:' + str(parent))

def getSnake(locals:dict,snakefile:str, targets:list,
             rule:str, redirect_error  = True,
            createFolder:bool = True, return_snake_obj=False, change_working_dir=True):
    """Return the input and output files according to a snakemake file, target and running rule

    Args:
    locals (dict): Local variables dictionary of caller script
    snakefile (str): Snakefile location
    targets (list): The file or files that are created when the rule is executed
    rule (str): The rule for which you want to determine the input and output files
    createFolder (bool): Whether or not to create output folders. Default is True.

    Returns:
    Tuple: A tuple of dictionaries containing input and output file names, as defined in the snakemake file.
    """

    if 'snakemake' not in locals:
        #We are running standlone mode

        #Auto switch to project root folder if SNAKE_ROOT is set
        snake_root = os.environ.get('SNAKEMAKE_DEBUG_ROOT')
        if snake_root is not None and change_working_dir:
            print('Changing working directory to:' + snake_root)
            os.chdir(snake_root)

        parser = None
        try:
            parser = IOParser(snakefile, targets)
            io = parser.getInputOutput4rule(rule)
            if createFolder:
                makeFolders(io.output)

            if redirect_error and createFolder:
                if len(io.log) > 0 :
                    logfile = io.log[0]
                    prepare_logger(logfile)

            if return_snake_obj:
                return (io.input, io.output, io)
            else:
                return (io.input, io.output)
        except Exception as e:
            # If we have a parser and it has log files, try to write the error
            if parser is not None and hasattr(parser, 'log_files') and rule in parser.log_files:
                parser._write_error_to_log(rule, e)
            raise
    else:
        if createFolder:
            makeFolders(locals['snakemake'].output)

        if redirect_error and createFolder:
            if hasattr(locals['snakemake'], 'log') and len(locals['snakemake'].log) > 0:
                logfile = locals['snakemake'].log[0]
                prepare_logger(logfile)

        if return_snake_obj:
            return (locals['snakemake'].input, locals['snakemake'].output, locals['snakemake'])
        else:
            return (locals['snakemake'].input, locals['snakemake'].output)
        

def prepare_logger(logfile):
    logger.remove()  # Remove default handler
    logger.add(logfile,  backtrace=True, diagnose=True)
    logger.add(sys.stderr, level="ERROR")  # Also keep stderr output

    sys.stderr = StreamToLogger(logger)


def makeDummpyOutput(output):
    for o in output:
        Path(o).touch()

class IOParser:
    def __init__(self, snakefile:str, targets:list):
        self.snakefile = snakefile
        self.targets = targets
        self.log_files = {}  # Will map rule names to their log files
        self.dag = None

        try:
            self.workflow = self.compileWorkflow()
            if not hasattr(self.workflow, 'dag') or self.workflow.dag is None:
                raise RuntimeError('Unable to access Snakemake DAG after dry-run execution')
            self.dag = self.workflow.dag

            # Extract log files from all jobs
            self._extract_log_files()
        except Exception as e:
            # If we have a partially built DAG, try to extract log files from it
            if self.dag is not None:
                self._extract_log_files()
            raise


    def compileWorkflow(self):
        """Compile the workflow and build a DAG via a dry-run using Snakemake API.

        Returns an object exposing a ``dag`` attribute for downstream use.
        """
        import sys
        from io import StringIO

        # Apply nest_asyncio patch if running in Jupyter
        _apply_jupyter_asyncio_patch()

        # Capture stderr for potential logging
        stderr_capture = StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_capture

        wf_api = None
        try:
            with _SMSnakemakeApi() as api:
                wf_api = api.workflow(
                    resource_settings=_SMResourceSettings(cores=1),
                    snakefile=Path(self.snakefile),
                    workdir=None,
                )
                dag_api = wf_api.dag(
                    dag_settings=_SMDAGSettings(
                        targets=set(self.targets),
                        forceall=True,
                    )
                )
                # execute with dryrun executor to materialize DAG
                from snakemake.exceptions import MissingInputException

                try:
                    dag_api.execute_workflow(executor="dryrun", updated_files=[])
                except MissingInputException as ex:
                    # Parse and create placeholder inputs if needed, then retry once.
                    msg = str(ex)
                    missing = []
                    if "affected files:" in msg:
                        tail = msg.split("affected files:")[-1].strip()
                        for line in tail.splitlines():
                            line = line.strip().lstrip("- ")
                            if line:
                                missing.append(line)
                    for m in missing:
                        p = Path(m)
                        if p.suffix == "":
                            p.mkdir(parents=True, exist_ok=True)
                        else:
                            p.parent.mkdir(parents=True, exist_ok=True)
                            p.touch(exist_ok=True)
                    dag_api.execute_workflow(executor="dryrun", updated_files=[])

                # Expose the underlying workflow's dag via a simple wrapper
                underlying_wf = wf_api._workflow
                dag = getattr(underlying_wf, 'dag', None)
                if dag is None:
                    dag = getattr(getattr(underlying_wf, 'persistence', None), 'dag', None)
                if dag is None:
                    raise RuntimeError('Unable to access Snakemake DAG after dry-run execution')

                # Store captured stderr for later use
                self._stderr_output = stderr_capture.getvalue()
                # Make DAG available to the class
                self.dag = dag
                return SimpleNamespace(dag=dag)
        except Exception as e:
            # Store stderr and exception for potential logging
            self._stderr_output = stderr_capture.getvalue()
            self._compilation_error = e

            # Try to extract DAG even if there was an error
            if wf_api is not None:
                try:
                    underlying_wf = wf_api._workflow
                    dag = getattr(underlying_wf, 'dag', None)
                    if dag is None:
                        dag = getattr(getattr(underlying_wf, 'persistence', None), 'dag', None)
                    if dag is not None:
                        self.dag = dag
                except:
                    pass  # If we can't get the DAG, that's ok
            raise
        finally:
            # Restore original stderr
            sys.stderr = old_stderr

    def _extract_log_files(self):
        """Extract log file paths from all jobs in the DAG."""
        for job in self.dag.jobs:
            if hasattr(job, 'log') and job.log:
                # Get the first log file if there are multiple
                if hasattr(job.log, '__iter__') and not isinstance(job.log, str):
                    log_file = next(iter(job.log), None)
                else:
                    log_file = job.log
                if log_file:
                    self.log_files[job.name] = str(log_file)

    def _write_error_to_log(self, rulename: str, error: Exception):
        """Write error information to the rule's log file."""
        if rulename in self.log_files:
            log_file = self.log_files[rulename]
            import traceback
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'a') as f:
                f.write("=== Error during workflow compilation/execution ===\n")
                f.write(f"Error: {str(error)}\n")
                f.write(traceback.format_exc())
                if hasattr(self, '_stderr_output') and self._stderr_output:
                    f.write("\n=== Captured stderr ===\n")
                    f.write(self._stderr_output)
                f.write("\n")

    def getInputOutput(self):
        return self.getJobList(self.dag)

    def getInputOutput4rule(self, rulename: str):
        """Get the input and output of a specific rule.

        If an error occurred during compilation, log it to the rule's log file.
        """
        try:
            io = self.getInputOutput()
            result = io[rulename]

            # If there was a compilation error stored, write it to log
            if hasattr(self, '_compilation_error'):
                self._write_error_to_log(rulename, self._compilation_error)

            return result
        except Exception as e:
            # Write any errors to the log file if available
            self._write_error_to_log(rulename, e)
            raise

    def getJobList(self, dag):
        # Return a dict of jobs
        jobs = {}
        for j in dag.jobs:
            jobs[j.name] = j
        return jobs


# Redirect stderr to logger
class StreamToLogger:
    """Redirect stream writes to logger at ERROR level."""

    def __init__(self, logger_instance):
        """Initialize StreamToLogger with a logger instance.

        Args:
            logger_instance: A logger object with an error() method (e.g., loguru logger)
        """
        self.logger = logger_instance
        self._buffer = ''

    def write(self, message: str) -> None:
        if not message:
            return

        self._buffer += message
        if message.endswith("\n"):
            text = self._buffer.strip()
            if text:
                # Log the entire accumulated message once
                self.logger.error(text)
            self._buffer = ""

    def flush(self) -> None:
        pass