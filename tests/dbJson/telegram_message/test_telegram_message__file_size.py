import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
from file_types.video import Video
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_telegram_message__file_size(TelegramManagerClient_init):
    """
    Test the file_size method of TelegramMessage with a valid message
    """
    # Create a TelegramMessage object with a valid file path and assert that the file_size method returns the correct value
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a File object with a test file
        file = File("test_files/test_file.txt")
        # Upload a file to the target chat instance to create a new file message
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Get the child file of the file message
        children = await file_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.FILE)
        
        assert len(children) == 1, f"Expected 1 child file message, but got {len(children)}"
        child_file_message = children[0]
        
        assert child_file_message.file_size == file.size, f"TelegramMessage.file_size() returned {child_file_message.file_size} instead of {file.size} for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:        
        await client.disconnect()
        
@pytest.mark.asyncio
async def test_telegram_message__file_size__video(TelegramManagerClient_init):
    """
    Test the file_size method of TelegramMessage with a valid video message
    """
    # Create a TelegramMessage object with a valid file path and assert that the file_size method returns the correct value
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a File object with a test file
        file = Video(File("test_files/test_video.mp4"))
        # Upload the video file to the target chat instance to create a new file message
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Get the child file of the file message
        children = await file_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.FILE)
        
        assert len(children) == 1, f"Expected 1 child file message, but got {len(children)}"
        child_file_message = children[0]
        
        assert child_file_message.file_size == file.size, f"TelegramMessage.file_size() returned {child_file_message.file_size} instead of {file.size} for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:        
        await client.disconnect()
        
def test_telegram_message__file_size__invalid_message():
    """
    Test the file_size method of TelegramMessage with an invalid message
    """
    # Create a TelegramMessage object with an invalid message and assert that the file_size method raises an exception
    with pytest.raises(ValueError, match="Invalid message type"):
        TelegramMessage(None).file_size
