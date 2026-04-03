from file_types.file import File
from file_types.video import Video
import pytest

def test_video__length_seconds():
    """
    Test the length_seconds property of the Video class to ensure it correctly retrieves the video length in seconds
    """
    # Create a Video object using the test video file path
    video = Video(File('test_files/test_video.mp4'))

    # Get the length of the video in seconds
    length_seconds = video.length_seconds

    # Check that the length is a positive float
    assert isinstance(length_seconds, float), "The length_seconds property does not return a float"
    assert length_seconds > 0, "The length_seconds property does not return a positive value"