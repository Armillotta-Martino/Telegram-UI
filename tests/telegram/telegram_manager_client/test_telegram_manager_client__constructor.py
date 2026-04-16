import os
import sys

import pytest

from telegram.telegram_manager_client import TelegramManagerClient
from config import API_HASH, API_ID
from telethon.tl.types import Channel

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_telegram_manager_client__constructor(TelegramManagerClient_init):
    """
    Test the constructor of the TelegramManagerClient class to ensure it initializes correctly with valid parameters
    """
    try:
        # Initialize the TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init

        # Check that the instance is created successfully
        assert isinstance(client, TelegramManagerClient), "The constructor did not create an instance of TelegramManagerClient"
        assert isinstance(target_chat_instance, Channel), "The target_chat_instance should be an instance of Entity"
        
        assert client.api_id == API_ID, "The api_id attribute was not set correctly"
        assert client.api_hash == API_HASH, "The api_hash attribute was not set correctly"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()