import json
import math
import os
import functools
from xml.dom.minidom import Entity

from telethon import types 
from telethon.tl.types import DocumentAttributeImageSize, DocumentAttributeVideo

# Import DbJson
from dbJson.telegram_message import TelegramMessage, TelegramMessageType

from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload_utils import FileManager_Upload_Utils
from telegram.telegram_manager_client import TelegramManagerClient

## Import file List[typ# Import LRV class to generate low-resolution videos
from file_types.LRV import LRV
from file_types.image import Image
from file_types.video import Video

class FileManager_Upload_Video:
    """
    Class to handle the upload of video files to Telegram, including generating and uploading a 
    thumbnail and a low-resolution version of the video
    """
    
    @staticmethod
    async def upload_video(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : Video, 
        message : TelegramMessage
        ) -> list[types.Message] | types.Message:
        """
        Upload a video file to Telegram, including generating and uploading a thumbnail and a low-resolution version of the video

        Args:
            client (TelegramManagerClient): The Telegram manager client to use for uploading the video
            chat_instance (Entity): The chat entity to send the video to
            file (Video): The video file to upload
            message (TelegramMessage): The message to comment the video to
        Returns:
            list[types.Message] | types.Message: The message(s) containing the uploaded video(s)
        Raises:
            Exception: If the video upload fails
        """
        
        '''
        ### Video Info
        # NOTE: Removed now as i want to see if i can get some of those info from telegram itself
        
        # Get video info
        video_info = file.get_ffprobe_file_details()
        
        # Send video info as a message
        await client.send_message(
            chat_instance,
            message = json.dumps(video_info, indent=4),
            comment_to = message.telegram_message, 
        )
        '''
        
        ### Thumbnail
        
        # Generate and upload the thumbnail for the video
        await FileManager_Upload_Video.__process_thumbnail(client, chat_instance, file, comment_to = message)
        
        ### LRV
        
        # Generate the LRV video
        LRV_video = LRV.generate_video_low_resolution(file)
        
        if LRV_video is None:
            # If the LRV video generation failed, log the error and continue with the original video
            print(f"Failed to generate LRV video for {file.file_name}. Continuing with original video.")
            raise Exception(f"Failed to generate LRV video for {file.file_name}.")
        
        # File caption for LRV
        file_caption_lrv = TelegramMessage.generate_json_caption(TelegramMessageType.LRV, file.file_name)
        
        # Post the LRV video
        await FileManager_Upload_Video.__process_normal_video(
            client, 
            chat_instance, 
            LRV_video, 
            caption = file_caption_lrv, 
            comment_to = message, 
            force_document = False, 
            supports_streaming = True
        )
        
        LRV_video.close()
        
        # Delete the temporary LRV file
        # NOTE: The LRV video is a temporary file, so we need to delete it after uploading otherwise 
        # it will create problems with the sync function that will upload it as a normal file
        os.remove(LRV_video.path)
        
        ### Original video
        
        # File caption for the original video
        file_caption = TelegramMessage.generate_json_caption(TelegramMessageType.FILE, file.file_name)
        
        # Check if the file size is bigger then the max allowed size for the user
        if file.size > client.max_file_size:
            # Process as large video
            return await FileManager_Upload_Video.__process_large_video(client, chat_instance, file, caption = file_caption, comment_to = message)
        else:
            # Process as normal video
            return await FileManager_Upload_Video.__process_normal_video(client, chat_instance, file, caption = file_caption, comment_to = message, force_document = True)
    
    @staticmethod    
    async def __process_normal_video(
        client : TelegramManagerClient, 
        chat_entity : Entity, 
        file: Video, 
        caption : str, 
        comment_to : TelegramMessage, 
        force_document = False, 
        supports_streaming : bool = False
        ) -> types.Message:
        """
        File is normal file (less than max allowed size), upload it as a single file
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_entity (Entity): Chat entity to send the file to
            file (Video): Video file to upload
            caption (str): Caption for the file
            comment_to (TelegramMessage): TelegramMessage to comment the file to
            force_document (bool): Whether to force the file to be sent as a document
            supports_streaming (bool): Whether the video supports streaming
        Returns:
            types.Message: The message containing the uploaded video
        """
        
        # Get video details
        json_video_info = file.get_ffprobe_file_details()
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
        return await client.send_file(
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
        comment_to : TelegramMessage
        ) -> list[types.Message]:
        """
        Process large video file by splitting it into parts and uploading each part separately
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_entity (Entity): Chat entity to send the file to
            file (Video): Video file to upload
            caption (str): Caption for the file
            comment_to (TelegramMessage): TelegramMessage to comment the file to
        Returns:
            list[types.Message]: The list of messages containing the uploaded video parts
        """
        # Calculate how many parts are needed
        parts = math.ceil(file.size / client.max_file_size)
        # Calculate the zfill for part numbering (e.g., 001, 002, etc.)
        zfill = int(math.log10(10)) + 1
        
        messages = list()

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
            message =await client.send_file(chat_entity, splitted_file, comment_to = comment_to.telegram_message, caption = json_file_message, force_document = True)
            # Append the message to the list of messages
            messages.append(message)
            # Get the next part
            file.seek(client.max_file_size * part)
        
        # Return the list of messages for all parts
        return messages
            
    @staticmethod    
    async def __process_thumbnail(
        client : TelegramManagerClient, 
        chat_entity : Entity, 
        file: Video, 
        comment_to : TelegramMessage,
        ) -> None:
        """
        File is normal file (less than max allowed size), upload it as a single file
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_entity (Entity): Chat entity to send the file to
            file (Video): Video file to use to generate the thumbnail
            comment_to (TelegramMessage): TelegramMessage to comment the file to
        Returns:
            None
        """
        
        # Extract a frame from the video to use as thumbnail for the LRV video
        thumb_file = Image(file.extract_frame_from_video())
        
        # Upload the file data
        # This is done before send the message with the file to have the file already uploaded when sending the message
        thumb_file_thumb = await FileManager_Upload_Utils.upload_file_data(
            client, 
            thumb_file, 
            file_output_size = thumb_file.size, 
            file_output_path = thumb_file.path, 
            progress_callback=functools.partial(FileManager_Utils.progress, text=f"Uploading Thumbnail for {file.file_name}")
        )
        
        # Generate the thumbnail caption
        file_caption_thumbnail = TelegramMessage.generate_json_caption(TelegramMessageType.THUMBNAIL, file.file_name)
        json_file_message = json.dumps(file_caption_thumbnail, indent=4)
        
        img_dimensions = thumb_file.get_dimensions()
        
        # Send the file message
        await client.send_file(
            chat_entity, 
            thumb_file_thumb, 
            comment_to = comment_to.telegram_message, 
            caption = json_file_message,
            # Add video attributes
            # This is needed to have the video playable in Telegram
            attributes = [
                DocumentAttributeImageSize(
                    w = img_dimensions[0], 
                    h = img_dimensions[1]
                )
            ]
        )
        
        # Close and delete the temporary thumbnail file
        try:
            # thumb_file is a File (FileIO); close its descriptor first
            try:
                thumb_file.close()
            except Exception:
                pass
            if os.path.exists(thumb_file.path):
                os.remove(thumb_file.path)
        except Exception:
            # On Windows the file may still be locked briefly; ignore cleanup errors
            pass