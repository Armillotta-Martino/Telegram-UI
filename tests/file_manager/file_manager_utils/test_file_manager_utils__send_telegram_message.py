import os
import sys

from dbJson.telegram_message import TelegramMessage, TelegramMessageType
from file_manager.file_manager_utils import FileManager_Utils
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_utils__send_telegram_message(TelegramManagerClient_init):
    """
    Test the send_telegram_message function of FileManager_Utils by sending a test message to the Telegram channel
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Send a test message using the utility function
        json_message = TelegramMessage.generate_json_caption(TelegramMessageType.ROOT, "File name")
        await FileManager_Utils.send_telegram_message(client, target_chat_instance, json_message)
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()
        
@pytest.mark.asyncio
async def test_file_manager_utils__send_telegram_message__invalid_json(TelegramManagerClient_init):
    """
    Test the send_telegram_message function of FileManager_Utils with invalid JSON input
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Send a test message using the utility function
        test_message = "This is a test message from the FileManager_Utils test suite."
        
        with pytest.raises(TypeError):
            await FileManager_Utils.send_telegram_message(client, target_chat_instance, test_message)
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()