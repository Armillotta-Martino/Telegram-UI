import os
import sys

from file_manager.file_manager_main import FileManager
from file_types.file import File
from file_types.video import Video
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_message__get_comments(TelegramManagerClient_init):
    """
    Test the get_comments method of TelegramMessage with valid input
    """
    try:
        client, target_chat_instance = TelegramManagerClient_init
            
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        
        # Upload a video file
        file = Video(File('test_files/test_video.mp4'))
        file_message = await FileManager.upload_file(client, target_chat_instance, file, root_message)
        
        # Get the comments of type FILE for the file message
        comments = await file_message.get_comments(client, target_chat_instance)
        
        assert len(comments) > 0, "There should be at least one comment of type FILE"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()