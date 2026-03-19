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
    
    @staticmethod
    async def download_file(
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : FileMessage,
        ) -> str:
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
    """
    async def _download_file_part(
            client: TelegramManagerClient, 
            input_location: 'hints.FileLike',
            file: 'hints.OutFileLike' = None,
            *,
            part_size_kb: float = None,
            file_size: int = None,
            progress_callback: 'hints.ProgressCallback' = None,
            dc_id: int = None,
            key: bytes = None,
            iv: bytes = None,
            msg_data: tuple = None) -> typing.Optional[bytes]:
        if not part_size_kb:
            if not file_size:
                part_size_kb = 64  # Reasonable default
            else:
                part_size_kb = utils.get_appropriated_part_size(file_size)

        part_size = int(part_size_kb * 1024)
        if part_size % MIN_CHUNK_SIZE != 0:
            raise ValueError(
                'The part size must be evenly divisible by 4096.')

        if isinstance(file, pathlib.Path):
            file = str(file.absolute())

        in_memory = file is None or file is bytes
        if in_memory:
            f = io.BytesIO()
        elif isinstance(file, str):
            # Ensure that we'll be able to download the media
            helpers.ensure_parent_dir_exists(file)
            f = open(file, 'wb')
        else:
            f = file

        try:
            # The speed of this code can be improved. 10 requests are made in parallel, but it waits for all 10 to
            # finish before launching another 10.
            for tasks in grouper(self._iter_download_chunk_tasks(input_location, part_size, dc_id, msg_data, file_size), PARALLEL_DOWNLOAD_BLOCKS):
                tasks = list(filter(bool, tasks))
                await asyncio.wait(tasks)
                chunk = b''.join(filter(bool, [task.result() for task in tasks]))
                if not chunk:
                    break
                if iv and key:
                    chunk = AES.decrypt_ige(chunk, key, iv)
                r = f.write(chunk)
                if inspect.isawaitable(r):
                    await r

                if progress_callback:
                    r = progress_callback(f.tell(), file_size)
                    if inspect.isawaitable(r):
                        await r

            # Not all IO objects have flush (see #1227)
            if callable(getattr(f, 'flush', None)):
                f.flush()

            if in_memory:
                return f.getvalue()
        finally:
            if isinstance(file, str) or in_memory:
                f.close()
                
    def _iter_download_chunk_tasks(self, input_location, part_size, dc_id, msg_data, file_size):
        for i in range(0, file_size, part_size):
            yield self.loop.create_task(
                anext(self._iter_download(input_location, offset=i, request_size=part_size, dc_id=dc_id,
                                          msg_data=msg_data))
            )
    """