import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__get_mime():
    """
    Test the get_mime method of the File class to ensure it correctly retrieves the MIME type of the file
    """
    # Create a test file object with a known file path
    test_file = File('test_files/test_video.mp4')

    # Get the MIME type of the file
    mime_type = test_file.get_mime()

    # Check that the MIME type is correct (this will depend on the actual content of the test video)
    assert mime_type == 'video', f"The MIME type returned by get_mime is incorrect. Expected 'video', got '{mime_type}'"