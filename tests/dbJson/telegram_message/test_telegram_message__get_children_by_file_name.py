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
async def test_file_message__get_children_by_file_name(TelegramManagerClient_init):
    """
    Test the get_children_by_file_name method of TelegramMessage with an invalid file name
    """
    # Create a TelegramMessage object with a valid file path and assert that the get_children_by_file_name method raises an exception when an invalid file name is provided
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
        
        children = await folder_message.get_children(client)
        if not children or len(children) == 0:
            pytest.fail("TelegramMessage.get_children() returned an empty list after uploading a file to the folder message")
        
        # Attempt to get the child message by an invalid file name and assert that an exception is raised
        children_by_name = await folder_message.get_children_by_file_name(client, "test_file.txt")
        
        if len(children_by_name) == 0:
            pytest.fail("TelegramMessage.get_children_by_file_name() did not return the expected child message for a valid file name")
    
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_children_by_file_name() raised an exception for a valid TelegramMessage object: {e}")
    finally:        
        await client.disconnect()
        
def test_file_message__get_children_by_file_name__invalid_message():
    """
    Test the get_children_by_file_name method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the get_children_by_file_name method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).get_children_by_file_name("test_file.txt")