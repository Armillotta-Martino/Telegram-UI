import os
import sys

from file_manager.file_manager_main import FileManager
from telethon.tl.custom.message import Message
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage

@pytest.mark.asyncio
async def test_telegram_message__constructor(TelegramManagerClient_init):
    """
    Test the constructor of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that it is created successfully
    try:
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        file_message = await FileManager.get_root(client, target_chat_instance)
        # Assert that the TelegramMessage object is created successfully
        assert file_message is not None, "TelegramMessage constructor returned None for a valid file path"
    except Exception as e:
        pytest.fail(f"TelegramMessage constructor raised an exception for a valid file path: {e}")
    finally:        
        await client.disconnect()
        
def test_telegram_message__constructor__invalid_path():
    """
    Test the constructor of TelegramMessage with an invalid file path
    """
    # Attempt to create a TelegramMessage object with an invalid file path and assert that an exception is raised
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None)
        
def test_telegram_message__constructor__non_file_message():
    """
    Test the constructor of TelegramMessage with a non-file message
    """
    # Attempt to create a TelegramMessage object with a non-file message and assert that an exception is raised
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage("This is not a file message")
        
def test_telegram_message__constructor__empty_message():
    """
    Test the constructor of TelegramMessage with an empty message
    """
    # Attempt to create a TelegramMessage object with an empty message and assert that an exception is raised
    with pytest.raises(ValueError, match="Message is empty or has no text"):
        TelegramMessage(Message(0, None, message=""))

def test_telegram_message__constructor__invalid_message_type():
    """
    Test the constructor of TelegramMessage without a message type
    """
    message = Message(0, None, message='{}')
    
    # Attempt to create a TelegramMessage object with an invalid message type and assert that an exception is raised
    with pytest.raises(ValueError, match="Message does not contain Type"):
        TelegramMessage(message)