import os
import sys

import pytest

from utils import Utils

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_utils__free_disk_usage():
    """
    Test the free_disk_usage function to ensure it returns a non-negative integer representing free disk space in bytes
    """
    # Call the free_disk_usage function
    result = Utils.free_disk_usage()
    
    assert isinstance(result, int), "Expected free_disk_usage to return an integer representing free disk space in bytes"
    assert result >= 0, "Expected free_disk_usage to return a non-negative integer representing free disk space in bytes"