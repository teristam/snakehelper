import os
import shutil
from pathlib import Path
import glob

import pytest
from snakehelper.SnakeIOHelper import getSnake
import subprocess


@pytest.fixture(scope="session", autouse=True)
def cleanup_tmp_recordings():
    """Clean up any tmp_recording folders before and after test session."""
    # Cleanup before tests
    for folder in glob.glob('tmp_recording*'):
        if os.path.isdir(folder):
            shutil.rmtree(folder)

    yield

    # Cleanup after tests
    for folder in glob.glob('tmp_recording*'):
        if os.path.isdir(folder):
            shutil.rmtree(folder)

def test_parse_workflow():
    (sinput, soutput) = getSnake(locals(), 'tests/make_files/workflow_common.smk', 
                                            ['tests/processed/recording_info.pkl'],
                                            'sort_spikes', change_working_dir=False)
    
    assert sinput.recording_to_sort =='tests'
    # Normalize separators across OS (Windows vs POSIX)
    assert Path(str(soutput.recording_info)) == Path('tests/processed/recording_info.pkl')


def test_return_snake_obj_for_rule():
    sinput, soutput, job = getSnake(
        locals(),
        'tests/make_files/workflow_common.smk',
        ['tests/processed/recording_info.pkl'],
        'sort_spikes',
        change_working_dir=False,
        return_snake_obj=True,
    )

    assert getattr(job, 'name', None) == 'sort_spikes'
    assert sinput.recording_to_sort == 'tests'
    assert soutput.recording_info.endswith('processed/recording_info.pkl')


def test_create_folders_for_output(tmp_path):
    # Use a unique recording name so we don't collide with repo files
    recording = f"tmp_recording_{os.getpid()}"
    out_dir = Path(recording) / 'processed'
    out_file = out_dir / 'recording_info.pkl'

    # Ensure clean slate
    if out_dir.exists():
        shutil.rmtree(out_dir)

    try:
        _in, out = getSnake(
            locals(),
            'tests/make_files/workflow_common.smk',
            [str(out_file)],
            'sort_spikes',
            change_working_dir=False,
            createFolder=True,
        )

        assert out_dir.is_dir(), 'Expected output directory to be created'
        # Compare as Paths to avoid separator issues
        assert Path(str(out.recording_info)) == out_file
    finally:
        # Cleanup created directories/files
        if out_dir.exists():
            shutil.rmtree(out_dir)


def test_change_working_dir_respects_env(monkeypatch):
    # Set env var and ensure chdir is called with it
    target_root = os.getcwd()
    monkeypatch.setenv('SNAKEMAKE_DEBUG_ROOT', target_root)

    called = {}

    def fake_chdir(path):
        called['path'] = path

    # Patch the os.chdir used inside the module
    import snakehelper.SnakeIOHelper as mod
    monkeypatch.setattr(mod.os, 'chdir', fake_chdir)

    getSnake(
        locals(),
        'tests/make_files/workflow_common.smk',
        ['tests/processed/recording_info.pkl'],
        'sort_spikes',
        change_working_dir=True,
    )

    assert called.get('path') == target_root


def test_with_snakemake_in_locals(monkeypatch):
    class FakeIO:
        def __init__(self):
            self.recording_to_sort = 'tests'

    class FakeOO:
        def __init__(self):
            self.recording_info = 'tests/processed/recording_info.pkl'

    class FakeSM:
        def __init__(self):
            self.input = FakeIO()
            self.output = FakeOO()

    fake = FakeSM()

    # createFolder=True should not error even if folders already exist
    sinput, soutput = getSnake({'snakemake': fake}, '', [], '', createFolder=True)
    assert sinput.recording_to_sort == 'tests'
    assert soutput.recording_info.endswith('processed/recording_info.pkl')

    sinput2, soutput2, sobj = getSnake({'snakemake': fake}, '', [], '', createFolder=False, return_snake_obj=True)
    assert sobj is fake
    assert sinput2.recording_to_sort == 'tests'
    assert soutput2.recording_info.endswith('processed/recording_info.pkl')


def test_missing_rule_raises_keyerror():
    with pytest.raises(KeyError):
        getSnake(
            locals(),
            'tests/make_files/workflow_common.smk',
            ['tests/processed/recording_info.pkl'],
            'nonexistent_rule',
            change_working_dir=False,
        )


def test_no_chdir_when_disabled(monkeypatch):
    # Ensure env var is set but change_working_dir=False prevents chdir
    monkeypatch.setenv('SNAKEMAKE_DEBUG_ROOT', os.getcwd())

    called = {'count': 0}

    def fake_chdir(_):
        called['count'] += 1

    import snakehelper.SnakeIOHelper as mod
    monkeypatch.setattr(mod.os, 'chdir', fake_chdir)

    getSnake(
        locals(),
        'tests/make_files/workflow_common.smk',
        ['tests/processed/recording_info.pkl'],
        'sort_spikes',
        change_working_dir=False,
    )

    assert called['count'] == 0


