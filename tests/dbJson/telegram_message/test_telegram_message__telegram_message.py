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
async def test_file_message__telegram_message(TelegramManagerClient_init):
    """
    Test the telegram_message method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the telegram_message method returns the correct message
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root TelegramMessage
        telegram_message = await FileManager.get_root(client, target_chat_instance)
        # Assert that the telegram_message method returns the correct message
        assert telegram_message.telegram_message is not None, "TelegramMessage.telegram_message returned None for a valid TelegramMessage object"
    except Exception as e:
        pytest.fail(f"TelegramMessage.telegram_message raised an exception for a valid TelegramMessage object: {e}")
    finally:
        await client.disconnect()