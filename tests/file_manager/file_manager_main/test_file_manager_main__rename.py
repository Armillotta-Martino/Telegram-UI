import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_main__rename__folder(TelegramManagerClient_init):
    """
    Test the rename method of FileManager with a folder
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Create a subfolder under the root folder
        subfolder = await file_manager.create_folder(client, target_chat_instance, "Test Subfolder", root_folder)
        
        # Rename the subfolder
        await file_manager.rename(client, target_chat_instance, subfolder, "Renamed Subfolder")
        
        # Check that the subfolder has the new name
        assert subfolder.file_name == "Renamed Subfolder", "The subfolder was not renamed correctly"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()
    
@pytest.mark.asyncio
async def test_file_manager_main__rename__file(TelegramManagerClient_init):
    """
    Test the rename method of FileManager with a file
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Upload a file under the root folder
        file = File("test_files/test_file.txt")
        file_message = await file_manager.upload_file(client, target_chat_instance, file, root_folder)
        
        # Rename the file
        await file_manager.rename(client, target_chat_instance, file_message, "Renamed File")
        
        # Check that the file has the new name
        assert file_message.file_name == "Renamed File", "The file was not renamed correctly"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()