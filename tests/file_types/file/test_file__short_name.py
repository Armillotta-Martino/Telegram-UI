import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__short_name():
    """
    Test the short_name property of the File class
    """
    # Get a test file
    file = File('test_files/test_file.txt')
        
    # Check that the short_name property returns the expected value
    assert file.short_name == 'test_file', f'Expected short name to be "test_file", but got "{file.short_name}"'