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

def test_file_message__generate_json_caption__root():
    """
    Test the generate_json_caption method of TelegramMessage with a root folder
    """
    # Generate a JSON caption for a root folder
    root_caption = TelegramMessage.generate_json_caption(TelegramMessageType.ROOT, "Test Root")
    
    # Check Version field
    assert "Version" in root_caption, "The Version field is not set for a root folder"
    
    # Check Type field
    assert "Type" in root_caption, "The Type field is not set for a root folder"
    assert root_caption["Type"] == TelegramMessageType.ROOT.value, "The Type field is not set correctly for a root folder"
    
    # Check Name field
    assert "Name" in root_caption, "The Name field is not set for a root folder"
    assert root_caption["Name"] == "Test Root", "The Name field is not set correctly for a root folder"
    
    # Check Children field
    assert "Children" in root_caption, "The Children field is not set for a root folder"
    assert root_caption["Children"] == [], "The Children field is not set correctly for a root folder"

    # Ensure there are no extra keys
    assert set(root_caption.keys()) == {"Version", "Type", "Name", "Children"}, "Root caption contains unexpected keys"
    
def test_file_message__generate_json_caption__folder():
    """
    Test the generate_json_caption method of TelegramMessage with a folder
    """
    # Generate a JSON caption for a folder
    folder_caption = TelegramMessage.generate_json_caption(TelegramMessageType.FOLDER, "Test Folder")
    
    # Check Version field
    assert "Version" in folder_caption, "The Version field is not set for a folder"
    
    # Check Type field
    assert "Type" in folder_caption, "The Type field is not set for a folder"
    assert folder_caption["Type"] == TelegramMessageType.FOLDER.value, "The Type field is not set correctly for a folder"
    
    # Check Name field
    assert "Name" in folder_caption, "The Name field is not set for a folder"
    assert folder_caption["Name"] == "Test Folder", "The Name field is not set correctly for a folder"
    
    # Check Children field
    assert "Children" in folder_caption, "The Children field is not set for a folder"
    assert folder_caption["Children"] == [], "The Children field is not set correctly for a folder"
    
    # Check Parent field
    assert "Parent" in folder_caption, "The Parent field is not set for a folder"
    assert folder_caption["Parent"] == None, "The Parent field is not set correctly for a folder"
    
    # Ensure there are no extra keys
    assert set(folder_caption.keys()) == {"Version", "Type", "Name", "Children", "Parent"}, "Folder caption contains unexpected keys"

def test_file_message__generate_json_caption__file():
    """
    Test the generate_json_caption method of TelegramMessage with a file
    """
    # Generate a JSON caption for a file
    file_caption = TelegramMessage.generate_json_caption(TelegramMessageType.FILE, "Test File")
    
    # Check Version field
    assert "Version" in file_caption, "The Version field is not set for a file"
    
    # Check Type field
    assert "Type" in file_caption, "The Type field is not set for a file"
    assert file_caption["Type"] == TelegramMessageType.FILE.value, "The Type field is not set correctly for a file"
    
    # Check Name field
    assert "Name" in file_caption, "The Name field is not set for a file"
    assert file_caption["Name"] == "Test File", "The Name field is not set correctly for a file"
    
    # Check Parent field
    assert "Parent" in file_caption, "The Parent field should not be set for a file"
    
    # Ensure there are no extra keys
    assert set(file_caption.keys()) == {"Version", "Type", "Name", "Parent"}, "File caption contains unexpected keys"

def test_file_message__generate_json_caption__LRV():
    """
    Test the generate_json_caption method of TelegramMessage with a LRV file
    """
    # Generate a JSON caption for a LRV file
    lrv_caption = TelegramMessage.generate_json_caption(TelegramMessageType.LRV, "Test LRV")
    
    # Check Version field
    assert "Version" in lrv_caption, "The Version field is not set for a LRV file"
    
    # Check Type field
    assert "Type" in lrv_caption, "The Type field is not set for a LRV file"
    assert lrv_caption["Type"] == TelegramMessageType.LRV.value, "The Type field is not set correctly for a LRV file"
    
    # Ensure there are no extra keys
    assert set(lrv_caption.keys()) == {"Version", "Type"}, "LRV caption contains unexpected keys"
    
def test_file_message__generate_json_caption__thumbnail():
    """
    Test the generate_json_caption method of TelegramMessage with a thumbnail file
    """
    # Generate a JSON caption for a thumbnail file
    thumbnail_caption = TelegramMessage.generate_json_caption(TelegramMessageType.THUMBNAIL, "Test Thumbnail")
    
    # Check Version field
    assert "Version" in thumbnail_caption, "The Version field is not set for a thumbnail file"
    
    # Check Type field
    assert "Type" in thumbnail_caption, "The Type field is not set for a thumbnail file"
    assert thumbnail_caption["Type"] == TelegramMessageType.THUMBNAIL.value, "The Type field is not set correctly for a thumbnail file"
    
    # Ensure there are no extra keys
    assert set(thumbnail_caption.keys()) == {"Version", "Type"}, "Thumbnail caption contains unexpected keys"
    
def test_file_message__generate_json_caption__invalid_type():
    """
    Test the generate_json_caption method of TelegramMessage with an invalid type
    """
    with pytest.raises(ValueError, match="Unknown TelegramMessageType: InvalidType"):
        TelegramMessage.generate_json_caption("InvalidType", "Test Name")
        
