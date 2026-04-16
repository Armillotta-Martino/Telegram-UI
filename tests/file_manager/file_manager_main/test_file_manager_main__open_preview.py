import os
import subprocess
import sys

from file_manager.file_manager_main import FileManager

from file_types.file import File
from file_types.video import Video
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_main__open_preview(monkeypatch, TelegramManagerClient_init):
    """
    Test the open_preview method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Create a root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # Upload a video file
        video = Video(File("test_files/test_video.mp4"))
        video_file_message = await file_manager.upload_file(client, target_chat_instance, video, root_folder)
        
        # Prepare monkeypatch to intercept external opener calls (no real GUI open)
        recorded = {}

        class FakePopen:
            def __init__(self, cmd, stdout=None, stderr=None):
                recorded['cmd'] = cmd

            def wait(self):
                return 0

        monkeypatch.setattr(subprocess, "Popen", FakePopen)
        # os.startfile is Windows-only; allow creating it if missing
        monkeypatch.setattr(os, "startfile", lambda path: recorded.setdefault('startfile', path), raising=False)

        # Open preview for the file message (should call our fake opener)
        await file_manager.open_preview(client, target_chat_instance, video_file_message)

        # Assert an opener was invoked and received an mp4 temp file
        assert ('cmd' in recorded) or ('startfile' in recorded), "No opener was invoked"
        if 'cmd' in recorded:
            cmd = recorded['cmd']
            assert any(isinstance(e, str) and (e.endswith('.mp4') or '.mp4' in e) for e in cmd), f"Opener called without mp4: {cmd}"
            assert cmd[0] in ("vlc", "open", "xdg-open", "powershell"), f"Unexpected opener: {cmd[0]}"
        else:
            assert recorded['startfile'].endswith('.mp4'), f"startfile called with unexpected path: {recorded['startfile']}"
    except Exception as e:
        raise e
    finally:
        await client.disconnect()