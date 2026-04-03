import os
import sys

from file_manager.file_manager_main import FileManager
from file_manager.file_manager_utils import FileManager_Utils
from file_types.file import File
from file_types.video import Video
import pytest
from telegram.telegram_manager_client import TelegramManagerClient
from config import API_ID, API_HASH, CHANNEL_NAME

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_message__get_comments_by_type(TelegramManagerClient_init):
    """
    Test the get_comments_by_type method of TelegramMessage with valid input
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
            
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Upload a video file
        file = Video(File('test_files/test_video.mp4'))
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Get the comments of type FILE for the file message
        comments = await file_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.FILE)
        
        assert len(comments) == 1, "There should be one comment of type FILE"
        assert comments[0].file_name == file_message.file_name, "The comment's file name should match the file message's file name"
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_comments_by_type() raised an exception for valid input: {e}")
    finally:
        await client.disconnect()
    
@pytest.mark.asyncio
async def test_file_message__get_comments_by_type__invalid():
    """
    Test the get_comments_by_type method of TelegramMessage with invalid input
    """
    # Create a dummy TelegramMessage instance (not connected to Telegram)
    telegram_message = TelegramMessage.__new__(TelegramMessage)  # Bypass __init__
    
    # Attempt to get comments by type without a valid Telegram client or chat instance
    with pytest.raises(Exception):
        await telegram_message.get_comments_by_type(None, None, TelegramMessageType.FILE)
        
@pytest.mark.asyncio
async def test_file_message__get_comments_by_type__no_comments(TelegramManagerClient_init):
    """
    Test the get_comments_by_type method of TelegramMessage when there are no comments of the specified type
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
            
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Attempt to get comments of a type that does not exist (e.g., FILE if no FILE comments were added)
        comments = await root_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.FILE)
        
        assert len(comments) == 0, "There should be no comments of type FILE"
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_comments_by_type() raised an exception when there are no comments of the specified type: {e}")
    finally:
        await client.disconnect()
    
@pytest.mark.asyncio
async def test_file_message__get_comments_by_type__invalid_type(TelegramManagerClient_init):
    """
    Test the get_comments_by_type method of TelegramMessage with an invalid comment type
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
            
        # Get the target chat instance
        target_chat_instance = await client.get_entity(CHANNEL_NAME)
            
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Attempt to get comments with an invalid type (e.g., a string that is not in TelegramMessageType)
        with pytest.raises(ValueError):
            comments = await root_message.get_comments_by_type(client, target_chat_instance, "INVALID_TYPE")
    except Exception as e:
        pytest.fail(f"TelegramMessage.get_comments_by_type() raised an unexpected exception for invalid comment type: {e}")
    finally:
        await client.disconnect()