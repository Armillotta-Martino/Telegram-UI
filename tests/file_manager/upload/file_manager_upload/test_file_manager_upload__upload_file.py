import os
import sys

from file_manager.file_manager_main import FileManager
from file_manager.upload.file_manager_upload import FileManager_Upload
from file_types.file import File
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessageType

@pytest.mark.asyncio
async def test_file_manager_upload__upload_file(TelegramManagerClient_init):
    """
    Test the upload_file method of FileManager_Upload
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a File instance for the test file
        test_file = File("test_files/test_file.txt")
        
        # Upload the file using FileManager_Upload
        file_message = await FileManager_Upload.upload_file(
            client,
            target_chat_instance,
            test_file,
            root_message)
        
        # Check if the file message was created successfully
        assert file_message is not None, "The file message was not created successfully"
        assert file_message.file_name == os.path.basename(test_file.name), "The file name in the file message does not match the uploaded file"
        
        file_part_message = (await file_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.FILE))[0]
        assert file_part_message.file_size == test_file.size, "The file size in the file message does not match the uploaded file"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()
    
    