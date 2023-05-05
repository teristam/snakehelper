#%%
from snakehelper.SnakeIOHelper import getSnake

# %%
(sinput, soutput, snake_obj) = getSnake(locals(), '../tests/make_files/workflow_common.smk', 
                                            ['../tests/processed/recording_info.pkl'],'sort_spikes', return_snake_obj=True)
# %%
(sinput, soutput) = getSnake(locals(), '../tests/make_files/workflow_common.smk', 
                                            ['../tests/processed/recording_info.pkl'],'sort_spikes')
# %%
