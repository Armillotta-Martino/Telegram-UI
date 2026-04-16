import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_manager_main__get_root(TelegramManagerClient_init):
    """
    Test the get_root method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
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
       raise e
    finally:
        await client.disconnect()

@pytest.mark.asyncio
async def test_file_manager_main__get_root_invalid(TelegramManagerClient_init):
    """
    Test the get_root method of FileManager with an invalid chat instance
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
            
        # Get the root folder with an invalid chat instance
        with pytest.raises(ValueError):
            await file_manager.get_root(client, None)
        
    except Exception as e:
        raise e
    finally:
        await client.disconnect()