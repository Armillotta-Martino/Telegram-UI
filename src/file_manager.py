import asyncio
import hashlib
import json
import math
import os
from typing import Optional
from xml.dom.minidom import Entity
import click

from telethon import TelegramClient, utils, helpers, custom
from telethon.tl import types, TLRequest, functions
from telethon.errors import InvalidBufferError
from telethon.tl.types import DocumentAttributeVideo
from telethon.tl.types import InputMessagesFilterPinned

from config import MAX_RECONNECT_RETRIES, MIN_RECONNECT_WAIT, PARALLEL_UPLOAD_BLOCKS, PART_MAX_SIZE, RECONNECT_TIMEOUT, SMALL_FILE_THRESHOLD
from dbJson.file_message import FileMessage, FileMessageType
from telegram.telegram_manager_client import TelegramManagerClient

from compression.FFMPEG import FFMPEG
from file_types.LRV import LRV
from file_types.file import File
from file_types.video import Video

class FileManager():
    """
    Class to work with Telegram messages as files and folders
    """
    
    async def __send_telegram_message(client : TelegramManagerClient, target_chat_instance: Entity, message_json : dict[str, any]) -> FileMessage:
        """
        Send a telegram message with a JSON content
        
        Args:
            client: The telegram client to use
            target_chat_instance: The chat to send the message to
            message_json: The JSON content of the message
        Returns:
            FileMessage: The sent message wrapped in a FileMessage object
        Raises:
            TypeError: If the message_json is not a dict
        """
        # Validate input
        if not isinstance(message_json, dict):
            raise TypeError(
                f"__send_telegram_message expects a JSON dict, got {type(message_json).__name__}"
            )
        
        # Convert dict to JSON string
        json_text = json.dumps(message_json, ensure_ascii=False, indent=4)

        # Send message
        telegram_message = await client.send_message(
            entity=target_chat_instance, 
            message=json_text
        )
        
        # Wrap in FileMessage
        return FileMessage(telegram_message)

    async def __reconnect(self, client : TelegramManagerClient, reconnecting_lock : asyncio.Lock, upload_semaphore : asyncio.Semaphore):
        """
        Reconnects to Telegram servers
        
        This function is used to reconnect to Telegram servers when the connection is lost
        It uses a lock to prevent multiple reconnection at the same time
            
        Args:
            client: The Telegram client to reconnect
            reconnecting_lock: A lock to prevent multiple reconnection at the same time
            upload_semaphore: A semaphore to limit the number of parallel uploads
        Raises:
            Exception: If the reconnection fails
        """
        
        # Acquire the lock
        await reconnecting_lock.acquire()
        
        # Check if the client is already connected
        if client.is_connected():
            # Reconnected in another task
            reconnecting_lock.release()
            return
        
        # Decreases the upload semaphore by one
        if self.parallel_upload_blocks > 1:
            self.parallel_upload_blocks -= 1
            client.loop.create_task(upload_semaphore.acquire())
            
        try:
            # Reconnect to Telegram servers
            click.echo('Reconnecting to Telegram servers...')
            await asyncio.wait_for(client.connect(), RECONNECT_TIMEOUT)
            click.echo('Reconnected to Telegram servers.')
        except Exception:
            click.echo('InvalidBufferError connecting to Telegram servers.', err=True)
        except asyncio.TimeoutError:
            click.echo('Timeout connecting to Telegram servers.', err=True)
        finally:
            reconnecting_lock.release()
            
    def __progress(sent : int, total : int):
        """
        Callback function to show the upload progress
        
        Args:
            sent: The number of bytes sent
            total: The total number of bytes to send
        """
        print(f"Uploaded {sent / total * 100:.2f}%")
    
    
    
    
    # region Actions
    
    '''
    Actions region
    
    This region contains all the functions to execute actions (create folder, upload file, move, rename, delete, etc...)
    '''
    
    @classmethod
    async def get_root(self, client : TelegramManagerClient, chat_instance : Entity) -> FileMessage:
        """
        Get the root folder of the chat
        The root folder is the first pinned message in the chat
        
        Args:
            client: The telegram client to use
            chat_instance: The chat to get the root folder from
        Returns:
            FileMessage: The root folder message wrapped in a FileMessage object or None if not found
        """
        
        async for msg in client.iter_messages(chat_instance, filter=InputMessagesFilterPinned()):
            # Get the first pinned message
            return FileMessage(msg)
        
        return None
    
    @classmethod
    async def create_root(self, client : TelegramManagerClient, chat_instance : Entity) -> FileMessage:
        """
        Create the root folder in the chat
        
        Args:
            client: The telegram client to use
            chat_instance: The chat to create the root folder in
        Returns:
            FileMessage: The root folder message wrapped in a FileMessage object
        Raises:
            Exception: If the root folder creation fails
        """
        try:
            # Create the root folder message
            root_message = await self.__send_telegram_message(
                client, 
                chat_instance, 
                FileMessage.generate_json_caption(FileMessageType.ROOT, "ROOT"),
            )
            # Pin the root folder message
            await client.pin_message(chat_instance, root_message.telegram_message)
            # Return the root folder message
            return root_message
        except Exception as e:
            raise e
    
    @classmethod
    async def create_folder(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        folder_name : str, 
        parent_message : FileMessage
        ) -> FileMessage:
        """
        Create a new folder
        
        Args:
            client: The Telegram client
            chat_instance: The chat to create the folder in
            folder_name: The name of the new folder
            parent_message: The parent folder message
        Returns:
            FileMessage: The created folder message wrapped in a FileMessage object
        """
        # Request parent message update
        await parent_message.refresh(client, chat_instance)
        
        # Create the folder message
        data = FileMessage.generate_json_caption(FileMessageType.FOLDER, folder_name)
        # Set the parent
        data["Parent"] = FileMessage.calculate_message_link(chat_instance, parent_message)
        
        # Send the folder message
        folder_message = await self.__send_telegram_message(
            client, 
            chat_instance,
            data
        )
        
        # Update parent message children
        await parent_message.add_children(client, chat_instance, FileMessage.calculate_message_link(chat_instance, folder_message))
        
        # Return the created folder message
        return folder_message
    
    @classmethod
    async def upload_file(
        self, 
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
        message = await self.__send_telegram_message(
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
                await self.__create_video(client, chat_instance, Video(file), message)
            case _:
                # Upload generic file
                await self.__create_generic_file(client, chat_instance, file, message)
            
        # Update parent message children
        await parent_message.add_children(client, chat_instance, FileMessage.calculate_message_link(chat_instance, message))
        
        # Return the uploaded file message
        return message
    
    '''
    @classmethod
    async def move(
        self, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : FileMessage, 
        new_parent_message : FileMessage
        ):
        """
        Move a file or a folder

        Args:
            client (TelegramClient): _description_
            chat_instance (Entity): _description_
            message (Message): _description_
            new_parent_message (Message): _description_
        """
        # Update
        await message.refresh(client, chat_instance)
        await new_parent_message.refresh(client, chat_instance)
        
        # --------------------------------------------
        # Update the childrens of the old parent
        # --------------------------------------------
        
        json_message_data = json.loads(message.message)
        parent_message = await FileMessage.get_filemessage_from_link(client, json_message_data['Parent'])    
        await parent_message.remove_children(client, chat_instance, json_message_data['Parent'])
        
        # --------------------------------------------
        # Update the message parent
        # --------------------------------------------
        
        json_message_data['Parent'] = self.__calculate_message_link(chat_instance, new_parent_message)
        json_new_message = json.dumps(json_message_data, indent=4)
        await client.edit_message(chat_instance, message, json_new_message)
        
        # --------------------------------------------
        # Update the childrens of the new parent
        # --------------------------------------------
        
        await new_parent_message.add_children(client, chat_instance, self.__calculate_message_link(chat_instance, message))
    '''
    
    @classmethod
    async def rename(self, client : TelegramClient, chat_instance : Entity, message : FileMessage, new_name : str):
        """
        Rename a file or a folder
        
        Args:
            client: The Telegram client
            chat_instance: The chat instance
            message: The file or folder message to rename
            new_name: The new name for the file or folder
        """
        # Update
        await message.refresh(client, chat_instance)
        
        # Parse the message data
        json_message_data = json.loads(message.telegram_message.message)
        # Update the name
        json_message_data['Name'] = new_name
        # Generate the new message JSON
        json_new_message = json.dumps(json_message_data, indent=4)
        
        # Edit the message
        await client.edit_message(chat_instance, message.telegram_message, json_new_message)

    @classmethod
    async def delete(self, client : TelegramClient, chat_instance : Entity, message : FileMessage):
        """
        Delete a file or a folder
        
        Args:
            client: The Telegram client
            chat_instance: The chat instance
            message: The file or folder message to delete
        """
        # Update
        await message.refresh(client, chat_instance)
        
        # Parse the message data
        json_message_data = json.loads(message.telegram_message.message)
        # Calculate the message link
        deleted_message_link = FileMessage.calculate_message_link(chat_instance, message)
        
        # Check if file or folder
        match json_message_data['Type']:
            case FileMessageType.FOLDER.value:
                # Remove all the children
                for c in json_message_data["Children"]:
                    # Recursively delete children
                    await self.delete(client, chat_instance, await FileMessage.get_FileMessage_from_link(client, c))
                
                # Delete the folder message
                await client.delete_messages(chat_instance, message.telegram_message.id)
            case FileMessageType.FILE.value:
                # Delete the file message
                await client.delete_messages(chat_instance, message.telegram_message.id)
            case FileMessageType.ROOT.value:
                raise Exception("Cannot delete root folder")
            case FileMessageType.LRV.value:
                raise Exception("Cannot delete LRV file directly")
            case _:
                raise Exception("Not implemented")
        
        # Remove the message from the parent's children
        parent_message = await FileMessage.get_FileMessage_from_link(client, json_message_data['Parent'])
        await parent_message.remove_children(client, chat_instance, deleted_message_link)
    
    # endregion
    
    
    # region Upload
    '''
    Upload functions
    '''
    
    # region UploadVideo
    
    '''
    Video Region
    
    This region contains all the functions to execute actions on Video file
    '''
    
    @classmethod
    async def __create_video(self, client : TelegramManagerClient, chat_instance : Entity, file : Video, message : FileMessage):
        ### LRV
        
        # Generate the LRV video
        LRV_video = LRV.generate_video_low_resolution(file)
        
        # File caption for LRV
        file_caption_lrv = FileMessage.generate_json_caption(FileMessageType.LRV, file.file_name)
        
        # Post the LRV video
        await self.__process_normal_video(client, chat_instance, LRV_video, caption = file_caption_lrv, comment_to = message, force_document = False, supports_streaming = True)
        
        ### Original video
        
        # File caption for the original video
        file_caption = FileMessage.generate_json_caption(FileMessageType.FILE, file.file_name)
        
        # Check if the file size is bigger then the max allowed size for the user
        if file.size > client.max_file_size:
            # Process as large video
            await self.__process_large_video(client, chat_instance, file, caption = file_caption, comment_to = message)
        else:
            # Process as normal video
            await self.__process_normal_video(client, chat_instance, file, caption = file_caption, comment_to = message, force_document = True)
    
    @classmethod    
    async def __process_normal_video(
        self, 
        client : TelegramManagerClient, 
        chat_entity : Entity, 
        file: Video, 
        caption : str, 
        comment_to : FileMessage, 
        force_document = False, 
        supports_streaming : bool = False
        ):
        """
        File is normal file
        
        Args:
            client: Telegram manager client
            chat_entity: Chat entity to send the file to
            file: Video file to upload
            caption: Caption for the file
            comment_to: FileMessage to comment the file to
            force_document: Whether to force the file to be sent as a document
            supports_streaming: Whether the video supports streaming
        """
        
        # Add the part number
        caption["Part"] = 1
        
        # Get video details
        json_video_info = FFMPEG.get_ffprobe_file_details(file)
        # Convert caption to JSON string
        json_file_message = json.dumps(caption, indent=4)
        
        # Upload the file data
        # This is done before send the message with the file to have the file already uploaded when sending the message
        file = await self.__upload_file(client, file, file_output_size = file.size, file_output_path = file.path, progress_callback=self.__progress)
        
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

    @classmethod    
    async def __process_large_video(
        self, 
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
            splitted_file = await self.__upload_file(client, file, file_output_size = size, file_output_path = part_name, progress_callback=self.__progress)
            
            # Add the part to the caption
            caption["Part"] = part + 1
            # Convert caption to JSON string
            json_file_message = json.dumps(caption, indent=4)
            # Send the file
            await client.send_file(chat_entity, splitted_file, comment_to = comment_to.telegram_message, caption = json_file_message, force_document = True)
            # Get the next part
            file.seek(client.max_file_size * part, split_seek=True)
    
    # endregion
    
    # region UploadGenericFile
    
    @classmethod
    async def __create_generic_file(self, client : TelegramManagerClient, chat_instance : Entity, file : File, message : FileMessage):
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
        file = await self.__upload_file(client, file, file_output_size = file.size, file_output_path = file.path, progress_callback=self.__progress)
        # Send the file as a comment of the message
        await client.send_file(
            chat_instance, 
            file,
            # Add the file to the comment
            comment_to = message.telegram_message,
            caption = json_file_message, 
            force_document = True,
        )
        
    # endregion
    
    # region UploadUtils
    
    @classmethod
    async def __upload_file(
        self, 
        client: TelegramManagerClient, 
        file: File, 
        *,
        part_size_kb: float = None, 
        file_output_size: int = None,
        file_output_path: str = None,
        progress_callback: 'hints.ProgressCallback' = None
        ):
        """
        Upload a file to Telegram servers in parts
        
        All the information of this process can be found at:
        https://core.telegram.org/api/files
        
        Args:
            client: Telegram manager client
            file: File to upload
            part_size_kb: Size of each part in KB. If None, an appropriate size will be determined
            file_output_size: Total size of the file to upload. If None, the size will be determined from the file
            file_output_path: Path of the file to upload. If None, the file name will be used
            progress_callback: Callback to use to show upload progress. Optional.
        Returns:
            InputFile or InputFileBig: The uploaded file as an InputFile or InputFileBig
        Raises:
            ValueError: If the part size is greater than the maximum allowed size
            ValueError: If the part size is not evenly divisible by 1024
            ValueError: If PART_MAX_SIZE is not evenly divisible by the part size
            TypeError: If the file descriptor does not return bytes when read
            Exception: If the upload fails after the maximum number of retries
        """
        
        # Semaphore to limit the number of parallel uploads
        upload_semaphore = asyncio.Semaphore(PARALLEL_UPLOAD_BLOCKS)
        reconnecting_lock = asyncio.Lock()
        
        # Check if the file is already an InputFile
        if isinstance(file, (types.InputFile, types.InputFileBig)):
            return file  # Already uploaded
        
        # Open the file stream
        async with helpers._FileStream(file.path, file_size=file_output_size) as stream:
            # Determine the file size
            file_size = file_output_size
            
            # Check if part_size_kb is a valid value
            if not part_size_kb:
                part_size_kb = utils.get_appropriated_part_size(file_size)
                
            # Validate part size
            if part_size_kb > (PART_MAX_SIZE / 1024):
                raise ValueError('The part size must be less or equal to 512KB')
            
            # Calculate part size in bytes
            part_size = int(part_size_kb * 1024)
            if part_size % 1024 != 0:
                raise ValueError(
                    'The part size must be evenly divisible by 1024')
            
            # Validate that PART_MAX_SIZE is evenly divisible by part_size
            if PART_MAX_SIZE % part_size != 0:
                raise ValueError(
                    f'{PART_MAX_SIZE} must be evenly divisible by the part size')
            
            # Generate a file id
            file_id = helpers.generate_random_long()
            
            # Set a default file name if None was specified
            if not file_output_path:
                file_output_path = stream.name or str(file_id)

            # If the file name lacks extension, add it if possible.
            # Otherwise Telegram gives the error `PHOTO_EXT_INVALID_ERROR`
            # even if the uploaded image is indeed a photo.
            if not os.path.splitext(file_output_path)[-1]:
                file_output_path += utils._get_extension(stream)

            # Determine whether the file is too big (over 10MB) or not
            # Telegram does make a distinction between big and small files
            # when uploading them.
            is_big = file_size > SMALL_FILE_THRESHOLD
            hash_md5 = hashlib.md5()
            
            # Calculate the number of parts
            part_count = (file_size + part_size - 1) // part_size

            pos = 0
            # Loop every part
            for part_index in range(part_count):
                # Read the file in chunks of size part_size
                part = await helpers._maybe_await(stream.read(part_size))
                
                # Validate the read part
                if not isinstance(part, bytes):
                    raise TypeError(
                        'file descriptor returned {}, not bytes (you must '
                        'open the file in bytes mode)'.format(type(part)))

                # `file_size` could be wrong in which case `part` may not be
                # `part_size` before reaching the end.
                if len(part) != part_size and part_index < part_count - 1:
                    raise ValueError(
                        'read less than {} before reaching the end; either '
                        '`file_size` or `read` are wrong'.format(part_size))
                    
                # Update position
                pos += len(part)
                
                if not is_big:
                    # Bit odd that MD5 is only needed for small files and not
                    # big ones with more chance for corruption, but that's
                    # what Telegram wants.
                    hash_md5.update(part)

                # The SavePartRequest is different depending on whether
                # the file is too large or not (over or less than 10MB)
                if is_big:
                    request = functions.upload.SaveBigFilePartRequest(
                        file_id, part_index, part_count, part)
                else:
                    request = functions.upload.SaveFilePartRequest(
                        file_id, part_index, part)
                
                # Acquire the semaphore before starting the upload
                await upload_semaphore.acquire()
                client.loop.create_task(
                    self.__send_file_part(client, reconnecting_lock, upload_semaphore, request, part_index, part_count, pos, file_size, progress_callback),
                    name=f"telegram-upload-file-{part_index}"
                )
            # Wait for all tasks to finish
            await asyncio.wait([
                task for task in asyncio.all_tasks() if task.get_name().startswith(f"telegram-upload-file-")
            ])
        if is_big:
            return types.InputFileBig(file_id, part_count, file.file_name)
        else:
            return custom.InputSizedFile(
                file_id, part_count, file.file_name, md5=hash_md5, size=file_size
            )
    
    @classmethod  
    async def __send_file_part(
        self, 
        client : TelegramManagerClient, 
        reconnecting_lock : asyncio.Lock, 
        upload_semaphore : asyncio.Semaphore, 
        request: TLRequest, 
        part_index: int, 
        part_count: int, 
        pos: int, 
        file_size: int,
        progress_callback: Optional['hints.ProgressCallback'] = None, 
        retry: int = 0
        ) -> None:
        """
        Submit the file request part to Telegram. This method waits for the request to be executed, logs the upload,
        and releases the semaphore to allow further uploading.
        
        Args:
            client: Telegram manager client
            reconnecting_lock: A lock to prevent multiple reconnection at the same time
            upload_semaphore: A semaphore to limit the number of parallel uploads
            request: The TLRequest to send
            part_index: Index of the part being uploaded
            part_count: Total number of parts
            pos: Current position in the file
            file_size: Total size of the file
            progress_callback: Callback to use to show upload progress. Optional.
            retry: Current retry count
        Raises:
            RuntimeError: If the upload fails after the maximum number of retries
        """
        # Initialize result
        result = None
        try:
            # Send the request
            result = await client(request)
        except InvalidBufferError as e:
            if e.code == 429:
                # Too many connections
                click.echo('Too many connections to Telegram servers.', err=True)
            else:
                raise
        except ConnectionError:
            # Retry to send the file part
            click.echo('Detected connection error. Retrying...', err=True)
        else:
            # Successful upload
            upload_semaphore.release()

        # Check the result and retry if needed
        if result is None and retry < MAX_RECONNECT_RETRIES:
            # An error occurred, retry
            await asyncio.sleep(max(MIN_RECONNECT_WAIT, retry * MIN_RECONNECT_WAIT))
            await self.__reconnect()
            await self.__send_file_part(
                client, reconnecting_lock, upload_semaphore, request, part_index, part_count, pos, file_size, progress_callback, retry + 1
            )
        elif result:
            if progress_callback:
                await helpers._maybe_await(progress_callback(pos, file_size))
        else:
            raise RuntimeError(
                'Failed to upload file part {}.'.format(part_index))
    # endregion
    
    # endregion