import os
import sys

from file_manager.file_manager_main import FileManager

from file_types.file import File
from file_types.video import Video
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_download__download_file(monkeypatch, TelegramManagerClient_init):
    """
    Test the download_file method of FileManager with a video file
    """
    try:
        # Mock the directory selection to return a specific path for downloads
        monkeypatch.setattr('tkinter.filedialog.askdirectory', lambda title: os.path.abspath('test_files/downloads'))
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Upload a video file to Telegram
        video_file_manager = await FileManager.upload_file(client, target_chat_instance, Video(File('test_files/test_video.mp4')), root_message)
        
        # Download the video file
        downloaded_file_path = await FileManager.download_file(client, target_chat_instance, video_file_manager)
        
        # Create a File instance for the downloaded file
        downloaded_file = File(downloaded_file_path)
        
        # Check if the downloaded file exists
        assert os.path.exists(downloaded_file.path), "The downloaded file does not exist"
        
        # Check if the downloaded file is a video
        assert downloaded_file.get_mime() == 'video', "The downloaded file is not a video"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()

@pytest.mark.asyncio
async def test_file_manager_download__download_file__file(monkeypatch, TelegramManagerClient_init):
    """
    Test the download_file method of FileManager with a file
    """
    try:
        # Mock the directory selection to return a specific path for downloads
        monkeypatch.setattr('tkinter.filedialog.askdirectory', lambda title: os.path.abspath('test_files/downloads'))
        
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Upload a non-video file to Telegram
        non_video_file_manager = await FileManager.upload_file(client, target_chat_instance, File('test_files/test_file.txt'), root_message)
        
        # Download the non-video file
        downloaded_file_path = await FileManager.download_file(client, target_chat_instance, non_video_file_manager)
        
        # Create a File instance for the downloaded file
        downloaded_file = File(downloaded_file_path)
        
        # Check if the downloaded file exists
        assert os.path.exists(downloaded_file.path), "The downloaded file does not exist"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()