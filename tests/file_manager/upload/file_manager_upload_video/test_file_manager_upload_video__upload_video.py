import os
import sys

from file_manager.file_manager_main import FileManager
from file_manager.file_manager_utils import FileManager_Utils
from file_manager.upload.file_manager_upload_utils import FileManager_Upload_Utils
from file_manager.upload.file_manager_upload_video import FileManager_Upload_Video
from file_types.file import File
from file_types.video import Video
import pytest
from telegram.telegram_manager_client import TelegramManagerClient
from config import API_ID, API_HASH, CHANNEL_NAME
from telethon import types

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_manager_upload_video__upload_video(TelegramManagerClient_init):
    """
    Test the upload_video method of FileManager_Upload_Video with a small video file
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a Video instance for the test video file
        test_file = Video(File("test_files/test_video.mp4"))
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create the file message
        data = TelegramMessage.generate_json_caption(TelegramMessageType.FILE, test_file.file_name)
        # Set the parent
        data["Parent"] = TelegramMessage.calculate_message_link(target_chat_instance, root_message)
        # Send the file message
        message = await FileManager_Utils.send_telegram_message(
            client, 
            target_chat_instance, 
            data
        )
        
        # Upload the file data using FileManager_Upload_Video
        uploaded_file_data = await FileManager_Upload_Video.upload_video(client, target_chat_instance, test_file, message)
        
        assert isinstance(uploaded_file_data, types.Message), "The upload_video method should return a Message instance for small videos"
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()
        
@pytest.mark.asyncio
async def test_file_manager_upload_video__upload_video__to_root(TelegramManagerClient_init):
    """
    Test the upload_video method of FileManager_Upload_Video with a small video file to the root message
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a Video instance for the test video file
        test_file = Video(File("test_files/test_video.mp4"))
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        with pytest.raises(Exception) as exc_info:
            # Upload the file data using FileManager_Upload_Video
            await FileManager_Upload_Video.upload_video(client, target_chat_instance, test_file, root_message)
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()

'''  
@pytest.mark.asyncio
async def test_file_manager_upload_video__upload_video_large_video(TelegramManagerClient_init):
    """
    Test the upload_video method of FileManager_Upload_Video with a large video file
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a Video instance for the test video file
        test_file = Video(File("test_files/test_large_video.mp4"))
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Upload the file data using FileManager_Upload_Video
        uploaded_file_data = await FileManager_Upload_Video.upload_video(client, target_chat_instance, test_file, root_message)
        
        assert isinstance(uploaded_file_data, list), "The upload_video method should return a list of Message instances for large videos"
        assert all(isinstance(msg, types.Message) for msg in uploaded_file_data), "All elements in the returned list should be Message instances"
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()
'''