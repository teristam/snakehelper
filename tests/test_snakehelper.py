import pytest
from snakehelper.SnakeIOHelper import getSnake

def test_parse_workflow():
    (sinput, soutput) = getSnake(locals(), 'tests/make_files/workflow_common.smk', 
                                            ['tests/processed/recording_info.pkl'],'sort_spikes')
    
    assert sinput.recording_to_sort =='tests'
    assert soutput.recording_info == 'tests/processed/recording_info.pkl'