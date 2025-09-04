# a simple helper class to make working with snake input and output easier in a script
import os
from pathlib import Path
import sys
from pathlib import Path
import os
import snakemake

# Try to import stable APIs across Snakemake versions
try:  # Snakemake >= 9 public API
    from snakemake.api import (
        SnakemakeApi as _SMSnakemakeApi,
        DAGSettings as _SMDAGSettings,
        ResourceSettings as _SMResourceSettings,
    )
except Exception:  # pragma: no cover - compatibility path
    _SMSnakemakeApi = None
    _SMDAGSettings = None
    _SMResourceSettings = None

try:  # Older internal API (Snakemake < 9)
    from snakemake.workflow import Workflow as _SMWorkflow
except Exception:  # pragma: no cover - compatibility path
    _SMWorkflow = getattr(snakemake, 'Workflow', None)

try:
    from snakemake.io import OutputFiles as _SMOutputFiles
except Exception:  # pragma: no cover - compatibility path
    _SMOutputFiles = None

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
        # Retrieve DAG in a version-robust way
        dag = None
        # If compileWorkflow already returned an object with a dag, prefer that
        if hasattr(self.workflow, 'dag') and self.workflow.dag is not None:
            dag = self.workflow.dag
        else:
            try:
                if hasattr(self.workflow, 'persistence') and hasattr(self.workflow.persistence, 'dag'):
                    dag = self.workflow.persistence.dag
            except Exception:
                dag = None
            if dag is None and hasattr(self.workflow, 'dag'):
                dag = self.workflow.dag
        if dag is None:
            raise RuntimeError('Unable to access Snakemake DAG after dry-run execution')
        self.dag = dag


    def compileWorkflow(self):
        """Compile the workflow and build a DAG via a dry-run.

        Uses the public Snakemake API when available (>=9),
        falling back to legacy internals for older versions.
        Returns an object exposing a ``dag`` attribute for downstream use.
        """
        # Preferred API (Snakemake >= 9)
        if _SMSnakemakeApi is not None and _SMDAGSettings is not None:
            from types import SimpleNamespace
            from pathlib import Path as _Path

            # Build workflow and execute dryrun via API
            with _SMSnakemakeApi() as api:
                wf_api = api.workflow(
                    resource_settings=_SMResourceSettings(cores=1),
                    snakefile=_Path(self.snakefile),
                    workdir=None,
                )
                dag_api = wf_api.dag(
                    dag_settings=_SMDAGSettings(
                        targets=set(self.targets),
                        forceall=True,
                    )
                )
                # execute with dryrun executor to materialize DAG
                # Try to build DAG; if missing raw inputs are reported, create
                # minimal placeholders (dirs or empty files) and retry once.
                try:
                    dag_api.execute_workflow(executor="dryrun", updated_files=[])
                except Exception as ex:  # pragma: no cover - compatibility path
                    from snakemake.exceptions import MissingInputException
                    if isinstance(ex, MissingInputException):
                        msg = str(ex)
                        missing = []
                        # Parse affected files from exception message
                        if "affected files:" in msg:
                            tail = msg.split("affected files:")[-1].strip()
                            # support multiple lines
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
                        # retry once
                        dag_api.execute_workflow(executor="dryrun", updated_files=[])
                    else:
                        raise

                # Expose the underlying workflow's dag via a simple wrapper
                underlying_wf = wf_api._workflow  # noqa: SLF001 - public via API property
                dag = getattr(underlying_wf, 'dag', None)
                if dag is None:
                    # Some versions might keep dag on persistence
                    dag = getattr(getattr(underlying_wf, 'persistence', None), 'dag', None)
                if dag is None:
                    raise RuntimeError('Unable to access Snakemake DAG after dry-run execution (API path)')
                return SimpleNamespace(dag=dag)

        # Legacy fallback (Snakemake < 9)
        # Some Snakemake versions do not expose logger.setup_logfile
        logger = getattr(snakemake, 'logger', None)
        if logger is not None and hasattr(logger, 'setup_logfile'):
            try:
                logger.setup_logfile()
            except Exception:
                pass

        if _SMWorkflow is None:
            raise RuntimeError("Snakemake Workflow API not found; incompatible version")

        workflow = _SMWorkflow(self.snakefile)
        workflow.include(self.snakefile)
        workflow.check()
        # execute legacy dryrun
        workflow.execute(dryrun=True, updated_files=[], quiet=True,
                         targets=self.targets, forceall=True)
        return workflow

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
