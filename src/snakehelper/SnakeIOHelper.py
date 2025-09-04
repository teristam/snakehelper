# a simple helper class to make working with snake input and output easier in a script
import os
from pathlib import Path
import sys
from pathlib import Path
import os
import snakemake

# Try to import stable APIs across Snakemake versions
try:
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
        # compile workflow to build the DAG
        # Some Snakemake versions do not expose logger.setup_logfile
        logger = getattr(snakemake, 'logger', None)
        if logger is not None and hasattr(logger, 'setup_logfile'):
            try:
                logger.setup_logfile()
            except Exception:
                pass

        # Build workflow using version-compatible entry point
        if _SMWorkflow is None:
            raise RuntimeError("Snakemake Workflow API not found; incompatible version")

        # Use conservative constructor args for compatibility
        workflow = _SMWorkflow(self.snakefile)
        workflow.include(self.snakefile)
        workflow.check()

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


