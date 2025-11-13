"""Helper utilities for working with Snakemake I/O in scripts (Snakemake >= 9)."""

import os
from pathlib import Path
from types import SimpleNamespace

from snakemake.api import DAGSettings as _SMDAGSettings
from snakemake.api import SnakemakeApi as _SMSnakemakeApi
from snakemake.settings.types import ResourceSettings as _SMResourceSettings


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
             rule:str, createFolder:bool = True, return_snake_obj=False, change_working_dir=True):
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
            
        parser = IOParser(snakefile, targets)
        io = parser.getInputOutput4rule(rule)
        if createFolder:
            makeFolders(io.output)
            
        if return_snake_obj:
            return (io.input, io.output, io)
        else:
            return (io.input, io.output)
    else:
        if createFolder:
            makeFolders(locals['snakemake'].output)
        if return_snake_obj:
            return (locals['snakemake'].input, locals['snakemake'].output, locals['snakemake'])
        else:
            return (locals['snakemake'].input, locals['snakemake'].output)


def makeDummpyOutput(output):
    for o in output:
        Path(o).touch()

class IOParser:
    def __init__(self, snakefile:str, targets:list):
        self.snakefile = snakefile
        self.targets = targets

        self.workflow = self.compileWorkflow()
        if not hasattr(self.workflow, 'dag') or self.workflow.dag is None:
            raise RuntimeError('Unable to access Snakemake DAG after dry-run execution')
        self.dag = self.workflow.dag


    def compileWorkflow(self):
        """Compile the workflow and build a DAG via a dry-run using Snakemake API.

        Returns an object exposing a ``dag`` attribute for downstream use.
        """
        # Apply nest_asyncio patch if running in Jupyter
        _apply_jupyter_asyncio_patch()

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
            return SimpleNamespace(dag=dag)

    def getInputOutput(self):
        return self.getJobList(self.dag)

    def getInputOutput4rule(self,rulename:str):
        #Get the input and output of a specific rule
        io = self.getInputOutput()
        return io[rulename]
    
    def getJobList(self,dag):
        # Return a dict of jobs
        jobs = {}
        for j in dag.jobs:
            jobs[j.name] = j
        return jobs
