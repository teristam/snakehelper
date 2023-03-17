## snakehelper

Provide a simple interface to query the input and output files of a snake workflow. This allows snakemake to be used as part of the workflow or execute indepedently as scripts. This enables the development of snakemake scripts in jupyter notebook or vscode code cells, significantly improving the development efficiency.

The original snakemake will inject a `snakemake` object into the running script, which will be confused with the snakemake package if you are running the sccript outside of the snakemake environment. This helper function compile the workflow and extract the input and output file names for you, so that you can use them to develop the script outside of the snakemake environment (e.g. in a Jupyter notebook or interactive shell). It uses the variables returned by `local()` function to determine whether it is running in a snakemake environment, and if so, return the input and output from the `snakemake` object. This provide a seamless development workflow where the same script can be run both inside and outside of snakemake, making code iteratiion and debugging much easier.

### Installation
Simply clone the repository and then install via pip

```
git clone https://github.com/teristam/snakehelper.git
cd snakehelper
pip install .
```


### Usage
```
from snakehelper.SnakeIOHelper import getSnake
(sinput, soutput) = getSnake(locals(), 'tests/make_files/workflow_common.smk',
  ['tests/processed/recording_info.pkl'],'sort_spikes')
```
snakemake require you to specify at least one of the output file name so that it can extract the wildcards used to build the workflow. 
`sinput` and `soutput` will then be a dictionary containing the input and output file name from the `sort_spikes` rule. `getSnake` will automatically determinate if it is inside the snakemake environment or it is run as an standalone script.

