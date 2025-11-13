#%% 
from snakehelper.SnakeIOHelper import getSnake, StreamToLogger
from pathlib import Path
# %%
(sinput, soutput, snake_obj) = getSnake(locals(), 'tests/make_files/workflow_error.smk', 
                                            ['tests/example_recording/processed/recording_info.pkl'],
                                            'sort_spikes', return_snake_obj=True, change_working_dir=False)


raise ValueError('There is some error in script.')

# %%
