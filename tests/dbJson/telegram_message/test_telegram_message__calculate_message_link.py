import os
import sys

from file_manager.file_manager_main import FileManager

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage

@pytest.mark.asyncio
async def test_telegram_message__calculate_message_link(TelegramManagerClient_init):
    """
    Test the calculate_message_link method of TelegramMessage with valid input
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Calculate the message link and assert that it is correct
        message_link = TelegramMessage.calculate_message_link(target_chat_instance, root_message)
        
        assert message_link == f"https://t.me/c/{target_chat_instance.id}/{root_message.telegram_message.id}", "The calculated message link is not correct"
        
    except Exception as e:
        raise e
    finally:
        # Disconnect the client after the test
        await client.disconnect()
    
@pytest.mark.asyncio
async def test_telegram_message__calculate_message_link__invalid(TelegramManagerClient_init):
    """
    Test the calculate_message_link method of TelegramMessage with invalid input
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Calculate the message link with invalid input and assert that it raises a ValueError
        with pytest.raises(ValueError):
            TelegramMessage.calculate_message_link("Invalid Chat Instance", root_message)
        
        with pytest.raises(ValueError):
            TelegramMessage.calculate_message_link(target_chat_instance, "Invalid Message Instance")
            
    except Exception as e:
        raise e
    finally:
        # Disconnect the client after the test
        await client.disconnect()
        
@pytest.mark.asyncio
async def test_telegram_message__calculate_message_link__empty_message(TelegramManagerClient_init):
    """
    Test the calculate_message_link method of TelegramMessage with an empty message
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create an empty message instance
        class EmptyMessage:
            message_id = 12345
        
        empty_message = EmptyMessage()
        
        # Calculate the message link with the empty message and assert that it raises a ValueError
        with pytest.raises(ValueError):
            TelegramMessage.calculate_message_link(target_chat_instance, empty_message)
        
    except Exception as e:
        raise e
    finally:
        # Disconnect the client after the test
        await client.disconnect()