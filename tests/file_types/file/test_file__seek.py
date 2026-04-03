import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__seek():
    """
    Test the seek method of the File class to ensure it correctly seeks to a specified position in the file
    """
    # Create and use the File object directly so seek affects the same descriptor
    with File('test_files/test_video.mp4') as test_file:
        initial_bytes = test_file.read(100)
        initial_position = test_file.tell()

        # Use the seek method to move back to the beginning of the file
        test_file.seek(0)

        # Read bytes again and check that we are back at the beginning
        new_bytes = test_file.read(100)
        new_position = test_file.tell()

        assert initial_bytes == new_bytes, "The seek method did not correctly move the file pointer back to the beginning"
        assert new_position == 100, "The seek method did not correctly update the file pointer position"