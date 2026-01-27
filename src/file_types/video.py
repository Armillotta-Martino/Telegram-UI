import json
import os
import re
import tempfile

import click
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from hachoir.core import config as hachoir_config

from compression.FFMPEG import FFMPEG
from file_types.file import File

hachoir_config.quiet = True

class Video(File):
    """
        Video file type class
        Inherits from File
    """
    
    def __init__(self, file : File, force_file : bool = False):
        """
        Constructor
        
        Args:
            file: The file to convert to Video
            force_file: Force to treat the file as a video even if the mime type is not video
        """
        # Convert File to Video
        super().__init__(file.path)
        
        # Check if the file is a valid video
        if self.get_mime() != 'video':
            self = None
            return
        
        self.force_file = self.force_file if force_file is None else force_file
    
    def get_total_frames_count(self):
        """
        Get the total number of frames in the video
        
        This use ffprobe to get the number of frames
        
        Returns:
            int: Total number of frames
        """
        
        ################################################################################
        # Execute ffprobe (to show streams), and get the output in JSON format
        # Actually counts packets instead of frames but it is much faster
        # https://stackoverflow.com/questions/2017843/fetch-frame-count-with-ffmpeg/28376817#28376817
        data = FFMPEG.call_ffprobe([
            '-v', 'error',
            '-select_streams', 'v:0',
            '-count_packets',
            '-show_entries', 'stream=nb_read_packets',
            '-of', 'csv=p=0',
            '-of', 'json',
            self.path
        ]).communicate()[0]
        
        # Convert data from JSON string to dictionary
        dict = json.loads(data)
        
        # Get the total number of frames
        return int(dict['streams'][0]['nb_read_packets'])
    
    def get_FFMPEG_size(self):
        """
        Get the video size (width, height)
        
        This use ffmpeg to get the video size
        
        Returns:
            list: [width, height] of the video
        """
        # Call ffmpeg to get the video size
        p = FFMPEG.call_ffmpeg([
            '-i', self.name,
        ])
        stdout, stderr = p.communicate()
        
        # Extract the size from the output
        video_lines = re.findall(': Video: ([^\n]+)', stdout)
        if not video_lines:
            return None
        
        # Extract the size
        matchs = re.findall("(\d{2,6})x(\d{2,6})", video_lines[0])
        if matchs:
            return [int(x) for x in matchs[0]]
        
        return None
    
    def metadata(self):
        """
        Get the video metadata
            
        This use hachoir to get the video metadata
            
        Returns:
            hachoir.metadata.Metadata: Video metadata
        """
        return extractMetadata(createParser(self))
        
    def get_thumbnail(self):
        """
        Get the video thumbnail
            
        This use hachoir to get the video thumbnail
        
        Returns:
            str: Path to the thumbnail file
        Raises:
            Exception: If the thumbnail file does not exists
        """
        thumb = None
        
        # Generate thumbnail if needed
        # TODO Check this part
        if self._thumbnail is None and not self.force_file:
            try:
                # Check if is video
                if self.get_mime() == 'video':
                    thumb = Video.get_thumb()
            except Exception as e:
                click.echo('{}'.format(e), err=True)
        elif self.is_custom_thumbnail:
            if not isinstance(self._thumbnail, str):
                raise TypeError('Invalid type for thumbnail: {}'.format(type(self._thumbnail)))
            elif not os.path.lexists(self._thumbnail):
                raise Exception('{} thumbnail file does not exists.'.format(self._thumbnail))
            thumb = self._thumbnail
            
        # Return thumbnail
        return thumb
    
    def get_FFMPEG_thumb(self, output : str = None, size : int = 200):
        """
        Get the video thumbnail using FFMPEG
        
        Args:
            output: Path to the output thumbnail file. If None, a temporary file will be created
            size: Size of the thumbnail (width or height, depending on the aspect ratio)
        Returns:
            str: Path to the thumbnail file
        Raises:
            Exception: If the video ratio is not available
        """
        
        # Create a temporary file if no output is provided
        output = output or tempfile.NamedTemporaryFile(suffix='.jpg').name
        
        # Get video metadata
        metadata = self.metadata()
        
        # Check if metadata is available
        if metadata is None:
            return
        
        # Get video duration
        duration = metadata.get('duration').seconds if metadata.has('duration') else 0
        # Get video size (Width, Height)
        ratio = self.get_size()
        
        if ratio is None:
            raise Exception('Video ratio is not available.')
        
        # Calculate width and height
        # Determine if landscape or portrait
        if ratio[0] / ratio[1] > 1:
            # Landscape
            width, height = size, -1
        else:
            # Portrait
            width, height = -1, size
        
        # Call ffmpeg to generate the thumbnail
        # Seek to the middle of the video and take one frame
        p = FFMPEG.call_ffmpeg([
            '-ss', str(int(duration / 2)),
            '-i', self.name,
            '-filter:v',
            'scale={}:{}'.format(width, height),
            '-vframes:v', '1',
            output,
        ])
        # Get the output
        p.communicate()
        
        # Return the output file if successful
        if not p.returncode and os.path.lexists(self.name):
            return output
        
        return None