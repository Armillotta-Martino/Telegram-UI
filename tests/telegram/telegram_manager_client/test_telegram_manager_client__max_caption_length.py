import os
import sys

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_telegram_manager_client__max_caption_length(TelegramManagerClient_init):
    """
    Test the max_caption_length property of the TelegramManagerClient class to ensure it returns the correct value
    """
    try:
        # Create a test instance of TelegramManagerClient with valid parameters
        client, target_chat_instance = TelegramManagerClient_init

        # Check that the max_caption_length property returns the expected value
        if hasattr(client.me, 'premium') and client.me.premium:
            expected_max_caption_length = 2048  # 2048 characters for premium users
        else:
            expected_max_caption_length = 1024  # 1024 characters for non-premium users
            
        assert client.max_caption_length == expected_max_caption_length, f"The max_caption_length property did not return the expected value of {expected_max_caption_length} characters"
    except Exception as e:
        pytest.fail(f"An exception occurred while testing max_caption_length: {e}")
    finally:
        await client.disconnect()