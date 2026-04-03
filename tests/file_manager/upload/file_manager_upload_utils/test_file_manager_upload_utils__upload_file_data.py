import os
import sys

from file_manager.upload.file_manager_upload_utils import FileManager_Upload_Utils
from file_types.file import File
from file_types.video import Video
import pytest
from telethon import types

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_upload_utils__upload_file_data(TelegramManagerClient_init):
    """
    Test the upload_file_data method of FileManager_Upload_Utils with a small text file
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a File instance for the test file
        test_file = File("test_files/test_file.txt")
        
        # Upload the file data using FileManager_Upload_Utils
        uploaded_file_data = await FileManager_Upload_Utils.upload_file_data(client, test_file)
        
        # Check if the uploaded file data is correct
        assert isinstance(uploaded_file_data, types.InputFile), "Uploaded file data should be of type InputFile"
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()
    
    
@pytest.mark.asyncio
async def test_file_manager_upload_utils__upload_file_data__small_video(TelegramManagerClient_init):
    """
    Test the upload_file_data method of FileManager_Upload_Utils with a small video file
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a Video instance for the test video file
        test_file = Video(File("test_files/test_video.mp4"))
        
        # Upload the file data using FileManager_Upload_Utils
        uploaded_file_data = await FileManager_Upload_Utils.upload_file_data(client, test_file)
        
        assert isinstance(uploaded_file_data, types.InputFile), "Uploaded file data should be of type InputFile"
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()
    
    