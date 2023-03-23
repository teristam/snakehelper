## snakehelper

Provide a simple interface to query the input and output files of a snake workflow. This allows snakemake to be used as part of the workflow or execute indepedently as scripts. This enables the development of snakemake scripts in jupyter notebook or vscode code cells, significantly improving the development efficiency.

The original snakemake will inject a `snakemake` object into the running script, which will be confused with the snakemake package if you are running the sccript outside of the snakemake environment. This helper function compile the workflow and extract the input and output file names for you, so that you can use them to develop the script outside of the snakemake environment (e.g. in a Jupyter notebook or interactive shell). It uses the variables returned by `local()` function to determine whether it is running in a snakemake environment, and if so, return the input and output from the `snakemake` object. This provide a seamless development workflow where the same script can be run both inside and outside of snakemake, making code iteratiion and debugging much easier.

### Installation
Due to the requirement of snakemake on the `datrie` package, in Windows you will need to install the [Microsoft Build Tool](https://visualstudio.microsoft.com/visual-cpp-build-tools/) for the setup to be successfully. Download the run the installer. Click `modify`

![](docs/build%20tool.png)

Ensure that the C++ tools are installed

![](docs/c%2B%2B%20tools.png)


Next clone the repository and then install via pip

```
git clone https://github.com/teristam/snakehelper.git
cd snakehelper
pip install .
```


### Usage


```
def getSnake(locals:dict,snakefile:str, targets:list, rule:str, createFolder:bool = True):
    """Return the input and output files according to a snakemake file, target and running rule

    Args:
    locals (dict): Local variables dictionary of caller script
    snakefile (str): Snakefile location
    targets (list): The file or files that are created when the rule is executed
    rule (str): The rule for which you want to determine the input and output files
    createFolder (bool): Whether or not to create output folders. Default is True. 

    Returns:
    Tuple: A tuple containing input and output files.
    """

```

### Example

```
from snakehelper.SnakeIOHelper import getSnake
(sinput, soutput) = getSnake(locals(), 'tests/make_files/workflow_common.smk',
  ['tests/processed/recording_info.pkl'],'sort_spikes')
```
snakemake require you to specify at least one of the output file name so that it can extract the wildcards used to build the workflow. 
`sinput` and `soutput` are dictionaries containing the input and output file name from the `sort_spikes` rule. `getSnake` will automatically determinate if it is inside the snakemake environment or it is run as an standalone script.

### Development

When you run `getSnake` in the Python interactive cell in VS Code, by default it will open the shell at the folder of the Python script. However, in many cases, the Snakemake files are defined relative to the project root folder. You can either change the working directory of the interactive shell to the project root folder, or you can define the project root directory in the `SNAKEMAKE_DEBUG_ROOT` environment variable and `getSnake` will automatically switch the working directory to that folder. Alternatively, you can also define the environment variable in a `.env` file in the project root directory and VS Code will automatically load it when it opens the interactive window. Note that the `.env` file will not be automatically loaded if you run the Python script outside of VS Code. In that case, you need to define the environmental variable manually according to the methods commonly used for your operating system.