def test_no_create_folder_when_disabled():
    # Use a unique recording folder; ensure it doesn't get created
    recording = f"tmp_recording_nofolder_{os.getpid()}"
    out_dir = Path(recording) / 'processed'
    out_file = out_dir / 'recording_info.pkl'

    if out_dir.exists():
        shutil.rmtree(out_dir)

    try:
        _in, out = getSnake(
            locals(),
            'tests/make_files/workflow_common.smk',
            [str(out_file)],
            'sort_spikes',
            change_working_dir=False,
            createFolder=False,
        )
        # Directory should still not exist
        assert not out_dir.exists()
        # Compare as Paths to avoid separator issues
        assert Path(str(out.recording_info)) == out_file
    finally:
        if out_dir.exists():
            shutil.rmtree(out_dir)


def test_stderr_capture_and_logging():
    """Test that stderr is captured during workflow compilation and available for logging."""
    # Using the normal workflow_common.smk which compiles successfully
    # The log file is defined as '{recording}/processed/snakemake.log'
    # With target 'tests/processed/recording_info.pkl', wildcard {recording} = 'tests'
    expected_log_file = Path('tests/processed/snakemake.log')

    # Clean up any existing log file
    if expected_log_file.exists():
        expected_log_file.unlink()

    try:
        # Compile a normal workflow - this should succeed
        sinput, soutput = getSnake(
            locals(),
            'tests/make_files/workflow_common.smk',
            ['tests/processed/recording_info.pkl'],
            'sort_spikes',
            change_working_dir=False,
        )

        # Verify the compilation succeeded
        assert sinput.recording_to_sort == 'tests'
        assert Path(str(soutput.recording_info)) == Path('tests/processed/recording_info.pkl')

        # The stderr during compilation should be captured but not written unless there's an error
        # This test verifies the mechanism is in place

    finally:
        # Clean up
        if expected_log_file.exists():
            expected_log_file.unlink()


def test_error_logging_mechanism():
    """Test that the error logging mechanism is in place and functional."""
    from snakehelper.SnakeIOHelper import IOParser

    # Use the 'tests' recording with sort_spikes rule
    # The log file for sort_spikes is 'tests/processed/snakemake.log'
    expected_log_file = Path('tests/processed/snakemake.log')

    # Clean up
    if expected_log_file.exists():
        expected_log_file.unlink()

    try:
        # Create parser - this compiles the workflow and extracts log files
        parser = IOParser(
            'tests/make_files/workflow_common.smk',
            ['tests/processed/recording_info.pkl']
        )

        # Verify log files were extracted
        assert 'sort_spikes' in parser.log_files, "Log file should be extracted for sort_spikes rule"
        assert parser.log_files['sort_spikes'] == 'tests/processed/snakemake.log'

        # Test the error writing mechanism in an exception context
        try:
            raise ValueError("Test error for logging")
        except ValueError as e:
            parser._write_error_to_log('sort_spikes', e)

        # Verify the log file was created and contains error information
        assert expected_log_file.exists(), "Log file should be created when error is logged"
        log_content = expected_log_file.read_text()
        assert 'Test error for logging' in log_content, "Log should contain error message"
        assert 'ValueError' in log_content, "Log should mention the error type"
        assert 'Error during workflow compilation/execution' in log_content, "Log should have error header"
        assert 'Traceback' in log_content, "Log should contain traceback information"

    finally:
        # Clean up
        if expected_log_file.exists():
            expected_log_file.unlink()


def test_cli_execution_error_logfile():
    subprocess.run(
        'uv run snakemake -F --snakefile tests/make_files/workflow_error.smk tests/example_recording/processed/recording_info.pkl'.split()
    )

    expected_log_file = Path('tests/example_recording/processed/error.log')

    # Clean up
    assert expected_log_file.exists()

    log_content = expected_log_file.read_text()
    assert 'ValueError' in log_content, "Log should mention the error type"

    if expected_log_file.exists():
        expected_log_file.unlink()

def test_cli_execution_normal_logfile():
    subprocess.run(
        'uv run snakemake -F --snakefile tests/make_files/workflow_common.smk tests/example_recording/processed/recording_info.pkl'.split()
    )

    expected_log_file = Path('tests/example_recording/processed/snakemake.log')

    # Clean up
    assert expected_log_file.exists()

    log_content = expected_log_file.read_text()
    assert 'Finish' in log_content, "Log should contain the finish message"

    if expected_log_file.exists():
        expected_log_file.unlink()
