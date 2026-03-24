from io import SEEK_SET, FileIO
import mimetypes
import os

mimetypes.init()

class File(FileIO):
    """
    A class that represent a generic file
    """
    
    def __init__(self, path, force_document : bool = False) -> None:
        """
        Constructor
        
        Args:
            path: The file path
            force_document: Whether to force the file to be treated as a document
        Raises:
            ValueError: If the file is not valid
        """
        # Store the path and force_document
        self.path = path
        self.force_document = force_document
        
        super().__init__(path, mode='rb')
        
        # Check if the file is valid
        if not self.__is_valid_file():
            raise ValueError('File "{}" is not valid.'.format(self.path))

    @property
    def file_name(self) -> str:
        """
        Get the file name
        
        This override the name (Usually it's a path like C:\\file)
        
        Returns:
            str: The file name
        """
        return os.path.basename(self.path)
    
    @property
    def size(self) -> int:
        """
        Get the file size
        
        Returns:
            int: The file size in bytes
        """
        return os.path.getsize(self.path)

    @property
    def short_name(self) -> str:
        """
        Get the file short name (without extension)
        
        Returns:
            str: The file short name
        """
        return '.'.join(self.file_name.split('.')[:-1])
    
    @property 
    def bytes(self) -> bytes:
        """
        Get the file content as bytes
        
        Returns:
            bytes: The file content as bytes
        """
        with open(self.path, 'rb') as f:
            return f.read()
        
    def __is_valid_file(self, error_logger=None) -> bool:
        """
        Check if the file is valid
            
        Validity conditions:
        - The file exists
        - The file size is greater than 0 bytes
        
        Args:
            error_logger: A callable to log errors
        Returns:
            bool: Whether the file is valid
        """
        # Initialize
        error_message = None
        
        # Check the path
        if not os.path.lexists(self.path):
            error_message = 'File "{}" does not exist.'.format(self.path)
        
        # Check the size
        elif self.size == 0:
            error_message = 'File "{}" is empty.'.format(self.path)
        
        # Log error if needed
        if error_message and error_logger is not None:
            error_logger(error_message)
            
        # Return validity
        return error_message is None
    
    def get_mime(self) -> str:
        """
        Get the file mime (type)

        https://pro.europeana.eu/page/media-formats-mime-types#:~:text=A%20MIME%20type%20(also%20known,accessed%20and%20used%20over%20time
        """
        return (mimetypes.guess_type(self.path)[0] or ('')).split('/')[0]
    
    def seek(self, offset: int, whence: int = SEEK_SET, split_seek: bool = False) -> int:
        """
        Seek to a specific position in the file
            
        This is used to go to a specific position in a file
        
        Args:
            offset: Initial offset
            whence: FILEIO whence value
            split_seek: Whether to use split seek (used for splitted files)
        Returns:
            int: New position
        """
        if not split_seek:
            self.remaining_size += self.tell() - offset
        return super().seek(offset, whence)