import os

from file_types.file import File
from file_types.video import Video
import pytest

from file_types.LRV import LRV

def test_LRV__generate_video_low_resolution():
    """
    Test the generate_video_low_resolution method of the LRV class to ensure it correctly generates a low resolution video from a given video file
    """
    # Create a Video object using the test video file path
    video = Video(File('test_files/test_video.mp4'))

    # Generate the low resolution video
    lrv_video = LRV.generate_video_low_resolution(video)

    # Check that the generated object is an instance of the Video class
    assert isinstance(lrv_video, Video), "The generate_video_low_resolution method does not return an instance of the Video class"

    # Check that the output path is correctly set in the LRV video object
    expected_output_path = os.path.splitext(os.path.basename('test_files/test_video.mp4'))[0] + "_LRV.mp4"
    assert lrv_video.file_name == expected_output_path, "The output path is not correctly set in the LRV video object"