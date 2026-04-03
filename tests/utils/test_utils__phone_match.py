import os
import sys

import pytest

from utils import Utils

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_utils__phone_match():
    """
    Test the phone_match function to ensure it correctly identifies valid phone numbers and raises ValueError for invalid ones
    """
    # Valid phone numbers
    valid_phone_numbers = [
        "+1234567890",
        "1234567890",
        "(123) 456-7890",
        "123-456-7890",
        "123.456.7890",
        "123 456 7890"
    ]

    for phone in valid_phone_numbers:
        assert Utils.phone_match(phone) == phone

    # Invalid phone numbers
    invalid_phone_numbers = [
        "abc1234567",
        "phone1234567",
    ]

    for phone in invalid_phone_numbers:
        with pytest.raises(ValueError):
            Utils.phone_match(phone)