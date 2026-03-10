import json
import math
import os

from dbJson.file_message import FileMessage, FileMessageType
from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload_utils import FileManager_Upload_Utils
from file_types.video import Video
import functools

from telegram.telegram_manager_client import TelegramManagerClient
from telethon.tl.types import DocumentAttributeVideo
from xml.dom.minidom import Entity

# Import LRV class to generate low-resolution videos
from file_types.LRV import LRV

# Import FFMPEG class to handle video compression
from compression.FFMPEG import FFMPEG


class FileManager_Upload_Video:
    '''
    Upload Video Region
    
    This region contains all the functions to execute actions on Video file
    '''
    
    @staticmethod
    async def upload_video(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : Video, 
        message : FileMessage
        ):
        """
        ### Video Info
        # NOTE: Removed now as i want to see ifi can get some of those info from telegram itself
        
        # Get video info
        video_info = FFMPEG.get_ffprobe_file_details(file)
        
        # Send video info as a message
        await client.send_message(
            chat_instance,
            message = json.dumps(video_info, indent=4),
            comment_to = message.telegram_message, 
        )
        """
        ### LRV
        
        # Generate the LRV video
        LRV_video = LRV.generate_video_low_resolution(file)
        
        # File caption for LRV
        file_caption_lrv = FileMessage.generate_json_caption(FileMessageType.LRV, file.file_name)
        
        # Post the LRV video
        await FileManager_Upload_Video.__process_normal_video(client, chat_instance, LRV_video, caption = file_caption_lrv, comment_to = message, force_document = False, supports_streaming = True)
        
        LRV_video.close()
        
        # Delete the temporary LRV file
        # NOTE: The LRV video is a temporary file, so we need to delete it after uploading otherwise 
        # it will create problems with the sync function that will upload it as a normal file
        os.remove(LRV_video.path)
        
        ### Original video
        
        # File caption for the original video
        file_caption = FileMessage.generate_json_caption(FileMessageType.FILE, file.file_name)
        
        # Check if the file size is bigger then the max allowed size for the user
        if file.size > client.max_file_size:
            # Process as large video
            await FileManager_Upload_Video.__process_large_video(client, chat_instance, file, caption = file_caption, comment_to = message)
        else:
            # Process as normal video
            await FileManager_Upload_Video.__process_normal_video(client, chat_instance, file, caption = file_caption, comment_to = message, force_document = True)
    
    @staticmethod    
    async def __process_normal_video(
        client : TelegramManagerClient, 
        chat_entity : Entity, 
        file: Video, 
        caption : str, 
        comment_to : FileMessage, 
        force_document = False, 
        supports_streaming : bool = False
        ):
        """
        File is normal file (less than max allowed size), upload it as a single file
        
        Args:
            client: Telegram manager client
            chat_entity: Chat entity to send the file to
            file: Video file to upload
            caption: Caption for the file
            comment_to: FileMessage to comment the file to
            force_document: Whether to force the file to be sent as a document
            supports_streaming: Whether the video supports streaming
        """
        
        # Get video details
        json_video_info = FFMPEG.get_ffprobe_file_details(file)
        # Convert caption to JSON string
        json_file_message = json.dumps(caption, indent=4)
        
        # Upload the file data
        # This is done before send the message with the file to have the file already uploaded when sending the message
        file = await FileManager_Upload_Utils.upload_file_data(
            client, 
            file, 
            file_output_size = file.size, 
            file_output_path = file.path, 
            progress_callback=functools.partial(FileManager_Utils.progress, text=f"Uploading {file.file_name}")
        )
        
        # Send the file message
        await client.send_file(
            chat_entity, 
            file, 
            comment_to = comment_to.telegram_message, 
            caption = json_file_message, 
            force_document = force_document, 
            supports_streaming = supports_streaming,
            # Add video attributes
            # This is needed to have the video playable in Telegram
            attributes = [
                DocumentAttributeVideo(
                    duration = float(json_video_info["streams"][0]["duration"]),
                    w = int(json_video_info["streams"][0]["width"]),
                    h = int(json_video_info["streams"][0]["height"]),
                    supports_streaming = supports_streaming
                )
            ]
        )

    @staticmethod    
    async def __process_large_video(
        client: TelegramManagerClient, 
        chat_entity : Entity, 
        file : Video, 
        caption : str, 
        comment_to : FileMessage
        ):
        """
        Process large video file by splitting it into parts and uploading each part separately
        
        Args:
            client: Telegram manager client
            chat_entity: Chat entity to send the file to
            file: Video file to upload
            caption: Caption for the file
            comment_to: FileMessage to comment the file to
        """
        # Calculate how many parts are needed
        parts = math.ceil(file.size / client.max_file_size)
        # Calculate the zfill for part numbering (e.g., 001, 002, etc.)
        zfill = int(math.log10(10)) + 1

        # Loop every part
        for part in range(parts):
            # Calculate the part size
            # I read MAX_FILE_SIZE at a time
            size = file.size - (part * client.max_file_size) if part >= parts - 1 else client.max_file_size
            # Generate the part name
            part_name = '{}.{}'.format(file.name, str(part).zfill(zfill))
            # Upload the part
            splitted_file = await FileManager_Upload_Utils.upload_file_data(
                client, 
                file, 
                file_output_size = size, 
                file_output_path = part_name, 
                progress_callback=functools.partial(FileManager_Utils.progress, text=f"Uploading part {part+1}/{parts} {part_name}")
            )
            
            # Add the part to the caption
            caption["Part"] = part + 1
            # Convert caption to JSON string
            json_file_message = json.dumps(caption, indent=4)
            # Send the file
            await client.send_file(chat_entity, splitted_file, comment_to = comment_to.telegram_message, caption = json_file_message, force_document = True)
            # Get the next part
            file.seek(client.max_file_size * part, split_seek=True)