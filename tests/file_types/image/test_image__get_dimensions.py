from file_types.file import File
import pytest

from file_types.image import Image

def test_image__get_dimensions():
    """
    Test the get_dimensions method of the Image class to ensure it correctly returns the dimensions of a valid image file
    """
    # Create an Image object using the test image file path
    image = Image(File('test_files/test_image.jpg'))

    # Get the dimensions of the image
    dimensions = image.get_dimensions()

    # Check that the dimensions are returned as a tuple of two integers (width, height)
    assert isinstance(dimensions, tuple), "The dimensions should be returned as a tuple"
    assert len(dimensions) == 2, "The dimensions tuple should have two elements (width, height)"
    assert all(isinstance(d, int) for d in dimensions), "Both width and height should be integers"