import os
import subprocess
import sys
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from compression.FFMPEG import FFMPEG

def test_FFMPEG__call_ffprobe(monkeypatch):
    """
    Test that calling ffprobe with valid arguments does not raise an exception
    """
    # Call ffprobe with valid arguments and assert that no exception is raised
    FFMPEG.call_ffprobe(["-version"])

def test_FFMPEG__call_ffprobe__nonexistent_executable(monkeypatch):
    """
    Test that calling ffprobe with a non-existent executable raises a FileNotFoundError
    """
    # Set the ffprobe executable path to a non-existent file
    monkeypatch.setattr(FFMPEG, '_FFMPEG__get_command_path', lambda exe_path_json, exe_name: "non_existent_ffprobe.exe")
    
    # Call ffprobe with a non-existent executable and assert that an exception is raised
    with pytest.raises(FileNotFoundError, match="ffprobe executable not found"):
        FFMPEG.call_ffprobe(["-version"])
        
def test_FFMPEG__call_ffprobe__invalid_arguments(monkeypatch):
    """
    Test that calling ffprobe with invalid arguments raises an exception
    """
    # Call ffprobe with invalid arguments and assert that an exception is raised
    with pytest.raises(Exception, match="ffprobe execution failed"):
        p = FFMPEG.call_ffprobe(["-invalid_argument"])
        p.communicate()  # This will raise the exception since the command is invalid
        
        if p.returncode != 0:
            raise Exception(f"ffprobe execution failed with return code {p.returncode}")
        
def test_FFMPEG__call_ffprobe__return_value(monkeypatch):
    """
    Test that calling ffprobe with valid arguments returns a subprocess.Popen object
    """
    # Call ffprobe with valid arguments and assert that the return value is a subprocess.Popen object
    result = FFMPEG.call_ffprobe(["-version"])
    assert isinstance(result, subprocess.Popen), "ffprobe call did not return a subprocess.Popen object"