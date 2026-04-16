import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
from file_types.video import Video
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from dbJson.telegram_message import TelegramMessageType

@pytest.mark.asyncio
async def test_file_message__type_root(TelegramManagerClient_init):
    """
    Test the type method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the type method returns "file"
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        # Assert that the type method returns "file"
        assert root_message.type == TelegramMessageType.ROOT, f"TelegramMessage.type returned {root_message.type} instead of 'root' for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()
        
@pytest.mark.asyncio
async def test_file_message__type__file(TelegramManagerClient_init):
    """
    Test the type method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the type method returns "file"
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a File object with a test file
        file = File("test_files/test_file.txt")
        # Upload a file to the target chat instance to create a new TelegramMessage
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Assert that the type method returns "file"
        assert file_message.type == TelegramMessageType.FILE, f"TelegramMessage.type returned {file_message.type} instead of 'file' for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()

@pytest.mark.asyncio
async def test_file_message__type__folder(TelegramManagerClient_init):
    """
    Test the type method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the type method returns "file"
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a folder message
        folder_message = await FileManager.create_folder(client, target_chat_instance, "Test Folder", root_message)
        
        # Assert that the type method returns "folder"
        assert folder_message.type == TelegramMessageType.FOLDER, f"TelegramMessage.type returned {folder_message.type} instead of 'folder' for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()

@pytest.mark.asyncio
async def test_file_message__type__LRV(TelegramManagerClient_init):
    """
    Test the type method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the type method returns "file"
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a Video object with a test file
        file = Video(File("test_files/test_video.mp4"))
        # Upload a file to the target chat instance to create a new file message
        video_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Get the LRV file message
        lrv_file_messages = (await video_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.LRV))
        
        if len(lrv_file_messages) == 0:
            pytest.fail("No LRV file message found for a valid Video file message")
            
        if len(lrv_file_messages) > 1:
            pytest.fail("Multiple LRV file messages found for a valid Video file message")
            
        lrv_file_message = lrv_file_messages[0]
        
        # Assert that the type method returns "LRV"
        assert lrv_file_message.type == TelegramMessageType.LRV, f"TelegramMessage.type returned {lrv_file_message.type} instead of 'LRV' for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()
 
@pytest.mark.asyncio
async def test_file_message__type__thumbnail(TelegramManagerClient_init):
    """
    Test the type method of TelegramMessage
    """
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root TelegramMessage
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Create a Video object with a test file
        file = Video(File("test_files/test_video.mp4"))
        # Upload a file to the target chat instance to create a new TelegramMessage
        video_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Get the Thumbnail TelegramMessage
        thumbnail_file_messages = (await video_message.get_comments_by_type(client, target_chat_instance, TelegramMessageType.THUMBNAIL))
        
        if len(thumbnail_file_messages) == 0:
            pytest.fail("No Thumbnail file message found for a valid Video file message")
            
        if len(thumbnail_file_messages) > 1:
            pytest.fail("Multiple Thumbnail file messages found for a valid Video file message")
            
        thumbnail_file_message = thumbnail_file_messages[0]
        
        # Assert that the type method returns "THUMBNAIL"
        assert thumbnail_file_message.type == TelegramMessageType.THUMBNAIL, f"TelegramMessage.type returned {thumbnail_file_message.type} instead of 'THUMBNAIL' for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()