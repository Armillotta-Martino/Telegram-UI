import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_main__delete(TelegramManagerClient_init):
    """
    Test the delete method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Create a child folder under the root folder
        child_folder = await file_manager.create_folder(client, target_chat_instance, "Child Folder", root_folder)
        
        # Delete the child folder
        await file_manager.delete(client, target_chat_instance, child_folder)
        
        # Check that the child folder is deleted and no longer exists in the database
        with pytest.raises(ValueError):
            await child_folder.get_parent(client)
    except Exception as e:
        pytest.fail(f"Unexpected exception occurred: {e}")
    finally:
        await client.disconnect()