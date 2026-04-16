import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

async def test_file_manager_main__download_file(monkeypatch, TelegramManagerClient_init):
    """
    Test the download_file method of FileManager
    """
    try:
        # Mock the directory selection to return a specific path for downloads
        monkeypatch.setattr('tkinter.filedialog.askdirectory', lambda title: os.path.abspath('test_files/downloads'))
        
        
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Create a test file to upload and then download
        test_file_path = File("test_files/test_file.txt")
        
        # Upload the test file to the root folder
        uploaded_file_message = await file_manager.upload_file(client, target_chat_instance, test_file_path, root_folder)
        
        # Download the uploaded file to a new location
        download_path = await file_manager.download_file(client, target_chat_instance, uploaded_file_message)
        
        # Check that the downloaded file exists and has the same content as the original test file
        assert os.path.exists(download_path), "The downloaded file does not exist"
        
        with open(test_file_path.path, 'r') as original_file:
            original_content = original_file.read()
            
        with open(download_path, 'r') as downloaded_file:
            downloaded_content = downloaded_file.read()
            
        assert original_content == downloaded_content, "The content of the downloaded file does not match the original file"
        
        # Clean up by removing the downloaded file
        os.remove(download_path)
        
    except Exception as e:
        raise e
    finally:
        await client.disconnect()