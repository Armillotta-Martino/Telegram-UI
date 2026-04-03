import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_message__short_name(TelegramManagerClient_init):
    """
    Test the short_name method of TelegramMessage with a valid message
    """
    # Create a TelegramMessage object with a valid file path and assert that the short_name method returns the correct value
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a File object with a test file
        file = File("test_files/test_file.txt")
        # Upload a file to the target chat instance to create a new TelegramMessage
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        assert file_message.short_name == "test_file", f"TelegramMessage.short_name returned {file_message.short_name} instead of 'test_file' for a valid TelegramMessage object"
    except Exception as e:
        pytest.fail(f"TelegramMessage.short_name raised an exception for a valid TelegramMessage object: {e}")
    finally:
        await client.disconnect()
        
def test_file_message__short_name__invalid_message():
    """
    Test the short_name method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the short_name method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).short_name
        
