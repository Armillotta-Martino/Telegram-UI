import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_manager_main__create_root(TelegramManagerClient_init, delete_all_messages):
    """
    Test the create_root method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Delete all messages in the target chat to ensure a clean state for the test
        await delete_all_messages(client, target_chat_instance)
        
        # Create a root folder
        root_folder = await file_manager.create_root(client, target_chat_instance)
        
        # Check that the root folder is a TelegramMessage with type ROOT
        assert isinstance(root_folder, TelegramMessage), "The root folder is not a TelegramMessage instance"
        assert root_folder.type == TelegramMessageType.ROOT, "The root folder does not have type ROOT"
        
        # Check that the root folder has no parent
        with pytest.raises(ValueError):
            await root_folder.get_parent(client)
        
        # Check that the root folder has no children
        assert isinstance(await root_folder.get_children(client), list), "The children of the root folder should be a list"
        assert len(await root_folder.get_children(client)) == 0, "The children list of the root folder should be empty"
    except Exception as e:
        pytest.fail(f"An exception occurred during the test: {e}")
    finally:
        await client.disconnect()