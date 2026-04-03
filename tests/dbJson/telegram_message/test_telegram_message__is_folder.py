import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage

@pytest.mark.asyncio
async def test_file_message__is_folder(TelegramManagerClient_init):
    """
    Test the is_folder method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the is_folder method returns the correct value
    try:
        # Initialize the TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a folder message
        folder_message = await FileManager.create_folder(client, target_chat_instance, "Test Folder", root_message)
        
        # Assert that the is_folder method returns True for the folder message and False for the root message
        assert folder_message.is_folder == True, "TelegramMessage.is_folder returned False for a folder message"
        assert root_message.is_folder == True, "TelegramMessage.is_folder returned False for a root message"
    except Exception as e:
        pytest.fail(f"TelegramMessage.is_folder raised an exception for a valid TelegramMessage object: {e}")
    finally:
        await client.disconnect()
        
def test_file_message__is_folder__invalid_message():
    """
    Test the is_folder method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the is_folder method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).is_folder
        
def test_file_message__is_folder__non_file_message():
    """
    Test the is_folder method of TelegramMessage with a non-file message
    """
    # Create a TelegramMessage object with a non-file message and assert that the is_folder method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage("This is not a file message").is_folder