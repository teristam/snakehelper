## snakehelper

Provide a simple interface to query the input and output files of a snake workflow. This allows snakemake to be used as part of the workflow or execute indepedently as scripts. This enables the development of snakemake scripts in jupyter notebook or vscode code cells, significantly improving the development efficiency.

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
`sinput` and `soutput` will then be a dictionary containing the input and output file name from the `sort_spikes` rule.

