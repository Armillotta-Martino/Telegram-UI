import json
import tempfile

from hachoir.core import config as hachoir_config

from compression.FFMPEG import FFMPEG
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
            file (File): The file to convert to Video
            force_file (bool, optional): Force to treat the file as a video even if the mime type is not video
        Returns:
            None
        """
        # Convert File to Video
        super().__init__(file.path)
        
        # Check if the file is a valid video
        if self.get_mime() != 'video':
            self = None
            return
        
        self.force_file = self.force_file if force_file is None else force_file
    
    @property
    def length_seconds(self) -> float:
        """
        Get the video length in seconds
        
        Returns:
            float: The video length in seconds
        """
        details = self.get_ffprobe_file_details()
        for s in details.get("streams", []):
            if s.get("codec_type") == "video":
                if "duration" in s:
                    return float(s["duration"])
        return 0.0
    
    def get_video_resolution(self) -> list[int]:
        """
        Get the video resolution using ffprobe
        
        Returns:
            List[int]: The video resolution [width, height]
        """
        
        # Use ffprobe (JSON) to get stream width/height reliably
        details = self.get_ffprobe_file_details()
        for s in details.get("streams", []):
            if s.get("codec_type") == "video":
                if "width" in s and "height" in s:
                    return [int(s["width"]), int(s["height"])]
        return
        
    def extract_frame_from_video(self, time: float = 0.0) -> 'Image':
        """
        Extract a single frame from video data (bytes) at the given time (seconds)

        Returns the image as bytes (JPEG). Raises Exception on failure
        
        Args:
            time (float, optional): The time in seconds to extract the frame from. Defaults to 0.0
        Returns:
            Image: The extracted frame as an Image object
        """
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tmp_path = tmp.name
        tmp.close()

        # Scale to cover 320x320 (scale up/down preserving aspect) then center-crop to exactly 320x320
        # Use 'increase' (supported) instead of 'cover'
        vf_filter = 'scale=320:320:force_original_aspect_ratio=increase,crop=320:320'
        cmd = [
            '-hide_banner', '-loglevel', 'error',
            '-ss', str(time),
            '-i', self.path,
            '-vf', vf_filter,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            tmp_path
        ]
        
        # Call FFMPEG to extract the frame and save it as a JPEG image
        FFMPEG.call_ffmpeg(cmd).communicate()
        
        # Return the extracted frame file
        return Image(File(tmp_path))
        
    def get_ffprobe_file_details(self) -> dict:
        """
        Get the file details using ffprobe
        
        NOTE: The video argument is a Video object from video.py but as I have circular imports i use 
        a string for the type hint

        Returns:
            dict: The details of the file
        """
        # ffprobe call for get the file info as json
        p = FFMPEG.call_ffprobe([
            '-v', 'error',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            self.path
        ])
        stdout, stderr = p.communicate()
        
        # Parse the ffprobe output as JSON
        jsonResult = json.loads(stdout)

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
        
