from file_types.file import File
from file_types.video import Video
import pytest

def test_video__get_ffprobe_file_details():
    """
    Test the get_ffprobe_file_details method of the Video class to ensure it correctly retrieves video file details using ffprobe
    """
    # Create a Video object using the test video file path
    video = Video(File('test_files/test_video.mp4'))

    # Call the get_ffprobe_file_details method to retrieve video details
    details = video.get_ffprobe_file_details()

    # Check that the details are returned as a dictionary
    assert isinstance(details, dict), "The get_ffprobe_file_details method does not return a dictionary"

    # Check that the dictionary contains expected keys (e.g., 'format', 'streams')
    assert 'format' in details, "The details dictionary does not contain the 'format' key"
    assert 'streams' in details, "The details dictionary does not contain the 'streams' key"