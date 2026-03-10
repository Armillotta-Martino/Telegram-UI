import asyncio
import hashlib
import os
import click

from typing import Optional, Callable, Union

from config import MAX_RECONNECT_RETRIES, MIN_RECONNECT_WAIT, PARALLEL_UPLOAD_BLOCKS, PART_MAX_SIZE, SMALL_FILE_THRESHOLD
from file_manager.file_manager_utils import FileManager_Utils
from file_types.file import File
from telegram.telegram_manager_client import TelegramManagerClient

from telethon import utils, helpers, custom, hints
from telethon.errors import InvalidBufferError
from telethon.tl import types, TLRequest, functions


class FileManager_Upload_Utils:

    @staticmethod
    async def upload_file_data(
        client: TelegramManagerClient, 
        file: File, 
        *,
        part_size_kb: float = None, 
        file_output_size: int = None,
        file_output_path: str = None,
        progress_callback: Optional['hints.ProgressCallback'] = None
        ):
        """
        Upload a file data to Telegram servers in parts
        
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
                raise ValueError('The part size must be evenly divisible by 1024')
            
            # Validate that PART_MAX_SIZE is evenly divisible by part_size
            if PART_MAX_SIZE % part_size != 0:
                raise ValueError(f'{PART_MAX_SIZE} must be evenly divisible by the part size')
            
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
                        file_id, 
                        part_index, 
                        part_count, 
                        part
                        )
                else:
                    request = functions.upload.SaveFilePartRequest(
                        file_id, 
                        part_index, 
                        part
                        )
                
                # Acquire the semaphore before starting the upload
                await upload_semaphore.acquire()
                client.loop.create_task(
                    FileManager_Upload_Utils.__upload_file_part(
                        client, 
                        reconnecting_lock, 
                        upload_semaphore, 
                        request, 
                        part_index, 
                        part_count, 
                        pos, 
                        file_size, 
                        progress_callback
                        ),
                    name=f"telegram-upload-file-{part_index}"
                )
            # Wait for all tasks to finish
            await asyncio.wait([
                task for task in asyncio.all_tasks() if task.get_name().startswith(f"telegram-upload-file-")
            ])
        
        # Return the appropriate InputFile type
        if is_big:
            return types.InputFileBig(
                file_id, 
                part_count, 
                file.file_name
                )
        else:
            return custom.InputSizedFile(
                file_id, 
                part_count, 
                file.file_name, 
                md5=hash_md5, 
                size=file_size
            )
    
    @staticmethod  
    async def __upload_file_part(
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
            await FileManager_Utils.reconnect(client, reconnecting_lock, upload_semaphore)
            await FileManager_Upload_Utils.__upload_file_part(
                client, 
                reconnecting_lock, 
                upload_semaphore, 
                request, 
                part_index, 
                part_count, 
                pos, 
                file_size, 
                progress_callback, 
                retry + 1
            )
        elif result:
            if progress_callback:
                await helpers._maybe_await(
                    progress_callback(pos, file_size)
                    )
        else:
            raise RuntimeError(
                'Failed to upload file part {}.'.format(part_index))