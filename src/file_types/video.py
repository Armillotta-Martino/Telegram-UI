import json
import os
import re
import tempfile

import click
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from hachoir.core import config as hachoir_config

from file_types.compression.FFMPEG import FFMPEG
from file_types.file import File

hachoir_config.quiet = True

class Video(File):
    """
    Class to execute actions with video

    Raises:
        ThumbVideoError: _description_

    Returns:
        _type_: _description_
    """
    
    def __init__(
        self, 
        file : File, 
        force_file : bool = False
        ):
        # Convert File to Video
        super().__init__(file.path)
        
        # Check if the file is a valid video
        if self.get_mime() != 'video':
            self = None
            return
        
        self.force_file = self.force_file if force_file is None else force_file
    
    def get_total_frames_count(self):
        """
        Use ffprobe for counting the total number of frames
        
        Args:
            video_file (File): _description_

        Returns:
            _type_: _description_
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
        Get the size of the video using FFMPEG

        Args:
            video_file (File): _description_

        Returns:
            _type_: _description_
        """
        p = FFMPEG.call_ffmpeg([
            '-i', self.name,
        ])
        stdout, stderr = p.communicate()
        video_lines = re.findall(': Video: ([^\n]+)', stdout)
        if not video_lines:
            return
        matchs = re.findall("(\d{2,6})x(\d{2,6})", video_lines[0])
        if matchs:
            return [int(x) for x in matchs[0]]
    
    def metadata(self):
        """
        Extract the metadata of the video

        Args:
            file (_type_): _description_

        Returns:
            _type_: _description_
        """
        return extractMetadata(createParser(self))
        
    def get_thumbnail(self):
        """
        Get the file thumbnail
        """
        thumb = None
        if self._thumbnail is None and not self.force_file:
            try:
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
        return thumb
    
    def get_FFMPEG_thumb(
        self, 
        output : str = None, 
        size : int = 200
        ):
        """
        Generate the thumnail of the video

        Args:
            file (File): _description_
            output (str, optional): _description_. Defaults to None.
            size (int, optional): _description_. Defaults to 200.

        Raises:
            ThumbVideoError: _description_

        Returns:
            _type_: _description_
        """
        output = output or tempfile.NamedTemporaryFile(suffix='.jpg').name
        metadata = self.metadata()
        
        if metadata is None:
            return
        
        duration = metadata.get('duration').seconds if metadata.has('duration') else 0
        ratio = self.get_size()
        
        if ratio is None:
            raise Exception('Video ratio is not available.')
        
        if ratio[0] / ratio[1] > 1:
            width, height = size, -1
        else:
            width, height = -1, size
        
        p = FFMPEG.call_ffmpeg([
            '-ss', str(int(duration / 2)),
            '-i', self.name,
            '-filter:v',
            'scale={}:{}'.format(width, height),
            '-vframes:v', '1',
            output,
        ])
        p.communicate()
        if not p.returncode and os.path.lexists(self.name):
            return output