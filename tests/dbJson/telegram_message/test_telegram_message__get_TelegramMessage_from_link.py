import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage

@pytest.mark.asyncio
async def test_telegram_message__get_TelegramMessage_from_link(TelegramManagerClient_init):
    """
    Test the get_TelegramMessage_from_link method of TelegramMessage with a valid link
    """
    try:
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Calculate the link for the root message
        link = TelegramMessage.calculate_message_link(target_chat_instance, root_message)
        
        # Attempt to get the TelegramMessage from the valid link
        result = await root_message.get_TelegramMessage_from_link(client, link)
        
        assert result is not None, "The result should not be None for a valid link"
        assert isinstance(result, TelegramMessage), "The result should be an instance of TelegramMessage"
        assert result.telegram_message.id == root_message.telegram_message.id, "The TelegramMessage ID should match the root message ID"
    except Exception as e:
        pytest.fail(f"Unexpected exception occurred: {e}")
    finally:
        await client.disconnect()