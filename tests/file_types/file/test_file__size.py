import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__size_valid():
    """
    Test the size property of the File class to ensure it returns the correct file size
    """
    # Create a test file object with a known file path
    test_file = File('test_files/test_video.mp4')

    # Check that the size is returned correctly
    expected_size = os.path.getsize('test_files/test_video.mp4')
    assert test_file.size == expected_size, "The size property does not return the correct file size"