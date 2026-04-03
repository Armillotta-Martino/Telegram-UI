import os
import sys

import pytest

from telegram.telegram_manager_client import TelegramManagerClient

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_telegram_manager_client__initialize(TelegramManagerClient_init):
    """
    Test the initialization of the TelegramManagerClient class to ensure it starts and connects properly
    """
    try:
        # Create a test instance of TelegramManagerClient with valid parameters
        client, target_chat_instance = TelegramManagerClient_init

        # Check that the instance is created successfully and is connected
        assert isinstance(client, TelegramManagerClient), "The constructor did not create an instance of TelegramManagerClient"
        assert client.is_connected(), "The client did not connect successfully"
    except Exception as e:
        pytest.fail(f"Initialization of TelegramManagerClient failed with an exception: {e}")
    finally:
        await client.disconnect()