from file_types.file import File
from file_types.video import Video
import pytest

def test_video__constructor():
    """
    Test the constructor of the Video class to ensure it correctly initializes a Video object from a given file path
    """
    # Create a Video object using the test video file path
    video = Video(File('test_files/test_video.mp4'))

    # Check that the generated object is an instance of the Video class
    assert isinstance(video, Video), "The constructor does not return an instance of the Video class"

    # Check that the file path is correctly set in the Video object
    assert video.file_name == 'test_video.mp4', "The file path is not correctly set in the Video object"