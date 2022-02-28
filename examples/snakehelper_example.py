#%%
from snakehelper.SnakeIOHelper import getSnake

# %%
(sinput, soutput) = getSnake(locals(), '../tests/make_files/workflow_common.smk', 
                                            ['../tests/processed/recording_info.pkl'],'sort_spikes')
# %%
