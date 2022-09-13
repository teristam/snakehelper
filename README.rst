===========
snakehelper
===========

Provide a simple interface to query the input and output files of a snake workflow. This allows snakemake to be used as part of the workflow or execute indepedently as scripts. This enables the development of snakemake scripts in jupyter notebook or vscode code cells, significantly improving the development efficiency.

Usage
===========
Example::
    (sinput, soutput) = getSnake(locals(), 'tests/make_files/workflow_common.smk', ['tests/processed/recording_info.pkl'],'sort_spikes')



Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
