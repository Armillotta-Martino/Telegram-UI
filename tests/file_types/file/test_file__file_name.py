import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__file_name():
    """
    Test the file_name property of the File class to ensure it returns the correct file name
    """
    # Create a test file object with a known file path
    test_file = File('test_files/test_video.mp4')

    # Check that the file name is returned correctly
    assert test_file.file_name == 'test_video.mp4', "The file_name property does not return the correct file name"
    
def test_file__file_name__no_extension():
    """
    Test the file_name property of the File class with a file that has no extension to ensure it returns the correct file name
    """
    # Create a test file object with a known file path that has no extension
    test_file = File('test_files/test_file_no_extension')

    # Check that the file name is returned correctly
    assert test_file.file_name == 'test_file_no_extension', "The file_name property does not return the correct file name for a file with no extension"

def test_file__file_name__hidden_file():
    """
    Test the file_name property of the File class with a hidden file to ensure it returns the correct file name
    """
    # Create a test file object with a known file path that is a hidden file
    test_file = File('test_files/.hidden_file')

    # Check that the file name is returned correctly
    assert test_file.file_name == '.hidden_file', "The file_name property does not return the correct file name for a hidden file"
