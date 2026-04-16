import os
import sys

from file_manager.file_manager_main import FileManager
from file_manager.file_manager_utils import FileManager_Utils

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_message__refresh(TelegramManagerClient_init):
    """
    Test the refresh method of TelegramMessage with valid input
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
            
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create the folder message
        data = TelegramMessage.generate_json_caption(TelegramMessageType.FOLDER, "Test Folder")
        # Set the parent
        data["Parent"] = TelegramMessage.calculate_message_link(target_chat_instance, root_message)
            
        # Send the folder message
        folder_message = await FileManager_Utils.send_telegram_message(
            client, 
            target_chat_instance,
            data
        )
        
        # Add the child to the parent and assert that it is added successfully
        await root_message.add_children(client, target_chat_instance, TelegramMessage.calculate_message_link(target_chat_instance, folder_message))
        
        # Refresh the root message to get the updated children
        await root_message.refresh(client, target_chat_instance)
        
        assert len(await root_message.get_children(client)) == 1, "Child was not added to the parent TelegramMessage"
        assert (await root_message.get_children(client))[0].file_name == folder_message.file_name, "The added child is not the same as the expected child"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()