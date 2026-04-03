import os
import sys

import pytest

from file_types.file import File

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_file__constructor():
    """
    Test the constructor of the File class to ensure it correctly initializes the file information
    """
    # Create a test file object with a known file path
    test_file = File('test_files/test_video.mp4')

    # Check that the file path is set correctly
    assert test_file.path == 'test_files/test_video.mp4', "The file path is not set correctly in the constructor"

    # Check that the file information is populated (this will depend on the actual content of the test video)
    assert isinstance(test_file, File), "The object created by the constructor is not an instance of the File class"
    
def test_file__constructor__invalid():
    """
    Test the constructor of the File class with an invalid file path to ensure it raises an appropriate error
    """
    # Create a test file object with an invalid file path
    invalid_file_path = 'test_files/non_existent_file.mp4'
    
    # Check that the constructor raises a FileNotFoundError for an invalid file path
    with pytest.raises(FileNotFoundError):
        File(invalid_file_path)
        
def test_file__constructor__non_file():
    """
    Test the constructor of the File class with a directory path to ensure it raises an appropriate error
    """
    # Create a test file object with a directory path
    directory_path = os.path.dirname(__file__)
    
    # Check that the constructor raises a ValueError for a directory path
    with pytest.raises(ValueError):
        File(directory_path)