import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_manager_main__create_folder(TelegramManagerClient_init):
    """
    Test the create_folder method of FileManager
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
        
        # Check that the subfolder is a TelegramMessage with type FOLDER
        assert isinstance(subfolder, TelegramMessage), "The subfolder is not a TelegramMessage instance"
        assert subfolder.type == TelegramMessageType.FOLDER, "The subfolder does not have type FOLDER"
        
        # Check that the subfolder has the correct parent and an empty children list
        assert (await subfolder.get_parent(client)).telegram_message.id == root_folder.telegram_message.id, "The parent of the subfolder is not the root folder"
        assert isinstance(await subfolder.get_children(client), list), "The children of the subfolder should be a list"
        assert len(await subfolder.get_children(client)) == 0, "The children list of the subfolder should be empty"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()