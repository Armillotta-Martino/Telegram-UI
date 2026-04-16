import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

async def test_file_manager_main__move(TelegramManagerClient_init):
    """
    Test the move method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Create a subfolder under the root folder
        subfolder_1 = await file_manager.create_folder(client, target_chat_instance, "Test Subfolder 1", root_folder)
        
        # Create a subfolder under the root folder
        subfolder_2 = await file_manager.create_folder(client, target_chat_instance, "Test Subfolder 2", root_folder)
        
        # Move the subfolder_1 to subfolder_2
        await file_manager.move(client, target_chat_instance, subfolder_1, subfolder_2)
        
        # Assert that the parent of subfolder_1 is now subfolder_2
        assert (await subfolder_1.get_parent(client)).telegram_message.id == subfolder_2.telegram_message.id, "Subfolder 1 was not moved under Subfolder 2"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()
    
async def test_file_manager_main__move__to_none(TelegramManagerClient_init):
    """
    Test the move method of FileManager by moving a folder to None
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
        
        # Check if raised an error as a folder cannot be moved to None
        with pytest.raises(ValueError):
            await file_manager.move(client, target_chat_instance, subfolder, None)
    except Exception as e:
        raise e
    finally:
        await client.disconnect()
    