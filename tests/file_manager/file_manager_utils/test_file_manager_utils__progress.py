import os
import sys
import time
import asyncio
from ui.pop_up_progress_bar import PopUp_Progress_Bar

from file_manager.file_manager_utils import FileManager_Utils
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_utils__progress(monkeypatch):
    """
    Test the progress function of FileManager_Utils by simulating a long-running operation that updates progress information
    """
    # Monkeypatch the progress bar singleton to capture updates
    recorded = []

    class FakeWin:
        def update(self, pct, text):
            recorded.append((pct, text))

    monkeypatch.setattr(PopUp_Progress_Bar, "instance", staticmethod(lambda: FakeWin()))

    # Simulate progress updates without real sleeps
    for i in range(6):
        FileManager_Utils.progress(i * 20, 100, "Test")
        await asyncio.sleep(0)

    assert len(recorded) == 6
    for idx, (pct, text) in enumerate(recorded):
        assert pct == idx * 20.0
        assert text == "Test"
