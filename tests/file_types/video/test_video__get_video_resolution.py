from file_types.file import File
from file_types.video import Video
import pytest

def test_video__get_video_resolution():
    """
    Test the get_video_resolution method of the Video class to ensure it correctly retrieves the video resolution using ffprobe
    """
    # Create a Video object using the test video file path
    video = Video(File('test_files/test_video.mp4'))

    # Get the video resolution
    resolution = video.get_video_resolution()

    # Check that the resolution is a list of two integers [width, height]
    assert isinstance(resolution, list), "The resolution should be a list"
    assert len(resolution) == 2, "The resolution list should contain two elements"
    assert all(isinstance(x, int) for x in resolution), "Both width and height should be integers"