import os
import sys

from file_types.file import File
import pytest

from file_types.image import Image

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def test_image__constructor():
    """
    Test the constructor of the Image class to ensure it correctly initializes an Image object with a valid file path
    """
    # Create an Image object using the test image file path
    image = Image(File('test_files/test_image.jpg'))

    # Check that the created object is an instance of the Image class
    assert isinstance(image, Image), "The constructor does not return an instance of the Image class"

    # Check that the file path is correctly set in the Image object
    assert image.file_name == 'test_image.jpg', "The file path is not correctly set in the Image object"