import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage

@pytest.mark.asyncio
async def test_telegram_message__extension(TelegramManagerClient_init):
    """
    Test the extension method of TelegramMessage with a valid message
    """
    # Create a TelegramMessage object with a valid file path and assert that the extension method returns the correct value
    try:
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a File object with a test file
        file = File("test_files/test_file.txt")
        # Upload a file to the target chat instance to create a new file message
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        assert file_message.extension == "txt", f"TelegramMessage.extension() returned {file_message.extension} instead of 'txt' for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:        
        await client.disconnect()
        
def test_telegram_message__extension_invalid_message():
    """
    Test the extension method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the extension method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).extension