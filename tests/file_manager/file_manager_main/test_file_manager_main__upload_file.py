import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessage, TelegramMessageType

@pytest.mark.asyncio
async def test_file_manager_main__upload_file(TelegramManagerClient_init):
    """
    Test the upload_file method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Create a test file to upload
        test_file_path = File("test_files/test_file.txt")
        
        # Upload the test file to the root folder
        uploaded_file_message = await file_manager.upload_file(client, target_chat_instance, test_file_path, root_folder)
        
        # Check that the uploaded file message is a TelegramMessage with type FILE
        assert isinstance(uploaded_file_message, TelegramMessage), "The uploaded file message is not a TelegramMessage instance"
        assert uploaded_file_message.type == TelegramMessageType.FILE, "The uploaded file message does not have type FILE"
        
        # Check that the uploaded file message has the correct parent and an empty children list
        assert (await uploaded_file_message.get_parent(client)).telegram_message.id == root_folder.telegram_message.id, "The parent of the uploaded file message is not the root folder"
        
        with pytest.raises(ValueError):
            await uploaded_file_message.get_children(client)
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()
