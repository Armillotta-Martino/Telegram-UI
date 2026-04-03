import os
import sys

import pytest

from utils import Utils

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_utils__size_value_to_human():
    # Test cases for size_value_to_human
    test_cases = [
        (0, "0.0 B"),
        (512, "512.0 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1048576, "1.0 MB"),
        (1073741824, "1.0 GB"),
        (1099511627776, "1.0 TB"),
        (1125899906842624, "1.0 PB"),
        (1152921504606846976, "1.0 EB"),
        (1180591620717411303424, "1.0 ZB"),
        (1208925819614629174706176, "1.0 YB"),
    ]

    for input_value, expected_output in test_cases:
        assert Utils.size_value_to_human(input_value) == expected_output