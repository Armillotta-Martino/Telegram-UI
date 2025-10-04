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

from config import MAX_RECONNECT_RETRIES, MIN_RECONNECT_WAIT, PARALLEL_UPLOAD_BLOCKS, RECONNECT_TIMEOUT
from dbJson.file_message import FileMessage, FileMessageType
from telegram.telegram_manager_client import TelegramManagerClient

from file_types.compression.FFMPEG import FFMPEG
from file_types.compression.LRV import LRV
from file_types.file import File
from file_types.video import Video

class FileManager():
    """
    Class to work with Telegram messages as files and folders
    """
    
    # region Utils
    async def __send_telegram_message(
        client : TelegramManagerClient, 
        target_chat_instance: Entity, 
        message_json : dict[str, any],
        ) -> FileMessage:
        """
            Function to send a message to Telegram
        """
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

        return FileMessage(telegram_message)

    def __calculate_message_link(
        chat : Entity, 
        message : FileMessage
        ) -> str:
        """
            Calculate the link to a message in a channel or group.

            Args:
                chat (Entity): _description_
                message (FileMessage): _description_

            Returns:
                _type_: _description_
        """
        if message == None or message.telegram_message == None:
            return ""
        
        if hasattr(chat, 'username') and chat.username:
            # Public channel/group
            link = f"https://t.me/{chat.username}/{message.telegram_message.id}"
        else:
            # Private channel/group
            
            # remove -100 prefix
            internal_id = str(chat.id).replace('-100', '')
            link = f"https://t.me/c/{internal_id}/{message.telegram_message.id}"
        
        return link

    async def __reconnect(
        self, 
        client : TelegramManagerClient, 
        reconnecting_lock : asyncio.Lock, 
        upload_semaphore : asyncio.Semaphore
        ):
        """
            Reconnects to Telegram servers
            This function is used to reconnect to Telegram servers when the connection is lost
            It uses a lock to prevent multiple reconnections at the same time
            
            Args:
                client (TelegramManagerClient): The Telegram client to reconnect
                reconnecting_lock (asyncio.Lock): A lock to prevent multiple reconnections at the same time
                upload_semaphore (asyncio.Semaphore): A semaphore to limit the number of parallel uploads
        """
        
        await reconnecting_lock.acquire()
        if client.is_connected():
            # Reconnected in another task
            reconnecting_lock.release()
            return
        
        # Decreases the upload semaphore by one
        if self.parallel_upload_blocks > 1:
            self.parallel_upload_blocks -= 1
            client.loop.create_task(upload_semaphore.acquire())
            
        try:
            click.echo('Reconnecting to Telegram servers...')
            await asyncio.wait_for(client.connect(), RECONNECT_TIMEOUT)
            click.echo('Reconnected to Telegram servers.')
        except Exception:
            click.echo('InvalidBufferError connecting to Telegram servers.', err=True)
        except asyncio.TimeoutError:
            click.echo('Timeout connecting to Telegram servers.', err=True)
        finally:
            reconnecting_lock.release()
            
    def __progress(
        sent : int, 
        total : int
        ):
        """
            Callback function to show the upload progress
        """
        print(f"Uploaded {sent / total * 100:.2f}%")
    #endregion
    
    # region Actions
    
    '''
    Actions region
    
    This region contains all the functions to execute actions (create folder, upload file, move, rename, delete, etc...)
    '''
    
    @classmethod
    async def get_root(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity
        ) -> FileMessage:
        """
            Get the root folder of the chat
            The root folder is the first pinned message in the chat

            Args:
                client (TelegramManagerClient): _description_
                chat_instance (Entity): _description_

            Returns:
                _type_: _description_
        """
        
        async for msg in client.iter_messages(chat_instance, filter=InputMessagesFilterPinned()):
            # Get the first pinned message
            return FileMessage(msg)
        return None
    
    @classmethod
    async def create_root(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity
        ) -> FileMessage:
        """
            Create the root folder in the chat

            Args:
                client (TelegramManagerClient): _description_
                chat_instance (Entity): _description_

            Returns:
                FileMessage: _description_
        """
        
        root_message = await self.__send_telegram_message(
            client, 
            chat_instance, 
            FileMessage.generate_json_caption(FileMessageType.ROOT, "ROOT"),
        )
        await client.pin_message(chat_instance, root_message.telegram_message)
        return root_message
    
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
            client (TelegramClient): _description_
            chat_instance (Entity): _description_
            folder_name (str): _description_
            parent_message (Message, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        await parent_message.refresh(client, chat_instance)
        
        data = FileMessage.generate_json_caption(FileMessageType.FOLDER, folder_name)
        data["Parent"] = self.__calculate_message_link(chat_instance, parent_message)
        
        folder_message = await self.__send_telegram_message(
            client, 
            chat_instance,
            data
        )
        
        # Update parent message children
        await parent_message.add_children(client, chat_instance, self.__calculate_message_link(chat_instance, folder_message))
            
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
        Create a new file

        Args:
            client (TelegramClient): _description_
            chat_instance (Entity): _description_
            file_name (str): _description_
            parent_message (Message, optional): _description_. Defaults to None.
            file_path (_type_, optional): _description_. Defaults to str.

        Raises:
            Exception: _description_

        Returns:
            _type_: _description_
        """
        
        if not parent_message:
            json_data = json.loads(parent_message.telegram_message.message)
            type_value = json_data.get("Type")
            
            if type_value != FileMessageType.FOLDER.value and type_value != FileMessageType.ROOT.value:
                raise Exception("The parent is not a folder")
        
            # Update
            await parent_message.refresh(client, chat_instance)
            
            
        data = FileMessage.generate_json_caption(FileMessageType.FILE, file.file_name)
        data["Parent"] = self.__calculate_message_link(chat_instance, parent_message)
        
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
    
        mime = file.get_mime()
        match(mime):
            case "video":
                await self.__create_video(client, chat_instance, Video(file), message)
            case _:
                await self.__create_generic_file(client, chat_instance, file, message)
            
        # Update parent message children
        await parent_message.add_children(client, chat_instance, self.__calculate_message_link(chat_instance, message))
        
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
    async def rename(
        self, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : FileMessage, 
        new_name : str
        ):
        """
        Rename a file or a folder

        Args:
            client (TelegramClient): _description_
            chat_instance (Entity): _description_
            message (Message): _description_
            new_name (str): _description_
        """
        # Update
        await message.refresh(client, chat_instance)
        
        json_message_data = json.loads(message.telegram_message.message)
        json_message_data['Name'] = new_name
        json_new_message = json.dumps(json_message_data, indent=4)
        await client.edit_message(chat_instance, message.telegram_message, json_new_message)

    @classmethod
    async def delete(
        self, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : FileMessage
        ):
        """
        Delete a file or a folder

        Args:
            client (TelegramClient): _description_
            chat_instance (Entity): _description_
            message (Message): _description_

        Raises:
            Exception: _description_
        """
        # Update
        await message.refresh(client, chat_instance)
        
        json_message_data = json.loads(message.telegram_message.message)
        deleted_message_link = self.__calculate_message_link(chat_instance, message)
        
        # Check if file or folder
        match json_message_data['Type']:
            case FileMessageType.FOLDER.value:
                # Remove all the childrens
                for c in json_message_data["Children"]:
                    await self.delete(client, chat_instance, await FileMessage.get_filemessage_from_link(client, c))
                
                await client.delete_messages(chat_instance, message.telegram_message.id)
            case FileMessageType.FILE.value:
                await client.delete_messages(chat_instance, message.telegram_message.id)
            case _:
                raise Exception("Not implemented")
        
        # Remove from the children of parent
        parent_message = await FileMessage.get_filemessage_from_link(client, json_message_data['Parent'])
        await parent_message.remove_children(client, chat_instance, deleted_message_link)
    
    # endregion
    
    
    # region Upload
    '''
    Upload functios
    '''
    
    # region UploadVideo
    
    '''
    Video Region
    
    This region contains all the functions to execute actions on Video file
    '''
    
    @classmethod
    async def __create_video(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : Video, 
        message : FileMessage
        ):
        # Generate the LRV video
        LRV_video = LRV.generate_video_low_resolution(file)

        # Post the video as a comment of the message
        await self.__process_normal_video(client, chat_instance, LRV_video, caption = LRV_file_caption, comment_to = message, force_document = False, supports_streaming = True)
        
        file_caption = {
            #"Parent": calculate_message_link(chat_instance, file_message),
        }
        # Check if the fiel size is bigger then the max allowed size for the user
        if file.size > client.max_file_size:
            await self.__process_large_video(client, chat_instance, file, caption = file_caption, comment_to = message)
        else:
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
        """
        # Add the part number
        caption["Part"] = 1
        
        json_video_info = FFMPEG.get_ffprobe_file_details(file)
        json_file_message = json.dumps(caption, indent=4)
        file = await self.__upload_file(client, file, file_output_size = file.size, file_output_path = file.path, progress_callback=self.__progress)
        await client.send_file(
            chat_entity, 
            file, 
            comment_to = comment_to, 
            caption = json_file_message, 
            force_document = force_document, 
            supports_streaming = supports_streaming,
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
        Override the process_large_file base function
        """
        # Calculate how many parts i need
        parts = math.ceil(file.size / client.max_file_size)
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
            json_file_message = json.dumps(caption, indent=4)
            # Send the file
            await client.send_file(chat_entity, splitted_file, comment_to = comment_to, caption = json_file_message, force_document = True)
            # Get the next part
            file.seek(client.max_file_size * part, split_seek=True)
    
    # endregion
    
        # region UploadGenericFile
    @classmethod
    async def __create_generic_file(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : File, 
        message : FileMessage
        ):
        
        # Upload the file data
        file = await self.__upload_file(client, file, file_output_size = file.size, file_output_path = file.path, progress_callback=self.__progress)
        # Send the file as a comment of the message
        await client.send_file(
            chat_instance, 
            file,
            # Add the image to the comment
            comment_to = message.telegram_message,
            # TODO
            caption = "", 
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
        
        upload_semaphore = asyncio.Semaphore(PARALLEL_UPLOAD_BLOCKS)
        reconnecting_lock = asyncio.Lock()
        
        if isinstance(file, (types.InputFile, types.InputFileBig)):
            return file  # Already uploaded
        
        async with helpers._FileStream(file.path, file_size=file_output_size) as stream:
            # Opening the stream will determine the correct file size
            file_size = file_output_size
            
            # Check if part_size_kb is a valid value
            if not part_size_kb:
                part_size_kb = utils.get_appropriated_part_size(file_size)

            if part_size_kb > 512:
                raise ValueError('The part size must be less or equal to 512KB')

            part_size = int(part_size_kb * 1024)
            if part_size % 1024 != 0:
                raise ValueError(
                    'The part size must be evenly divisible by 1024')

            if 524288 % part_size != 0:
                raise ValueError(
                    '524288 must be evenly divisible by the part size')
            
            # Generate a file id
            file_id = helpers.generate_random_long()
            
            # Set a default file name if None was specified
            if not file_output_path:
                file_output_path = stream.name or str(file_id)

            # If the file name lacks extension, add it if possible.
            # Else Telegram complains with `PHOTO_EXT_INVALID_ERROR`
            # even if the uploaded image is indeed a photo.
            if not os.path.splitext(file_output_path)[-1]:
                file_output_path += utils._get_extension(stream)

            # Determine whether the file is too big (over 10MB) or not
            # Telegram does make a distinction between smaller or larger files
            is_big = file_size > 10 * 1024 * 1024
            hash_md5 = hashlib.md5()

            part_count = (file_size + part_size - 1) // part_size
            #client._log[__name__].info('Uploading file of %d bytes in %d chunks of %d',
            #                         file_size, part_count, part_size)

            pos = 0
            for part_index in range(part_count):
                # Read the file by in chunks of size part_size
                part = await helpers._maybe_await(stream.read(part_size))

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

        :param request: SaveBigFilePartRequest or SaveFilePartRequest. This request will be awaited.
        :param part_index: Part index as integer. Used in logging.
        :param part_count: Total parts count as integer. Used in logging.
        :param pos: Number of part as integer. Used for progress bar.
        :param file_size: Total file size. Used for progress bar.
        :param progress_callback: Callback to use after submit the request. Optional.
        :return: None
        """
        result = None
        try:
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
            upload_semaphore.release()

        
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