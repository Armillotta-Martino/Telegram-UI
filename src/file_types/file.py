from io import SEEK_SET, FileIO
import mimetypes
import os

from hachoir.metadata.metadata import RootMetadata

mimetypes.init()

class File(FileIO):
    
    def __init__(self, path, force_document : bool = False):
        # Store the path manually
        self.path = path
        self.force_document = force_document
        super().__init__(path, mode='rb')
        # Check if the file is valid
        if not self.__is_valid_file():
            self = None

    @property
    def file_name(self):
        """
        Get the file name
        This override the name (Usually it's a path like C:\\file)
        """
        return os.path.basename(self.path)
    
    @property
    def size(self):
        """
        Get the file size
        """
        return os.path.getsize(self.path)

    @property
    def short_name(self):
        """
        Get the file short name (without extension)
        """
        return '.'.join(self.file_name.split('.')[:-1])
    
    def __is_valid_file(self, error_logger=None):
        """
        Check if the file is valid
        For be valid it need to exist and not be empty
        """
        error_message = None
        # Check the path
        if not os.path.lexists(self.path):
            error_message = 'File "{}" does not exist.'.format(self.path)
        
        # Check the size
        elif self.size == 0:
            error_message = 'File "{}" is empty.'.format(self.path)
            
        if error_message and error_logger is not None:
            error_logger(error_message)
        return error_message is None
    
    def __metadata_has(metadata: RootMetadata, key: str):
        try:
            return metadata.has(key)
        except ValueError:
            return False
    
    def get_mime(self):
        """
        Get the file mime (type)

        https://pro.europeana.eu/page/media-formats-mime-types#:~:text=A%20MIME%20type%20(also%20known,accessed%20and%20used%20over%20time.
        """
        return (mimetypes.guess_type(self.path)[0] or ('')).split('/')[0]
    
    def seek(self, offset: int, whence: int = SEEK_SET, split_seek: bool = False) -> int:
        if not split_seek:
            self.remaining_size += self.tell() - offset
        return super().seek(offset, whence)
    
    '''
    @property
    def file_attributes(self):
        """
        Get the file metadata attributes
        """
        #if self.force_file:
        #    return [DocumentAttributeFilename(self.file_name)]
        #else:
        return self.__get_file_attributes(self.path)
    
    def __get_file_attributes(self, file):
        """
        Get the file attributes from metadata
        """
        attrs = []
        if self.get_mime(file) == 'video':
            # File is a video
            metadata = Video.video_metadata(file)
            video_meta = metadata
            meta_groups = None
            if hasattr(metadata, '_MultipleMetadata__groups'):
                # Is mkv
                meta_groups = metadata._MultipleMetadata__groups
            if metadata is not None and not metadata.has('width') and meta_groups:
                video_meta = meta_groups[next(filter(lambda x: x.startswith('video'), meta_groups._key_list))]
            if metadata is not None:
                supports_streaming = isinstance(video_meta, MP4Metadata)
                attrs.append(DocumentAttributeVideo(
                    (0, metadata.get('duration').seconds)[metadata_has(metadata, 'duration')],
                    (0, video_meta.get('width'))[metadata_has(video_meta, 'width')],
                    (0, video_meta.get('height'))[metadata_has(video_meta, 'height')],
                    False,
                    supports_streaming,
                ))
        return attrs
    '''