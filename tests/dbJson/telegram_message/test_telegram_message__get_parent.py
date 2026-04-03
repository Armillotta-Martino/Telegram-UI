import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
from file_types.video import Video
import pytest
from telegram.telegram_manager_client import TelegramManagerClient
from config import API_ID, API_HASH, CHANNEL_NAME

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_message__get_parent(TelegramManagerClient_init):
    """
    Test the get_parent method of TelegramMessage with a valid message
    """
    # Create a TelegramMessage object with a valid file path and assert that the get_parent method returns the correct value
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a folder message
        folder_message = await FileManager.create_folder(client, target_chat_instance, "Test Folder", root_message)
        
        # Create a File object with a test file
        file = File("test_files/test_file.txt")
        # Upload a file to the target chat instance to create a new file message
        file_message = await FileManager.upload_file(client, target_chat_instance, file, folder_message)
        
        parent_message = await file_message.get_parent(client)
        
        assert parent_message is not None, "TelegramMessage.get_parent() returned None for a valid TelegramMessage object"
        assert parent_message.telegram_message.id == folder_message.telegram_message.id, f"TelegramMessage.get_parent() returned a different parent message than expected for a valid TelegramMessage object"
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_parent() raised an exception for a valid TelegramMessage object: {e}")
    finally:
        await client.disconnect()
        
def test_file_message__get_parent__invalid_message():
    """
    Test the get_parent method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the get_parent method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).get_parent()
