import asyncio
from enum import Enum
import json
import os
import sys
import tempfile
import threading
import http.server
import socketserver
import webbrowser
import urllib.parse
import mimetypes
import time
import socket
import subprocess
from tkinter import Tk
from typing import Generator, Dict, Optional, Set
from xml.dom.minidom import Entity

from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPinned

from dbJson.file_message import FileMessage, FileMessageType
from file_manager.download.file_manager_download import FileManager_Download
from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload import FileManager_Upload
from file_types.file import File
from telegram.telegram_manager_client import TelegramManagerClient

class FileManager():
    
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
    async def create_root(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity
        ) -> FileMessage:
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
            root_message = await FileManager_Utils.send_telegram_message(
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
        folder_message = await FileManager_Utils.send_telegram_message(
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
        Upload a new file
        
        Args:
            client: The Telegram client
            chat_instance: The chat to upload the file in
            file: The file to upload
            parent_message: The parent folder message
        Returns:
            FileMessage: The created folder message wrapped in a FileMessage object
        """
        return await FileManager_Upload.upload_file(
            client,
            chat_instance,
            file,
            parent_message
        )
        
    @classmethod
    async def download_file(
        self, 
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        file : FileMessage,
        ) -> str:
        """
        Download a new file
        
        Args:
            client: The Telegram client
            chat_instance: The chat to download the file in
            file: The FileMessage to download
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
        # Remove the children from the old parent
        # --------------------------------------------
        
        json_message_data = json.loads(message.telegram_message.message)
        parent_message = await FileMessage.get_FileMessage_from_link(client, json_message_data['Parent'])    
        await parent_message.remove_children(client, chat_instance, FileMessage.calculate_message_link(chat_instance, message))
        
        # --------------------------------------------
        # Update the parent in the message
        # --------------------------------------------
        
        json_message_data['Parent'] = FileMessage.calculate_message_link(chat_instance, new_parent_message)
        json_new_message = json.dumps(json_message_data, indent=4)
        await client.edit_message(chat_instance, message.telegram_message, json_new_message)
        
        # --------------------------------------------
        # Add the children to the new parent
        # --------------------------------------------
        
        await new_parent_message.add_children(client, chat_instance, FileMessage.calculate_message_link(chat_instance, message))
    
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
    async def open_preview(
        self, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : FileMessage
        ):
        """
        Open a preview of a file or a folder
        
        Args:
            client: The Telegram client
            chat_instance: The chat instance
            message: The file or folder message to preview
        """
        # Update
        await message.refresh(client, chat_instance)
        
        # Display the video preview on the pop up panel
        
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(chat_instance, reply_to=message.telegram_message.id):
            
            # Find the file message
            json_message = json.loads(message.message)
            
            if json_message.get("Part") is not None and json_message.get("Part") == FileMessageType.LRV.value:
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
        self, 
        client : TelegramClient, 
        chat_instance : Entity, 
        message : FileMessage
        ):
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
    
    @classmethod
    async def sync(
        self, 
        client : TelegramClient, 
        chat_instance : Entity, 
        folder : str,
        current_position : FileMessage
        ):
        """
        Delete a file or a folder
        
        Args:
            client: The Telegram client
            chat_instance: The chat instance
            message: The file or folder message to delete
        """
        
        class SyncState(Enum):
            NEW = "new"
            IN_PROGRESS = "in_progress"
            PAUSED = "paused"
            STOPPED = "stopped"
            FINISHED = "finished"
            
        async def scan_dir(path: str, current_position: FileMessage, sync_job: dict):
            """
                Recursively explore the folder and sync it with Telegram
            
            :param path: Description
            :type path: str
            :param current_position: Description
            :type current_position: FileMessage
            :param sync_job: Description
            :type sync_job: dict
            """    
            # Recursive explore the folder
            with os.scandir(path) as it:
                for entry in it:
                    
                    # Check if the current file or folder has already been synced in the sync job
                    if await is_executed_sync_job(sync_job, entry.path):
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
                            await update_sync_job(sync_job, entry.path)
                            
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
                            await update_sync_job(sync_job, entry.path)
                            
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
                            await update_sync_job(sync_job, entry.path)
                            
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
                            await update_sync_job(sync_job, entry.path)
        
        async def save_sync_job(pc_path: str, telegram_link: str):
            """
            Save the pc path and Telegram path of the current folder in a json file to save the sync jobs

            Args:
                pc_path (str): The path of the folder on the PC
                telegram_path (str): The path of the folder on Telegram
            """
            
            # Init the sync jobs list
            sync_jobs = []
            
            # If the json file does not exist, create it with an empty list of sync jobs
            if not os.path.exists("sync_jobs.json"):
                with open("sync_jobs.json", "w") as f:
                    json.dump(sync_jobs, f, indent=4)
            
            # Check if the sync jobs already exists
            with open("sync_jobs.json", "r") as f:
                try:
                    sync_jobs = json.load(f)
                except json.JSONDecodeError:
                    sync_jobs = []
                    
                for job in sync_jobs:
                    if job["pc_path"] == pc_path and job["telegram_link"] == telegram_link:
                        # Sync job already exists, do not save it again
                        return
            
            # Create the new sync job
            sync_job = {
                "pc_path": pc_path,
                "telegram_link": telegram_link,
                "state": SyncState.NEW.value,
                "synced_files": []
            }
            # Append the new sync job to the list of sync jobs
            sync_jobs.append(sync_job)
            
            # Save the sync jobs in the json file
            with open("sync_jobs.json", "w") as f:
                json.dump(sync_jobs, f, indent=4)
        
        async def update_sync_job(sync_job: Dict, synced_file: str):
            """
            Update the sync job with the new synced file

            Args:
                sync_job (Dict): The sync job to update
                telegram_link (str): The link of the folder on Telegram
                synced_file (str): The name of the file that has been synced
            """
            # Load the sync jobs from the json file
            with open("sync_jobs.json", "r") as f:
                sync_jobs = json.load(f)
                
                # Find the sync job to update
                for job in sync_jobs:
                    if job["pc_path"] == sync_job["pc_path"] and job["telegram_link"] == sync_job["telegram_link"]:
                        # Sync job found, update it
                        if synced_file not in job["synced_files"]:
                            # Update the sync job with the new synced file
                            job["synced_files"].append(synced_file)
                            sync_job["synced_files"].append(synced_file)
                        break
            
            # Save the updated sync jobs in the json file
            with open("sync_jobs.json", "w") as f:
                json.dump(sync_jobs, f, indent=4)
        
        async def get_sync_job(pc_path: str, telegram_link: str) -> Optional[Dict]:
            """
            Get the sync job for the given pc path and telegram path

            Args:
                pc_path (str): The path of the folder on the PC
                telegram_link (str): The link of the folder on Telegram
            Returns:
                Optional[Dict]: The sync job if found, None otherwise
            """
            # Load the sync jobs from the json file
            with open("sync_jobs.json", "r") as f:
                sync_jobs = json.load(f)
                
                # Find the sync job
                for job in sync_jobs:
                    if job["pc_path"] == pc_path and job["telegram_link"] == telegram_link:
                        return job
            
            return None
        
        async def is_executed_sync_job(sync_job: Dict, pc_file_path: str) -> bool:
            """
            Check if the given file has already been synced in the sync job

            Args:
                sync_job (Dict): The sync job to check
                pc_file_path (str): The path of the file on the PC to check
            Returns:
                bool: True if the file has already been synced, False otherwise
            """
            return pc_file_path in sync_job["synced_files"]
        
        async def update_sync_job_state(sync_job: Dict, new_state: SyncState):
            """
            Update the state of the sync job

            Args:
                sync_job (Dict): The sync job to update
                new_state (SyncState): The new state of the sync job
            """
            # Load the sync jobs from the json file
            with open("sync_jobs.json", "r") as f:
                sync_jobs = json.load(f)
                
                # Find the sync job to update
                for job in sync_jobs:
                    if job["pc_path"] == sync_job["pc_path"] and job["telegram_link"] == sync_job["telegram_link"]:
                        # Sync job found, update its state
                        job["state"] = new_state.value
                        break
            
            # Save the updated sync jobs in the json file
            with open("sync_jobs.json", "w") as f:
                json.dump(sync_jobs, f, indent=4)
        
        # Update
        await current_position.refresh(client, chat_instance)
        
        # Save the sync job
        await save_sync_job(folder, FileMessage.calculate_message_link(chat_instance, current_position))
        
        # Get the sync job
        sync_job = await get_sync_job(folder, FileMessage.calculate_message_link(chat_instance, current_position))
        
        # Update the sync job state to in_progress
        await update_sync_job_state(sync_job, SyncState.IN_PROGRESS)
        
        # Check if the current folder has already been synced (this is useful to avoid syncing the 
        # same folder multiple times in case of nested folders with the same name)
        if not await is_executed_sync_job(sync_job, folder):
            # Get the children of the current position with the same name as the folder to sync
            children_by_file_name = await current_position.get_children_by_file_name(client, os.path.basename(folder))
            
            # If a child with the same name as the folder to sync already exists, move into it; otherwise, create the folder and move into it
            if (children_by_file_name is not None) and (len(children_by_file_name) > 0):
                # Folder already exists, move into it
                current_position = await FileMessage.get_FileMessage_from_link(client, FileMessage.calculate_message_link(chat_instance, children_by_file_name[0]))
            else:
                # Create the root folder
                parent_folder = await FileManager.create_folder(
                    client,
                    chat_instance,
                    os.path.basename(folder),
                    current_position
                )
                
                # Move the current position to the new folder
                current_position = await FileMessage.get_FileMessage_from_link(client, FileMessage.calculate_message_link(chat_instance, parent_folder))
        
        # Update the sync job with the new Telegram path of the current position
        await update_sync_job(sync_job, folder)
        
        # Scan the folder
        await scan_dir(folder, current_position, sync_job)
        
        # Update the sync job state to finished
        await update_sync_job_state(sync_job, SyncState.FINISHED)