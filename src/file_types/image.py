import json

from hachoir.core import config as hachoir_config

from compression.FFMPEG import FFMPEG
from file_types.file import File

hachoir_config.quiet = True

class Image(File):
    """
    Image file type class
    
    Inherits from File
    """
    
    def __init__(self, file : File, force_file : bool = False) -> None:
        """
        Constructor
        
        Args:
            file: The file to convert to Image
            force_file: Force to treat the file as an image even if the mime type is not image
        """
        # Convert File to Image
        super().__init__(file.path)
        
        # Check if the file is a valid image
        if self.get_mime() != 'image':
            self = None
            return
        
        self.force_file = self.force_file if force_file is None else force_file
    
    def get_dimensions(self) -> tuple[int, int]:
        """
        Get the dimensions of the image
        
        This use ffprobe to get the dimensions
        
        Returns:
            tuple: (width, height) of the image
        """
        
        ################################################################################
        # Execute ffprobe (to show streams), and get the output in JSON format
        data = FFMPEG.call_ffprobe([
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            '-of', 'json',
            self.path
        ]).communicate()[0]
        
        # Convert data from JSON string to dictionary
        dict = json.loads(data)
        
        # Get the dimensions
        return int(dict['streams'][0]['width']), int(dict['streams'][0]['height'])