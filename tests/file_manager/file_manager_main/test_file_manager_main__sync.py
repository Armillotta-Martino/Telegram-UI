import os
import sys

from file_manager.file_manager_main import FileManager
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_file_manager_main__sync(monkeypatch, TelegramManagerClient_init):
    """
    Test the sync method of FileManager
    """
    try:
        # Create a FileManager instance
        file_manager = FileManager()
        
        # Init variables for TelegramManagerClient
        client, target_chat_instance = TelegramManagerClient_init
        
        # Get the root folder
        root_folder = await file_manager.get_root(client, target_chat_instance)
        
        # async fake implementations
        async def fake_save(pc_path, telegram_link): 
            return None

        async def fake_get(pc_path, telegram_link):
            return {"pc_path": pc_path, "telegram_link": telegram_link, "state": FileManager.SyncState.NEW.value, "synced_files": []}
        
        async def fake_update(sync_job, synced_file):
            return None

        async def fake_update_state(sync_job, new_state):
            return None
        
        monkeypatch.setattr(FileManager, "_save_sync_job", staticmethod(fake_save))
        monkeypatch.setattr(FileManager, "_get_sync_job", staticmethod(fake_get))
        monkeypatch.setattr(FileManager, "_update_sync_job", staticmethod(fake_update))
        monkeypatch.setattr(FileManager, "_update_sync_job_state", staticmethod(fake_update_state))

        # Sync the test_files directory in the root folder
        await file_manager.sync(client, target_chat_instance, "test_files", root_folder)
        
        # Get the children of the root folder
        children = await root_folder.get_children(client)
        
        # Check that the root folder now has children (the synced files)
        assert len(children) > 0, "Root folder should have children after sync"    
        assert any(child.file_name == "test_files" for child in children), "Root folder should contain the synced 'test_files' folder"
        
        # Check that the synced folder is a copy of the local directory (not just a reference)
        synced_folder = next(child for child in children if child.file_name == "test_files")
        assert synced_folder.is_folder, "Synced 'test_files' should be a folder"
        
        synced_children = await synced_folder.get_children(client)
        
        assert len(synced_children) > 0, "Synced 'test_files' folder should have children"
        
        local_files = set(os.listdir("test_files"))
        assert all(child.file_name in local_files for child in synced_children), "Synced folder should contain the correct files"
        
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        await client.disconnect()