import math
import os

from file_types.compression.FFMPEG import FFMPEG
from file_types.file import File
from file_types.video import Video


class LRV():
    """
    Class to execute actions with LRV (Low resolution video) file

    Raises:
        ThumbVideoError: _description_

    Returns:
        _type_: _description_
    """
    
    @classmethod
    def generate_video_low_resolution(self, video : Video, width : int = -1, height=480):
        """
        Calculate the low resolution video for the given video file

        Right now the LRV video is only scaled to 480p
        In the future i can increase the crf value or make it "dynamic" (scale by a dividend)
        """
        # Output path of the low resoluition video
        output_path = os.path.dirname(video.path) + "/" + video.short_name + "_LRV" + os.path.splitext(video.path)[1]

        # Check the ratio of the video
        ratio = FFMPEG.get_video_resolution(video)
        if ratio is None:
            raise Exception('Video ratio is not available.')
        
        # Calculate the resolution
        # I could use the -1 for automatic aspect ratio but it give error for odd numbers
        if width != -1 and height == -1:
            height = ratio[1] * width / ratio[0]
        elif width == -1 and height != -1:
            width = ratio[0] * height / ratio[1]

        # Execute the ffmpeg command for create the LRV file
        p = FFMPEG.call_ffmpeg([
            '-y',
            '-i', video.name,
            '-vf',
            'scale={}:{}'.format(math.ceil(width/2)*2 if width != -1 else width, math.ceil(height/2)*2 if height != -1 else height),
            '-progress', 'pipe:1',
            output_path,
        ])
        
        # Get the total frame count
        tot_n_frames = video.get_total_frames_count()
        # Display the progress bar
        FFMPEG.ffmpeg_progress_bar(video, p, tot_n_frames)

        # Change the file extension to LRV (low resolution video, as GoPro do)
        # I do it here and not with ffmpeg because ffmpeg don't allow to put LRV
        #new_output = os.path.dirname(video.path) + "/" + video.short_name + ".LRV"
        #os.rename(output_path, new_output)
        #output_path = new_output

        # Return the LRV file path
        if not p.returncode and os.path.lexists(video.path):
            return File(output_path)