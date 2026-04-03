import functools
import json
from xml.dom.minidom import Entity

# Import DbJson
from dbJson.telegram_message import TelegramMessage, TelegramMessageType

from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload_utils import FileManager_Upload_Utils
from file_manager.upload.file_manager_upload_video import FileManager_Upload_Video
from telegram.telegram_manager_client import TelegramManagerClient

# Import file types
from file_types.file import File
from file_types.video import Video

class FileManager_Upload:
    """
    Class responsible for handling file uploads to Telegram, including generic files and videos. 
    It provides methods to upload files to a specified chat and parent folder, ensuring that the 
    parent is a valid folder before proceeding with the upload. The class also includes a helper 
    method for uploading generic files as comments to the parent message
    """
    
    @staticmethod
    async def upload_file(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : File, 
        parent_message : TelegramMessage
        ) -> TelegramMessage:
        """
        Upload a file to the chat under the specified parent folder
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat to upload the file to
            file (File): The file to upload
            parent_message (TelegramMessage): The parent folder message
        Returns:
            TelegramMessage: The uploaded file message wrapped in a TelegramMessage object
        Raises:
            Exception: If the parent is not a folder
        """
        
        # Check if the parent message is a folder
        if parent_message.is_folder is False:
            # Raise and exception if the parent is not a folder as only a folder can contain files
            raise Exception("The parent is not a folder")
        
        # Update
        await parent_message.refresh(client, chat_instance)
        
        # Create the file message
        data = TelegramMessage.generate_json_caption(TelegramMessageType.FILE, file.file_name)
        # Set the parent
        data["Parent"] = TelegramMessage.calculate_message_link(chat_instance, parent_message)
        # Send the file message
        message = await FileManager_Utils.send_telegram_message(
            client, 
            chat_instance, 
            data
        )
        
        '''
        # Check the remote file size and the local file size
        if hasattr(message.media, 'document') and file.size != message.media.document.size:
            raise Exception(
                'Remote document size: {} bytes (local file size: {} bytes)'.format(
                    message.media.document.size, file.size))
        '''
        
        # Get the file mime type
        mime = file.get_mime()
        
        # Handle the file upload based on the mime type
        match(mime):
            case "video":
                # Upload video file
                await FileManager_Upload_Video.upload_video(client, chat_instance, Video(file), message)
            case _:
                # Upload generic file
                await FileManager_Upload.__upload_generic_file(client, chat_instance, file, message)
            
        # Update parent message children
        await parent_message.add_children(
            client, 
            chat_instance, 
            TelegramMessage.calculate_message_link(chat_instance, message)
        )
        
        # Refresh the parent message to update the children list
        await parent_message.refresh(client, chat_instance)
        
        # Return the uploaded file message
        return message
    
    @staticmethod
    async def __upload_generic_file(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : File, 
        message : TelegramMessage
        ) -> None:
        """
        Upload a generic file to Telegram as a comment to the specified message
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_instance (Entity): Chat entity to send the file to
            file (File): File to upload
            message (TelegramMessage): TelegramMessage to comment the file to
        Returns:
            None
        """
        
        # File caption for the original video
        file_caption = TelegramMessage.generate_json_caption(TelegramMessageType.FILE, file.file_name)
        json_file_message = json.dumps(file_caption, indent=4)
        
        # Upload the file data
        file = await FileManager_Upload_Utils.upload_file_data(
            client, 
            file, 
            file_output_size = file.size, 
            file_output_path = file.path, 
            progress_callback=functools.partial(FileManager_Utils.progress, text=f"Uploading {file.file_name}")
        )
        # Send the file as a comment of the message
        await client.send_file(
            chat_instance, 
            file,
            # Add the file to the comment
            comment_to = message.telegram_message,
            caption = json_file_message, 
            force_document = True,
        )