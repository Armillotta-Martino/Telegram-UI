import os
import sys

import pytest

from utils import Utils

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_utils__get_environment_value():
    """
    Test the get_environment_value method of the Utils class to ensure it correctly retrieves environment variables
    """
    # Test with a string environment variable
    os.environ['TEST_ENV_STRING'] = 'test_value'
    assert Utils.get_environment_value('TEST_ENV_STRING', 'default') == 'test_value'
    
    # Test with an integer environment variable
    os.environ['TEST_ENV_INT'] = '42'
    assert Utils.get_environment_value('TEST_ENV_INT', 0) == 42
    
    # Test with a boolean environment variable
    os.environ['TEST_ENV_BOOL'] = 'true'
    assert Utils.get_environment_value('TEST_ENV_BOOL', False) is True
    
    # Test with a float environment variable
    os.environ['TEST_ENV_FLOAT'] = '3.14'
    assert Utils.get_environment_value('TEST_ENV_FLOAT', 0.0) == 3.14
    
    # Test with a custom type environment variable in a json format
    os.environ['TEST_ENV_JSON'] = '{"key": "value"}'
    assert Utils.get_environment_value('TEST_ENV_JSON', {}) == {"key": "value"}
    
    # Test with an environment variable that cannot be converted to the target type
    os.environ['TEST_ENV_INVALID_INT'] = 'not_an_int'
    with pytest.raises(Exception):
        Utils.get_environment_value('TEST_ENV_INVALID_INT', 0)
    
    # Test with a non-existent environment variable
    assert Utils.get_environment_value('NON_EXISTENT_ENV', 'default') == 'default'
    
    # Clean up environment variables
    del os.environ['TEST_ENV_STRING']
    del os.environ['TEST_ENV_INT']
    del os.environ['TEST_ENV_BOOL']
    del os.environ['TEST_ENV_FLOAT']
    del os.environ['TEST_ENV_JSON']