import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__bytes():
    """
    Test the bytes method of the File class to ensure it correctly returns the file content as bytes
    """
    # Create a test file object with a known file path
    test_file = File('test_files/test_video.mp4')

    # Get the file content as bytes
    file_bytes = test_file.bytes

    # Check that the returned value is of type bytes
    assert isinstance(file_bytes, bytes), "The bytes method does not return a value of type bytes"

    # Check that the returned bytes are not empty (this will depend on the actual content of the test video)
    assert len(file_bytes) > 0, "The bytes method returns an empty byte string"