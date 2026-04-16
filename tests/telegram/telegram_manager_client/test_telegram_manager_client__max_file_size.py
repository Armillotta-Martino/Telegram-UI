import os
import sys

from config import BOT_USER_MAX_FILE_SIZE, PREMIUM_USER_MAX_FILE_SIZE, USER_MAX_FILE_SIZE
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_telegram_manager_client__max_file_size(TelegramManagerClient_init):
    """
    Test the max_file_size property of the TelegramManagerClient class to ensure it returns the correct value
    """
    try:
        # Create a test instance of TelegramManagerClient with valid parameters
        client, target_chat_instance = TelegramManagerClient_init

        # Check that the max_file_size property returns the expected value
        if hasattr(client.me, 'premium') and client.me.premium:
            expected_max_file_size = PREMIUM_USER_MAX_FILE_SIZE
        elif client.me.bot:
            expected_max_file_size = BOT_USER_MAX_FILE_SIZE
        else:
            expected_max_file_size = USER_MAX_FILE_SIZE
        
        assert client.max_file_size == expected_max_file_size, f"The max_file_size property did not return the expected value of {expected_max_file_size} bytes"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()