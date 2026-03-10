import functools
import json
from xml.dom.minidom import Entity
from dbJson.file_message import FileMessage, FileMessageType
from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload_utils import FileManager_Upload_Utils
from file_manager.upload.file_manager_upload_video import FileManager_Upload_Video
from file_types.file import File
from file_types.video import Video
from telegram.telegram_manager_client import TelegramManagerClient


class FileManager_Upload:
    
    @staticmethod
    async def upload_file(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : File, 
        parent_message : FileMessage
        ) -> FileMessage:
        """
        Upload a file to the chat under the specified parent folder
        
        Args:
            client: The Telegram client
            chat_instance: The chat to upload the file to
            file: The file to upload
            parent_message: The parent folder message
        Returns:
            FileMessage: The uploaded file message wrapped in a FileMessage object
        Raises:
            Exception: If the parent is not a folder
        """
        
        # Check if the parent message is a folder
        json_data = json.loads(parent_message.telegram_message.message)
        type_value = json_data.get("Type")
        
        # Validate type
        if type_value != FileMessageType.FOLDER.value and type_value != FileMessageType.ROOT.value:
            # Raise and exception if the parent is not a folder as only a folder can contain files
            raise Exception("The parent is not a folder")
        
        # Update
        await parent_message.refresh(client, chat_instance)
        
        # Create the file message
        data = FileMessage.generate_json_caption(FileMessageType.FILE, file.file_name)
        # Set the parent
        data["Parent"] = FileMessage.calculate_message_link(chat_instance, parent_message)
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
            FileMessage.calculate_message_link(chat_instance, message)
        )
        
        # Return the uploaded file message
        return message
    
    @staticmethod
    async def __upload_generic_file(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : File, 
        message : FileMessage
        ):
        """
        Upload a generic file to Telegram as a comment to the specified message
        
        Args:
            client: Telegram manager client
            chat_instance: Chat entity to send the file to
            file: File to upload
            message: FileMessage to comment the file to
        """
        
        # File caption for the original video
        file_caption = FileMessage.generate_json_caption(FileMessageType.FILE, file.file_name)
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