import os
import subprocess
import sys
import tempfile
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from compression.FFMPEG import FFMPEG

def test_FFMPEG__call_ffmpeg(monkeypatch):
    """
    Test that calling ffmpeg with valid arguments does not raise an exception
    """
    # Attempt to call ffmpeg with valid arguments and assert that no exception is raised
    try:
        FFMPEG.call_ffmpeg(["-version"])
    except Exception as e:
        pytest.fail(f"ffmpeg call with valid arguments raised an exception: {e}")

def test_FFMPEG__call_ffmpeg__nonexistent_executable(monkeypatch):
    """
    Test that calling ffmpeg with a non-existent executable raises a FileNotFoundError
    """
    # Set the ffmpeg executable path to a non-existent file
    monkeypatch.setattr(FFMPEG, '_FFMPEG__get_command_path', lambda exe_path_json, exe_name: "non_existent_ffmpeg.exe")
    
    # Attempt to call ffmpeg with a non-existent executable and assert that an exception is raised
    with pytest.raises(FileNotFoundError, match="ffmpeg executable not found"):
        FFMPEG.call_ffmpeg(["-version"])

def test_FFMPEG__call_ffmpeg__invalid_arguments(monkeypatch):
    """
    Test that calling ffmpeg with invalid arguments raises an exception
    """
    # Attempt to call ffmpeg with invalid arguments and assert that an exception is raised
    with pytest.raises(Exception, match="ffmpeg execution failed"):
        p = FFMPEG.call_ffmpeg(["-invalid_argument"])
        p.communicate()  # This will raise the exception since the command is invalid
        
        if p.returncode != 0:
            raise Exception(f"ffmpeg execution failed with return code {p.returncode}")
        
def test_FFMPEG__call_ffmpeg__return_value(monkeypatch):
    """
    Test that calling ffmpeg with valid arguments returns a subprocess.Popen object
    """
    # Attempt to call ffmpeg with valid arguments and assert that the return value is a subprocess.Popen object
    try:
        result = FFMPEG.call_ffmpeg(["-version"])
        assert isinstance(result, subprocess.Popen), "ffmpeg call did not return a subprocess.Popen object"
    except Exception as e:
        pytest.fail(f"ffmpeg call with valid arguments raised an exception: {e}")
        
def test_FFMPEG__call_ffmpeg__output(monkeypatch):
    """
    Test that calling ffmpeg with valid arguments produces output
    """
    # Attempt to call ffmpeg with valid arguments and assert that it produces output
    try:
        # Generate a temporary output folder and file for ffmpeg to write to
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tmp_path = tmp.name
        tmp.close()
        
        result = FFMPEG.call_ffmpeg(["-input", "test_files/test_video.mp4", "-f", "null", "-output", tmp_path ])
        stdout, stderr = result.communicate()
        assert stdout is not None and len(stdout) > 0, "ffmpeg call did not produce any output"
    except Exception as e:
        pytest.fail(f"ffmpeg call with valid arguments raised an exception: {e}")

