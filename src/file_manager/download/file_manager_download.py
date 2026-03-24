import functools
import json
import os
from tkinter import filedialog
from xml.dom.minidom import Entity

from dbJson.file_message import FileMessage, FileMessageType
from file_manager.file_manager_utils import FileManager_Utils
from telegram.telegram_manager_client import TelegramManagerClient
from utils import free_disk_usage

class FileManager_Download:
    """
    Class responsible for downloading files from Telegram, ensuring that the total size of the file 
    parts does not exceed available disk space. It also allows the user to choose the download 
    location and handles the download
    """
    
    @staticmethod
    async def download_file(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : FileMessage,
        ) -> str:
        """
        Downloads a file from Telegram, ensuring that the total size of the file parts does 
        not exceed available disk space
        
        After a few tests i saw that the download speed is not as fast as in the web version of 
        Telegram, but it is the best we can achieve with the current Telegram API.
        All the tests can be seen in the learn folder

        Args:
            client (TelegramManagerClient): The Telegram manager client
            chat_instance (Entity): The chat instance from which to download the file
            file (FileMessage): The file message to download

        Raises:
            Exception: If the message is not a file
            Exception: If there is not enough disk space to download the file

        Returns:
            str: The path to the downloaded file, or None if the user cancels the download
        """
        # Check the type of the message
        json_data = json.loads(file.telegram_message.message)
        type_value = json_data.get("Type")
        
        # Validate type
        if type_value != FileMessageType.FILE.value:
            # Raise an exception if the message is not a file
            raise Exception("The message is not a file")
        
        totalDownloadSize = 0
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(chat_instance, reply_to=file.telegram_message.id):
            # Find the file message
            json_message = json.loads(message.message)
            if json_message.get("Part") is not None and json_message.get("Part") == FileMessageType.LRV.value or \
               json_message.get("Type") is not None and json_message.get("Type") == FileMessageType.THUMBNAIL.value:
                # Skip LRV and thumbnail files
                continue
            
            # Sum the downloaded size
            totalDownloadSize += message.media.document.size
            
        # Check disk space
        if totalDownloadSize > free_disk_usage():
            raise Exception('There is no disk space to download "{}". Space required: {}'.format(file.file_name, totalDownloadSize - free_disk_usage()))
        
        download_files = []
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(chat_instance, reply_to=file.telegram_message.id):
            
            # Find the file message
            json_message = json.loads(message.message)
            
            if json_message.get("Part") is not None and json_message.get("Part") == FileMessageType.LRV.value or \
               json_message.get("Type") is not None and json_message.get("Type") == FileMessageType.THUMBNAIL.value:
                # Skip LRV and thumbnail files
                continue
            
            # Download the file bytes
            download_bytes = await client.download_media(
                message, 
                bytes, 
                progress_callback=functools.partial(FileManager_Utils.progress, text=f"Downloading {file.file_name} ({message.media.document.size} bytes) part {json_message.get('Part') if json_message.get('Part') is not None else 'main'}")
            )
            
            # Append to downloaded files list
            download_files.append({
                "message": message.message, 
                "download_bytes": download_bytes
            })
            
        # Let the user choose the download location
        download_location = filedialog.askdirectory(title="Select the download location")
        
        if not download_location:
            # User cancelled
            return None

        # Write parts in the correct order. Each downloaded_file stores the original
        # message JSON in the "message" key; use its "Part" field (0 for main) to order.
        parts = []
        for downloaded_file in download_files:
            try:
                # Extract the part index from the message JSON
                meta = json.loads(downloaded_file.get('message') or '{}')
                part_index = int(meta.get('Part')) if meta.get('Part') is not None else 0
            except Exception:
                part_index = 0
                
            # Append the part index and the downloaded bytes to the parts list
            parts.append((part_index, downloaded_file.get('download_bytes') or b''))
            
        # Sort parts by their index to ensure correct order
        parts.sort(key=lambda x: x[0])
        
        # Construct the output file path
        output_path = os.path.join(download_location, file.file_name)
        
        # Write all parts sequentially into the output file
        with open(output_path, 'wb') as out:
            for _, chunk in parts:
                out.write(chunk)

        # Return the download location (full path)
        return output_path