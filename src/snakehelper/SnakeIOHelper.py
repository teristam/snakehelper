# a simple helper class to make working with snake input and output easier in a script
import os
from pathlib import Path
import snakemake
import sys
from pathlib import Path
import os

def makeFolders(output):
    # make folders used by the output varialbe if not exist
    # only needed when scripts are used independently
    # in snakemake, the folder will be created automatically
    # if the path contains '/' at the end, then it is considered as a directory and created accordingly
    
    paths = []

    #Check what kind of object the output is
    if isinstance(output, snakemake.io.OutputFiles):
        for _,v in output.items():
            paths.append(Path(v))
    else:
        #the output is a simple namespace
        for _,path in output.__dict__.items():
            paths.append(Path(path))


    for path in paths:
        if path.suffix == '': #if this is a folder
            if not os.path.exists(path):
                os.makedirs(path)
                print('Created folder:' + str(path))
        else:
            if not os.path.exists(path.parent):
                os.makedirs(path.parent)
                print('Created folder:' + str(path.parent))

def getSnake(locals:dict,snakefile:str, targets:list, rule:str, createFolder:bool = True, return_snake_obj=False):
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
        # if snake_root is not None:
        #     print('Changing working directory to:' + snake_root)
        #     os.chdir(snake_root)
            
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
        self.dag = self.workflow.persistence.dag


    def compileWorkflow(self):
        #compile workflow to build the DAG
        snakemake.logger.setup_logfile()
        workflow = snakemake.Workflow(self.snakefile,default_resources=None, rerun_triggers=['mtime'])
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


