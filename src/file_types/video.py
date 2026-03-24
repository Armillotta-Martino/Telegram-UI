from asyncio import subprocess
import json
import re
import tempfile

from hachoir.core import config as hachoir_config

from compression.FFMPEG import FFMPEG, FFMPEG_RELATIVE_PATH
from file_types.file import File
from file_types.image import Image

hachoir_config.quiet = True

class Video(File):
    """
    Video file type class
    
    Inherits from File
    """
    
    def __init__(self, file : File, force_file : bool = False) -> None:
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
    
    def get_total_frames_count(self) -> int:
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
    
    def get_video_resolution(self) -> list[int]:
        """
        Get the video resolution using ffprobe
        
        Args:
            video: The video file
        Returns:
            List[int]: The video resolution [width, height]
        """
        
        p = FFMPEG.call_ffmpeg([
            '-i', self.path,
        ])
        stdout, stderr = p.communicate()
        video_lines = re.findall(': Video: ([^\n]+)', stdout)
        
        if not video_lines:
            return
        
        matchs = re.findall("(\d{2,6})x(\d{2,6})", video_lines[0])
        if matchs:
            return [int(x) for x in matchs[0]]
        
    def extract_frame_from_video(self, time: float = 0.0) -> 'Image':
        """
        Extract a single frame from video data (bytes) at the given time (seconds)

        Returns the image as bytes (JPEG). Raises Exception on failure
        """
        # Build ffmpeg command to write a single jpeg frame to a temporary file,
        # then read the file bytes and delete the temporary file.
        ffmpeg_path = FFMPEG.__get_command_path("FFMPEG", FFMPEG_RELATIVE_PATH)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tmp_path = tmp.name
        tmp.close()

        # Scale to cover 320x320 (scale up/down preserving aspect) then center-crop to exactly 320x320
        # Use 'increase' (supported) instead of 'cover'
        vf_filter = 'scale=320:320:force_original_aspect_ratio=increase,crop=320:320'
        cmd = [
            ffmpeg_path,
            '-hide_banner', '-loglevel', 'error',
            '-ss', str(time),
            '-i', self.path,
            '-vf', vf_filter,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            tmp_path
        ]

        try:
            p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                stderr_text = err.decode('utf-8', errors='ignore') if isinstance(err, (bytes, bytearray)) else str(err)
                raise Exception(f'ffmpeg command failed with error: {stderr_text}')

            return File(tmp_path)
        except FileNotFoundError:
            raise Exception('ffmpeg command is not available. Thumbnails for videos are not available!')
        
    def get_ffprobe_file_details(self) -> dict:
        """
        Get the file details using ffprobe
        
        NOTE: The video argument is a Video object from video.py but as I have circular imports i use 
        a string for the type hint

        Args:
            video: The video file
        Returns:
            dict: The details of the file
        """
        # ffprobe call for get the file info as json
        p = FFMPEG.call_ffprobe([
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            self.path
        ])
        jsonResult = json.loads(p.communicate()[0].decode('utf-8'))

        # Format the result
        streams = []
        # Save the information i need
        for s in jsonResult['streams']:
            stream = {}
            stream["index"] = s['index']
            if 'codec_name' in s:
                stream["codec_name"] = s['codec_name']
            if 'codec_long_name' in s:
                stream["codec_long_name"] = s['codec_long_name']
            if 'codec_type' in s:
                stream["codec_type"] = s['codec_type']
            if 'codec_tag_string' in s:
                stream["codec_tag_string"] = s['codec_tag_string']
            if 'duration' in s:
                stream["duration"] = s['duration']
            if 'bit_rate' in s:
                stream["bit_rate"] = s['bit_rate']
            if 'tags' in s:
                if 'creation_time' in s['tags']:
                    stream["creation_time"] = s['tags']['creation_time']

            # Only video info
            if 'width' in s:
                stream["width"] = s['width']
            if 'height' in s:
                stream["height"] = s['height']
            if 'display_aspect_ratio' in s:
                stream["display_aspect_ratio"] = s['display_aspect_ratio']
            if 'r_frame_rate' in s:
                stream["r_frame_rate"] = s['r_frame_rate']
            if 'avg_frame_rate' in s:
                stream["avg_frame_rate"] = s['avg_frame_rate']
            if 'bits_per_raw_sample' in s:
                stream["bits_per_raw_sample"] = s['bits_per_raw_sample']

            # Only audio info
            if 'sample_fmt' in s:
                stream["sample_fmt"] = s['sample_fmt']
            if 'sample_rate' in s:
                stream["sample_rate"] = s['sample_rate']

            # Only image info
            if 'pix_fmt' in s:
                stream["pix_fmt"] = s['pix_fmt']
            if 'color_range' in s:
                stream["color_range"] = s['color_range']
            if 'color_space' in s:
                stream["color_space"] = s['color_space']
            if 'chroma_location' in s:
                stream["chroma_location"] = s['chroma_location']

            # Add stream to streams list
            streams.append(stream)

        format = {}
        if 'format' in jsonResult:
            if 'filename' in jsonResult['format']:
                format["filename"] = jsonResult['format']['filename']

            # Only image info
            if 'format_name' in jsonResult['format']:
                format["format_name"] = jsonResult['format']['format_name']
            if 'format_long_name' in jsonResult['format']:
                format["format_long_name"] = jsonResult['format']['format_long_name']

            if 'size' in jsonResult['format']:
                format["size"] = jsonResult['format']['size']
            if 'bit_rate' in jsonResult['format']:
                format["bit_rate"] = jsonResult['format']['bit_rate']
            if 'tags' in jsonResult['format']:
                if 'major_brand' in jsonResult['format']:
                    format["major_brand"] = jsonResult['format']['tags']['major_brand']
                if 'creation_time' in jsonResult['format']:
                    format["creation_time"] = jsonResult['format']['tags']['creation_time']

        result = {
            "streams": streams,
            "format": format
        }
        return result
        
