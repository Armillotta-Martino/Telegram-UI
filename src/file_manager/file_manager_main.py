import asyncio
from enum import Enum
import json
import os
import sys
import tempfile
import threading
import subprocess
from typing import Dict, Optional
from xml.dom.minidom import Entity

# Telethon imports
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPinned

# Import DbJson
from dbJson.telegram_message import TelegramMessage, TelegramMessageType

from file_manager.download.file_manager_download import FileManager_Download
from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload import FileManager_Upload
from telegram.telegram_manager_client import TelegramManagerClient

# Import File types
from file_types.file import File

class FileManager():
    """
    FileManager is the main class that handles the file management operations in the Telegram chat. 
    It provides methods to create folders, upload files, download files, move files and folders, 
    rename files and folders, open file previews, delete files and folders, and sync a local folder 
    with a Telegram folder
    """
    
    @classmethod
    async def get_root(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity
        ) -> TelegramMessage:
        """
        Get the root folder of the chat
        The root folder is the first pinned message in the chat
        
        Args:
            client (TelegramManagerClient): The telegram client to use
            chat_instance (Entity): The chat to get the root folder from
        Returns:
            TelegramMessage: The root folder message wrapped in a TelegramMessage object or None if not found
        """
        
        if not TelegramMessage._TelegramMessage__valid_chat_entity(chat_instance):
            raise ValueError("Invalid chat entity")
        
        async for msg in client.iter_messages(chat_instance, filter=InputMessagesFilterPinned()):
            # Get the first pinned message
            return TelegramMessage(msg)
        
        # Root not initialized. Create the root message and pin it
        return await cls.create_root(client, chat_instance)
    
    @classmethod
    async def create_root(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity
        ) -> TelegramMessage:
        """
        Create the root folder in the chat
        
        Args:
            client (TelegramManagerClient): The telegram client to use
            chat_instance (Entity): The chat to create the root folder in
        Returns:
            TelegramMessage: The root folder message wrapped in a TelegramMessage object
        Raises:
            Exception: If the root folder creation fails
        """
        try:
            # Create the root folder message
            root_message = await FileManager_Utils.send_telegram_message(
                client, 
                chat_instance, 
                TelegramMessage.generate_json_caption(TelegramMessageType.ROOT, "ROOT"),
            )
            # Pin the root folder message
            await client.pin_message(chat_instance, root_message.telegram_message)
            # Return the root folder message
            return root_message
        except Exception as e:
            raise e
    
    @classmethod
    async def create_folder(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        folder_name : str, 
        parent_message : TelegramMessage
        ) -> TelegramMessage:
        """
        Create a new folder
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat to create the folder in
            folder_name (str): The name of the new folder
            parent_message (TelegramMessage): The parent folder message
        Returns:
            TelegramMessage: The created folder message wrapped in a TelegramMessage object
        """
        # Request parent message update
        await parent_message.refresh(client, chat_instance)
        
        # Create the folder message
        data = TelegramMessage.generate_json_caption(TelegramMessageType.FOLDER, folder_name)
        # Set the parent
        data["Parent"] = TelegramMessage.calculate_message_link(chat_instance, parent_message)
        
        # Send the folder message
        folder_message = await FileManager_Utils.send_telegram_message(
            client, 
            chat_instance,
            data
        )
        
        # Update parent message children
        await parent_message.add_children(client, chat_instance, TelegramMessage.calculate_message_link(chat_instance, folder_message))
        
        # Return the created folder message
        return folder_message
    
    @classmethod
    async def upload_file(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : File, 
        parent_message : TelegramMessage
        ) -> TelegramMessage:
        """
        Upload a new file
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat to upload the file in
            file (File): The file to upload
            parent_message (TelegramMessage): The parent folder message
        Returns:
            TelegramMessage: The created folder message wrapped in a TelegramMessage object
        """
        return await FileManager_Upload.upload_file(
            client,
            chat_instance,
            file,
            parent_message
        )
    
    @classmethod
    async def download_file(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : TelegramMessage,
        ) -> str:
        """
        Download a new file
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat to download the file in
            file (TelegramMessage): The TelegramMessage to download
        Returns:
            str: The download location of the file
        """
        return await FileManager_Download.download_file(
            client,
            chat_instance,
            file,
        )
    
    @classmethod
    async def move(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        message : TelegramMessage, 
        new_parent_message : TelegramMessage
        ) -> None:
        """
        Move a file or a folder

        Args:
            client (TelegramManagerClient): The Telegram client to use
            chat_instance (Entity): The chat instance to use
            message (TelegramMessage): The message to move
            new_parent_message (TelegramMessage): The new parent message to move the message into
        Returns:
            None
        """
        
        # Validate the chat instance
        if not TelegramMessage._TelegramMessage__valid_chat_entity(chat_instance):
            raise ValueError("Invalid chat entity")
        
        # Validate the message
        if not TelegramMessage._TelegramMessage__valid_message(message):
            raise ValueError("Invalid message entity")
        
        # Validate the new parent message
        if not TelegramMessage._TelegramMessage__valid_message(new_parent_message):
            raise ValueError("Invalid new parent message entity")
        
        # Validate that the message is not being moved into itself
        if message.telegram_message.id == new_parent_message.telegram_message.id:
            raise Exception("Cannot move a message into itself")
        
        # Update
        await message.refresh(client, chat_instance)
        await new_parent_message.refresh(client, chat_instance)
        
        # --------------------------------------------
        # Remove the children from the old parent
        # --------------------------------------------
        
        json_message_data = json.loads(message.telegram_message.message)
        parent_message = await TelegramMessage.get_TelegramMessage_from_link(client, json_message_data['Parent'])    
        await parent_message.remove_children(client, chat_instance, TelegramMessage.calculate_message_link(chat_instance, message))
        
        # --------------------------------------------
        # Update the parent in the message
        # --------------------------------------------
        
        json_message_data['Parent'] = TelegramMessage.calculate_message_link(chat_instance, new_parent_message)
        json_new_message = json.dumps(json_message_data, indent=4)
        await client.edit_message(chat_instance, message.telegram_message, json_new_message)
        
        # --------------------------------------------
        # Add the children to the new parent
        # --------------------------------------------
        
        await new_parent_message.add_children(client, chat_instance, TelegramMessage.calculate_message_link(chat_instance, message))
        
        # Refresh the message and the new parent message to ensure the changes are reflected
        await message.refresh(client, chat_instance)
        await new_parent_message.refresh(client, chat_instance)
    
    @classmethod
    async def rename(
        cls, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        message : TelegramMessage, 
        new_name : str
        ) -> None:
        """
        Rename a file or a folder
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat instance
            message (TelegramMessage): The file or folder message to rename
            new_name (str): The new name for the file or folder
        Returns:
            None
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
        
        # Refresh the message to ensure the changes are reflected
        await message.refresh(client, chat_instance)
    
    @classmethod
    async def open_preview(
        cls, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : TelegramMessage
        ) -> None:
        """
        Open a preview of a file or a folder
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat instance
            message (TelegramMessage): The file or folder message to preview
        Returns:
            None
        """
        # Update
        await message.refresh(client, chat_instance)
        
        # Display the video preview on the pop up panel
        
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(chat_instance, reply_to=message.telegram_message.id):
            
            # Find the file message
            json_message = json.loads(message.message)
            
            if json_message.get("Type") is not None and json_message.get("Type") == TelegramMessageType.LRV.value:
                # create temp file path
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tmp_path = tmp.name
                tmp.close()

                # start background download (do not await)
                download_task = asyncio.create_task(client.download_media(message, file=tmp_path))

                # wait for a small initial buffer (timeout to avoid infinite wait)
                initial_threshold = 100 * 1024  # 100 KB
                waited = 0
                timeout = 10  # seconds
                while waited < timeout:
                    try:
                        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) >= initial_threshold:
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.25)
                    waited += 0.25

                # open with VLC if available, otherwise fallback to default opener
                try:
                    proc = None

                    if sys.platform == 'win32':
                        # Use PowerShell Start-Process -Wait to reliably wait for the launched app to exit
                        try:
                            cmd = f'Start-Process -FilePath "{tmp_path}" -Wait'
                            proc = subprocess.Popen(['powershell', '-NoProfile', '-Command', cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception:
                            # fallback to startfile (no waiting)
                            try:
                                os.startfile(tmp_path)
                                proc = None
                            except Exception:
                                proc = None
                    else:
                        # prefer vlc for progressive playback and wait on it
                        try:
                            proc = subprocess.Popen(['vlc', tmp_path, '--play-and-exit'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except FileNotFoundError:
                            if sys.platform == 'darwin':
                                # macOS: open with -W to wait until app closes
                                proc = subprocess.Popen(['open', '-W', tmp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                # Linux: xdg-open returns immediately; spawn it anyway and fall back to timed cleanup
                                try:
                                    proc = subprocess.Popen(['xdg-open', tmp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                except Exception:
                                    proc = None

                    def _wait_and_cleanup(p, path, download_task_ref, loop_ref):
                        try:
                            if p is not None:
                                p.wait()
                        except Exception:
                            pass

                        # Cancel the download task on the event loop if it's still running
                        try:
                            async def _cancel_and_wait(t):
                                try:
                                    if not t.done():
                                        t.cancel()
                                        try:
                                            await t
                                        except asyncio.CancelledError:
                                            pass
                                except Exception:
                                    pass

                            try:
                                # schedule cancellation on the original event loop
                                fut = asyncio.run_coroutine_threadsafe(_cancel_and_wait(download_task_ref), loop_ref)
                                # wait briefly for cancellation to complete
                                try:
                                    fut.result(timeout=5)
                                except Exception:
                                    pass
                            except Exception:
                                # fallback: attempt to call cancel() directly
                                try:
                                    download_task_ref.cancel()
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        # remove the temporary file
                        try:
                            if os.path.exists(path):
                                os.remove(path)
                        except Exception:
                            pass

                    # Capture running loop and start a thread to wait for player exit and then cleanup
                    try:
                        loop_ref = asyncio.get_running_loop()
                    except Exception:
                        loop_ref = None

                    cleanup_thread = threading.Thread(target=_wait_and_cleanup, args=(proc, tmp_path, download_task, loop_ref), daemon=True)
                    cleanup_thread.start()
                except Exception as e:
                    print('Failed to open player:', e)
    
    @classmethod
    async def delete(
        cls, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : TelegramMessage
        ) -> None:
        """
        Delete a file or a folder
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat instance
            message (TelegramMessage): The file or folder message to delete
        Returns:
            None
        """
        # Update
        await message.refresh(client, chat_instance)
        
        # Parse the message data
        json_message_data = json.loads(message.telegram_message.message)
        # Calculate the message link
        deleted_message_link = TelegramMessage.calculate_message_link(chat_instance, message)
        
        # Check if file or folder
        match json_message_data['Type']:
            case TelegramMessageType.FOLDER.value:
                # Remove all the children
                for c in json_message_data["Children"]:
                    # Recursively delete children
                    await cls.delete(client, chat_instance, await TelegramMessage.get_TelegramMessage_from_link(client, c))
                
                # Delete the folder message
                await client.delete_messages(chat_instance, message.telegram_message.id)
            case TelegramMessageType.FILE.value:
                # Delete the file message
                await client.delete_messages(chat_instance, message.telegram_message.id)
            case TelegramMessageType.ROOT.value:
                raise Exception("Cannot delete root folder")
            case TelegramMessageType.LRV.value:
                raise Exception("Cannot delete LRV file directly")
            case _:
                raise Exception("Not implemented")
        
        # Remove the message from the parent's children
        parent_message = await TelegramMessage.get_TelegramMessage_from_link(client, json_message_data['Parent'])
        await parent_message.remove_children(client, chat_instance, deleted_message_link)
        
        # Refresh the message to ensure it's deleted
        await message.refresh(client, chat_instance)
    
    class SyncState(Enum):
        NEW = "new"
        IN_PROGRESS = "in_progress"
        PAUSED = "paused"
        STOPPED = "stopped"
        FINISHED = "finished"

    @staticmethod
    async def _save_sync_job(pc_path: str, telegram_link: str) -> None:
        sync_jobs = []
        if not os.path.exists("sync_jobs.json"):
            with open("sync_jobs.json", "w") as f:
                json.dump(sync_jobs, f, indent=4)

        with open("sync_jobs.json", "r") as f:
            try:
                sync_jobs = json.load(f)
            except json.JSONDecodeError:
                sync_jobs = []

            for job in sync_jobs:
                if job["pc_path"] == pc_path and job["telegram_link"] == telegram_link:
                    return

        sync_job = {
            "pc_path": pc_path,
            "telegram_link": telegram_link,
            "state": FileManager.SyncState.NEW.value,
            "synced_files": []
        }
        sync_jobs.append(sync_job)

        with open("sync_jobs.json", "w") as f:
            json.dump(sync_jobs, f, indent=4)

    @staticmethod
    async def _update_sync_job(sync_job: Dict, synced_file: str) -> None:
        with open("sync_jobs.json", "r") as f:
            sync_jobs = json.load(f)

            for job in sync_jobs:
                if job["pc_path"] == sync_job["pc_path"] and job["telegram_link"] == sync_job["telegram_link"]:
                    if synced_file not in job["synced_files"]:
                        job["synced_files"].append(synced_file)
                        sync_job["synced_files"].append(synced_file)
                    break

        with open("sync_jobs.json", "w") as f:
            json.dump(sync_jobs, f, indent=4)

    @staticmethod
    async def _get_sync_job(pc_path: str, telegram_link: str) -> Optional[Dict]:
        with open("sync_jobs.json", "r") as f:
            sync_jobs = json.load(f)
            for job in sync_jobs:
                if job["pc_path"] == pc_path and job["telegram_link"] == telegram_link:
                    return job
        return None

    @staticmethod
    async def _is_executed_sync_job(sync_job: Dict, pc_file_path: str) -> bool:
        return pc_file_path in sync_job["synced_files"]

    @staticmethod
    async def _update_sync_job_state(sync_job: Dict, new_state: 'FileManager.SyncState') -> None:
        with open("sync_jobs.json", "r") as f:
            sync_jobs = json.load(f)

            for job in sync_jobs:
                if job["pc_path"] == sync_job["pc_path"] and job["telegram_link"] == sync_job["telegram_link"]:
                    job["state"] = new_state.value
                    break

        with open("sync_jobs.json", "w") as f:
            json.dump(sync_jobs, f, indent=4)

    @classmethod
    async def sync(
        cls, 
        client : TelegramClient, 
        chat_instance : Entity, 
        folder : str,
        current_position : TelegramMessage
        ) -> None:
        """
        Sync a folder with Telegram
        
        Args:
            client (TelegramManagerClient): The Telegram client
            chat_instance (Entity): The chat instance
            folder (str): The folder path to sync
            current_position (TelegramMessage): The current position in the Telegram folder structure
        Returns:
            None
        """
        
        async def scan_dir(path: str, current_position: TelegramMessage, sync_job: dict) -> None:
            """
            Recursively explore the folder and sync it with Telegram
            
            Args:
                path (str): The path of the folder to sync
                current_position (TelegramMessage): The current position in the Telegram folder structure
                sync_job (dict): The sync job to update with the synced files
            """    
            # Recursive explore the folder
            with os.scandir(path) as it:
                for entry in it:
                    
                    # Check if the current file or folder has already been synced in the sync job
                    if await cls._is_executed_sync_job(sync_job, entry.path):
                        # File or folder already synced, skip
                        print(f"File or folder already synced, skipping: {entry.path}")
                        continue
                    
                    # Check if entry is a directory or a file (avoid following symlinks)
                    is_dir = entry.is_dir(follow_symlinks=False)
                    
                    if is_dir:
                        ## Folder
                        
                        # Get the children of the current position with the same name as the folder to sync
                        children_by_file_name = await current_position.get_children_by_file_name(client, os.path.basename(entry.path))
                        
                        # If a child with the same name as the folder to sync already exists, move into it; otherwise, create the folder and move into it
                        if (children_by_file_name is not None) and (len(children_by_file_name) > 0):
                            # Update the sync job with the executed folder
                            await cls._update_sync_job(sync_job, entry.path)
                            
                            # Recurse into directory (avoid following symlinks)
                            await scan_dir(entry.path, children_by_file_name[0], sync_job)
                        else:
                            # Create folder
                            new_folder = await FileManager.create_folder(
                                client,
                                chat_instance,
                                os.path.basename(entry.path),
                                current_position
                            )
                            
                            # Update the sync job with the executed folder
                            await cls._update_sync_job(sync_job, entry.path)
                            
                            # Recurse into directory (avoid following symlinks)
                            await scan_dir(entry.path, new_folder, sync_job)
                    else:
                        ## File
                        
                        # Construct File object; skip files that are invalid (e.g. empty)
                        try:
                            file = File(entry.path)
                        except ValueError as e:
                            # Common case: empty file -> skip
                            print(f"Skipping file (invalid): {entry.path} -> {e}")
                            continue
                        except PermissionError as e:
                            print(f"Skipping file (permission denied): {entry.path} -> {e}")
                            continue
                        except OSError as e:
                            print(f"Skipping file (os error): {entry.path} -> {e}")
                            continue
                        
                        # Get the children of the current position with the same name as the file to sync
                        children_by_file_name = await current_position.get_children_by_file_name(client, os.path.basename(file.file_name))
                        
                        # If a child with the same name as the file to sync already exists, move into it; otherwise, upload the file
                        if (children_by_file_name is not None) and (len(children_by_file_name) > 0):
                            # Update the sync job with the executed folder
                            await cls._update_sync_job(sync_job, entry.path)
                            
                            # File already exists, skip
                            print(f"File already exists, skipping: {entry.path}")
                        else:
                            # Upload file
                            file = await FileManager.upload_file(
                                client,
                                chat_instance,
                                file,
                                current_position
                            )
                            
                            # Update the sync job with the executed folder
                            await cls._update_sync_job(sync_job, entry.path)
        
        # The sync helper functions are implemented as class-level async methods
        # so they can be monkeypatched in tests.
        
        # Update
        await current_position.refresh(client, chat_instance)
        
        # Save the current position to update it at the end of the sync
        saved_current_position = current_position

        # Save the sync job
        await cls._save_sync_job(folder, TelegramMessage.calculate_message_link(chat_instance, current_position))

        # Get the sync job
        sync_job = await cls._get_sync_job(folder, TelegramMessage.calculate_message_link(chat_instance, current_position))

        # Update the sync job state to in_progress
        await cls._update_sync_job_state(sync_job, cls.SyncState.IN_PROGRESS)

        # Check if the current folder has already been synced (this is useful to avoid syncing the 
        # same folder multiple times in case of nested folders with the same name)
        if not await cls._is_executed_sync_job(sync_job, folder):
            # Get the children of the current position with the same name as the folder to sync
            children_by_file_name = await current_position.get_children_by_file_name(client, os.path.basename(folder))
            
            # If a child with the same name as the folder to sync already exists, move into it; otherwise, create the folder and move into it
            if (children_by_file_name is not None) and (len(children_by_file_name) > 0):
                # Folder already exists, move into it
                current_position = await TelegramMessage.get_TelegramMessage_from_link(client, TelegramMessage.calculate_message_link(chat_instance, children_by_file_name[0]))
            else:
                # Create the root folder
                parent_folder = await FileManager.create_folder(
                    client,
                    chat_instance,
                    os.path.basename(folder),
                    current_position
                )
                
                # Move the current position to the new folder
                current_position = await TelegramMessage.get_TelegramMessage_from_link(client, TelegramMessage.calculate_message_link(chat_instance, parent_folder))
        
        # Update the sync job with the new Telegram path of the current position
        await cls._update_sync_job(sync_job, folder)
        
        # Scan the folder
        await scan_dir(folder, current_position, sync_job)
        
        # Update the sync job state to finished
        await cls._update_sync_job_state(sync_job, cls.SyncState.FINISHED)
        
        # Refresh the saved current position to ensure all changes are reflected
        await saved_current_position.refresh(client, chat_instance)