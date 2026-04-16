import os
import sys

from file_manager.file_manager_main import FileManager
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_message__version(TelegramManagerClient_init):
    """
    Test the version method of TelegramMessage
    """
    # Create a TelegramMessage object with a valid file path and assert that the version method returns the correct value
    try:
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root file message
        root_message = await FileManager.get_root(client, target_chat_instance)
        version = root_message.version
        
        assert version is not None and isinstance(version, str), "TelegramMessage.version did not return a valid version string for a valid TelegramMessage object"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()