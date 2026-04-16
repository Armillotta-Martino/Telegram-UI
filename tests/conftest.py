import json
import os
from xml.dom.minidom import Entity

from dbJson.telegram_message import TelegramMessage, TelegramMessageType
import pytest

from config import API_HASH, API_ID
import requests
from telegram.telegram_manager_client import TelegramManagerClient
from telethon.tl.types import InputMessagesFilterPinned, Message

CHANNEL_NAME = "Telegram-UI-Test-Channel"

@pytest.fixture(autouse=True)
def download_test_files():
    """
    Fixture to download test files before running tests
    This ensures that the necessary test files are available for the tests to run successfully
    """
    
    test_files = {
        "test_video.mp4": "https://iuawmxvsbadbzemjnmix.supabase.co/storage/v1/object/public/Telegram-UI-test-files/test_video.mp4",
        "test_image.jpg": "https://iuawmxvsbadbzemjnmix.supabase.co/storage/v1/object/public/Telegram-UI-test-files/test_image.jpg",
        "test_file.txt": "https://iuawmxvsbadbzemjnmix.supabase.co/storage/v1/object/public/Telegram-UI-test-files/test_file.txt",
        "test_file_no_extension": "https://iuawmxvsbadbzemjnmix.supabase.co/storage/v1/object/public/Telegram-UI-test-files/test_file_no_extension",
        ".hidden_file": "https://iuawmxvsbadbzemjnmix.supabase.co/storage/v1/object/public/Telegram-UI-test-files/.hidden_file",
    }

    os.makedirs("test_files", exist_ok=True)

    for filename, url in test_files.items():
        file_path = os.path.join("test_files", filename)
        if not os.path.exists(file_path):
            print(f"Downloading {filename}...")
            response = requests.get(url)
            with open(file_path, 'wb') as f:
                f.write(response.content)

@pytest.fixture
async def TelegramManagerClient_init() -> tuple[TelegramManagerClient, Entity]:
    """
    Init the connection with the Telegram API
    
    NOTE: THIS CLEAN UP ALL THE CHAT MESSAGES IN THE TARGET CHAT, SO USE IT ONLY WITH A TEST CHAT
    
    NOTE: This keeps only the pinned message, which is used as the root message for the tests as the pinned message has a timeout to be set if it is 
    set many times in a short period of time, so to avoid this issue, the pinned message is not deleted but only updated with the default root caption 
    if it is different from the default root caption
    Returns:
        tuple[TelegramManagerClient, Entity]: The TelegramManagerClient instance and the target chat instance
    """
    # Init variables for TelegramManagerClient
    client = TelegramManagerClient('Telegram-UI', API_ID, API_HASH)
    await client.start()
    await client.initialize()
    
    # This fetches all your chats and saves them to the session cache
    await client.get_dialogs()
        
    # Get the target chat instance
    target_chat_instance = await client.get_entity(CHANNEL_NAME)
    
    # Clean up the target chat messages before the test
    # TODO In the future i can implement a transaction system that allow every command to return a function to execute the rollback of the changes 
    # and to avoid deleting all the messages in the target chat, but for now this is the simplest solution to ensure a clean state for the tests
    await __TelegramManagerClient_reset(client, target_chat_instance)
    
    # Return the client and the target chat instance for use in the test
    return client, target_chat_instance

async def __TelegramManagerClient_reset(client : TelegramManagerClient, target_chat_instance : Entity):
    message_ids = []
    pinned_message : Message = None
    
    # Get the pinned message and save
    # NOTE: This is necessary because the pinned message has a timeout to be set if it is done many times
    # To avoid this issue, save the pinned message and delete all the other messages
    async for msg in client.iter_messages(target_chat_instance, filter=InputMessagesFilterPinned()):
            # Get the first pinned message
            pinned_message = msg
            break
        
    # Iterate through all messages
    async for message in client.iter_messages(target_chat_instance):
        if pinned_message is not None and message.id == pinned_message.id:
            continue  # Skip the pinned message
        
        # Add the message ID to the list for batch deletion
        message_ids.append(message.id)
        
        # Delete in batches of 100 (Telegram's common limit per request)
        if len(message_ids) >= 100:
            await client.delete_messages(target_chat_instance, message_ids, revoke=True)
            print(f"Deleted {len(message_ids)} messages...")
            message_ids = []

    # Delete any remaining messages
    if message_ids:
        await client.delete_messages(target_chat_instance, message_ids, revoke=True)
    
    # Clear the pinned message to be a default root message for the tests
    if pinned_message is not None:
        default_root_caption = json.dumps(TelegramMessage.generate_json_caption(TelegramMessageType.ROOT, "ROOT"), indent=4)
        
        # Update the pinned message with the default root caption if it is different from the default root caption
        # This check is necessary or Telegram API will return an error if the message is with the same caption
        if pinned_message.message != default_root_caption:
            await client.edit_message(target_chat_instance, pinned_message, default_root_caption)

@pytest.fixture
async def delete_all_messages() -> callable:
    """
    Return an async callable that deletes messages in the target chat

    Usage in tests:
        # delete everything (including pinned)
        delete_all_messages(client, target_chat_instance)

    Returns:
        Callable[[bool], Awaitable[None]]: Async function that performs deletion
    """
    
    async def _delete_all_messages(client: TelegramManagerClient, target_chat_instance: Entity):

        message_ids = []
        async for message in client.iter_messages(target_chat_instance):
            message_ids.append(message.id)

            if len(message_ids) >= 100:
                await client.delete_messages(target_chat_instance, message_ids, revoke=True)
                message_ids = []

        if message_ids:
            await client.delete_messages(target_chat_instance, message_ids, revoke=True)
            
    return _delete_all_messages