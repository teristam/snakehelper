# %%
from snakehelper.SnakeIOHelper import getSnake
from pathlib import Path

# %%
(sinput, soutput, snake_obj) = getSnake(locals(), 'tests/make_files/workflow_common.smk', 
                                            ['tests/example_recording/processed/recording_info.pkl'],
                                            'sort_spikes', return_snake_obj=True, change_working_dir=False)

# %%
Path(soutput.recording_info).touch()


# %%
