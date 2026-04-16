import os
import sys

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_telegram_manager_client__start(TelegramManagerClient_init):
    """
    Test the start method of the TelegramManagerClient class to ensure it starts the client correctly
    """
    try:
        # Initialize the TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Check that the client is started and connected
        assert client.is_connected(), "The client did not start and connect successfully"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()