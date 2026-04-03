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
async def test_file_message__get_children(TelegramManagerClient_init):
    """
    Test the get_children method of TelegramMessage with a valid message
    """
    # Create a TelegramMessage object with a valid file path and assert that the get_children method returns the correct value
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
        
        # Get the children messages of the folder message
        children_messages = await folder_message.get_children(client)
        
        # Assert that the get_children method returns the correct child message
        assert children_messages is not None, "TelegramMessage.get_children() returned None for a valid TelegramMessage object"
        assert len(children_messages) == 1, f"TelegramMessage.get_children() returned {len(children_messages)} children messages instead of 1 for a valid TelegramMessage object"
        assert children_messages[0].telegram_message.id == file_message.telegram_message.id, f"TelegramMessage.get_children() returned a different child message than expected for a valid TelegramMessage object"
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_children() raised an exception for a valid TelegramMessage object: {e}")
    finally:
        await client.disconnect()
        
def test_file_message__get_children_invalid_message():
    """
    Test the get_children method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the get_children method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).get_children()
        
@pytest.mark.asyncio
async def test_file_message__get_children_no_children(TelegramManagerClient_init):
    """
    Test the get_children method of TelegramMessage when there are no children messages
    """
    # Create a TelegramMessage object with a valid file path and assert that the get_children method returns an empty list when there are no children messages
    try:
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Get the children messages of the root message (which should have no children)
        children_messages = await root_message.get_children(client)
        
        # Assert that the get_children method returns an empty list
        assert children_messages is not None, "TelegramMessage.get_children() returned None for a valid TelegramMessage object with no children"
        assert len(children_messages) == 0, f"TelegramMessage.get_children() returned {len(children_messages)} children messages instead of 0 for a valid TelegramMessage object with no children"
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_children() raised an exception for a valid TelegramMessage object with no children: {e}")
    finally:
        await client.disconnect()