import os
import sys

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_telegram_manager_client__me(TelegramManagerClient_init):
    """
    Test the me method of the TelegramManagerClient class to ensure it retrieves the correct user information
    """
    try:
        # Initialize the TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init

        # Check that the retrieved information is correct
        assert client.me is not None, "The me method did not return any user information"
        assert client.me.id is not None, "The me method did not return a valid user ID"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()