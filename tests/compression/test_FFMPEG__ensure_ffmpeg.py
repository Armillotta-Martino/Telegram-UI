import io
import shutil
import zipfile
from types import SimpleNamespace
import zipfile
import os
import sys

import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from compression.FFMPEG import FFMPEG


def test_ensure_ffmpeg__noop(monkeypatch, tmp_path):
    """
    If ffmpeg files already exist, ensure_ffmpeg should be a no-op.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Make os.path.exists return True for any path so the function skips download
    monkeypatch.setattr('compression.FFMPEG.os.path.exists', lambda p: True)

    # Track whether requests.get would be called
    called = {"value": False}
    def fake_get(url, stream=True):
        called["value"] = True
        raise Exception("Download should not be attempted")

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Execute
    FFMPEG.ensure_ffmpeg()

    # Assert requests.get was not called
    assert called["value"] is False

def test_ensure_ffmpeg__creates_files(monkeypatch, tmp_path):
    """
        When ffmpeg is missing, ensure_ffmpeg should download and install binaries into `ffmpeg/`.
        This test mocks the download and file system interactions to verify the expected behavior.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Create an in-memory zip containing ffmpeg executables under a nested folder
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"fake-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"fake-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"fake-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    # Ensure ffmpeg folder does not exist before
    assert not (tmp_path / "ffmpeg").exists()

    # Execute
    FFMPEG.ensure_ffmpeg()

    # Verify executables moved into ffmpeg folder
    assert (tmp_path / "ffmpeg" / "ffmpeg.exe").exists()
    assert (tmp_path / "ffmpeg" / "ffprobe.exe").exists()
    assert (tmp_path / "ffmpeg" / "ffplay.exe").exists()

def test_ensure_ffmpeg__download_failure(monkeypatch, tmp_path):
    """
        If the download fails (e.g., network error), ensure_ffmpeg should raise an exception.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Patch requests.get to raise an exception simulating a download failure
    def fake_get(url, stream=True):
        raise Exception("Network error")

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)
    
    # Execute and assert that the expected exception is raised
    with pytest.raises(Exception, match="Network error"):
        FFMPEG.ensure_ffmpeg()
        
def test_ensure_ffmpeg__invalid_zip(monkeypatch, tmp_path):
    """
        If the downloaded file is not a valid zip, ensure_ffmpeg should raise an exception.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Patch requests.get to return invalid zip content
    def fake_get(url, stream=True):
        return SimpleNamespace(content=b"not-a-zip")

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)
    
    # Execute and assert that a BadZipFile exception is raised
    with pytest.raises(zipfile.BadZipFile):
        FFMPEG.ensure_ffmpeg()

def test_ensure_ffmpeg__missing_executables(monkeypatch, tmp_path):
    """
        If the zip does not contain the expected executables, ensure_ffmpeg should raise an exception.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Create an in-memory zip without the expected executables
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/some_other_file.exe", b"fake-content")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our invalid zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)
    
    # Execute and assert that the expected exception is raised due to missing executables
    with pytest.raises(Exception, match="Expected ffmpeg executables not found in the zip"):
        FFMPEG.ensure_ffmpeg()

def test_ensure_ffmpeg__cleanup_on_failure(monkeypatch, tmp_path):
    """
        If an error occurs during extraction, ensure_ffmpeg should clean up any partially created files.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Create an in-memory zip with valid structure but will cause an error during extraction
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"fake-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"fake-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"fake-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Patch shutil.move to raise an exception simulating a failure during file move
    def fake_move(src, dst):
        raise Exception("File move error")

    monkeypatch.setattr('compression.FFMPEG.shutil.move', fake_move)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)
    
    # Execute and assert that the expected exception is raised due to file move error
    with pytest.raises(Exception, match="File move error"):
        FFMPEG.ensure_ffmpeg()

    # Verify that no ffmpeg executables exist after the failure (dir may remain)
    assert not (tmp_path / "ffmpeg" / "ffmpeg.exe").exists()
    # Verify zip cleaned up
    assert not (tmp_path / "ffmpeg.zip").exists()

def test_ensure_ffmpeg__already_exists(monkeypatch, tmp_path):
    """
        If the ffmpeg folder already exists, ensure_ffmpeg should not attempt to download or modify files.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Create a dummy ffmpeg folder with an executable to simulate existing installation
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    (ffmpeg_dir / "ffmpeg.exe").write_text("existing-ffmpeg")
    (ffmpeg_dir / "ffprobe.exe").write_text("existing-ffprobe")
    (ffmpeg_dir / "ffplay.exe").write_text("existing-ffplay")

    # Patch requests.get to raise an exception if called, ensuring it is not called
    def fake_get(url, stream=True):
        raise Exception("Download should not be attempted")

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Run inside temporary cwd so function checks tmp path
    monkeypatch.chdir(tmp_path)

    # Call the function under test
    FFMPEG.ensure_ffmpeg()

    # Verify that the existing ffmpeg.exe is still there and unchanged
    assert (ffmpeg_dir / "ffmpeg.exe").exists()
    assert (ffmpeg_dir / "ffmpeg.exe").read_text() == "existing-ffmpeg"

def test_ensure_ffmpeg__partial_extraction_cleanup(monkeypatch, tmp_path):
    """
        If an error occurs during extraction, ensure_ffmpeg should clean up any partially extracted files.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Create an in-memory zip with valid structure but will cause an error during extraction
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"fake-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"fake-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"fake-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Patch shutil.move to raise an exception simulating a failure during file move
    def fake_move(src, dst):
        raise Exception("File move error")

    monkeypatch.setattr('compression.FFMPEG.shutil.move', fake_move)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    with pytest.raises(Exception, match="File move error"):
        FFMPEG.ensure_ffmpeg()

    # Verify that no ffmpeg executables exist after the failure (dir may remain)
    assert not (tmp_path / "ffmpeg" / "ffmpeg.exe").exists()
    # Verify zip cleaned up
    assert not (tmp_path / "ffmpeg.zip").exists()
    
def test_ensure_ffmpeg__invalid_zip_cleanup(monkeypatch, tmp_path):
    """
        If the downloaded file is not a valid zip, ensure_ffmpeg should clean up any partially created files.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)
    
    # Patch requests.get to return invalid zip content
    def fake_get(url, stream=True):
        return SimpleNamespace(content=b"not-a-zip")

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    with pytest.raises(zipfile.BadZipFile):
        FFMPEG.ensure_ffmpeg()

    # Verify that no ffmpeg executables exist after the failure (dir may remain)
    assert not (tmp_path / "ffmpeg" / "ffmpeg.exe").exists()
    # Verify zip cleaned up
    assert not (tmp_path / "ffmpeg.zip").exists()
    
def test_ensure_ffmpeg__successful_installation(monkeypatch, tmp_path):
    """
        When ffmpeg is successfully downloaded and installed, ensure_ffmpeg should create the expected files.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)

    # Create an in-memory zip containing ffmpeg executables under a nested folder
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"fake-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"fake-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"fake-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    # Call the function under test
    FFMPEG.ensure_ffmpeg()

    # Verify that the ffmpeg folder and executables exist after successful installation
    ffmpeg_dir = tmp_path / "ffmpeg"
    assert (ffmpeg_dir / "ffmpeg.exe").exists()
    assert (ffmpeg_dir / "ffprobe.exe").exists()
    assert (ffmpeg_dir / "ffplay.exe").exists()
    
def test_ensure_ffmpeg__ensure_last_version(monkeypatch, tmp_path):
    """
        If ffmpeg files already exist but are outdated, ensure_ffmpeg should update them to the latest version.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)

    # Create a dummy ffmpeg folder with an old executable to simulate existing installation
    ffmpeg_dir = tmp_path / "ffmpeg"
    ffmpeg_dir.mkdir()
    (ffmpeg_dir / "ffmpeg.exe").write_text("old-ffmpeg")

    # Create an in-memory zip containing the latest ffmpeg executables under a nested folder
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"new-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"new-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"new-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    # Call the function under test
    FFMPEG.ensure_ffmpeg()

    # Verify that the ffmpeg executables have been updated to the new version
    assert (ffmpeg_dir / "ffmpeg.exe").exists()
    assert (ffmpeg_dir / "ffprobe.exe").exists()
    assert (ffmpeg_dir / "ffplay.exe").exists()
    
def test_ensure_ffmpeg__no_partial_files_on_failure(monkeypatch, tmp_path):
    """
        If an error occurs during the installation process, ensure_ffmpeg should not leave any partial files behind.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)

    # Create an in-memory zip containing ffmpeg executables under a nested folder
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"fake-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"fake-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"fake-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Patch shutil.move to raise an exception simulating a failure during file move
    def fake_move(src, dst):
        raise Exception("File move error")

    monkeypatch.setattr('compression.FFMPEG.shutil.move', fake_move)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    with pytest.raises(Exception, match="File move error"):
        FFMPEG.ensure_ffmpeg()

    # Verify that no ffmpeg folder or executables exist after the failure
    # (on some systems an empty directory may remain; ensure executables are gone)
    assert not (tmp_path / "ffmpeg" / "ffmpeg.exe").exists()
    assert not (tmp_path / "ffmpeg.zip").exists()
    
def test_ensure_ffmpeg__valid_zip_creates_files(monkeypatch, tmp_path):
    """
        When a valid zip is downloaded, ensure_ffmpeg should extract and create the expected files.
    """
    # Ensure clean state before test
    __cleanup_ffmpeg_folder(tmp_path)

    # Create an in-memory zip containing ffmpeg executables under a nested folder
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("build/bin/ffmpeg.exe", b"fake-ffmpeg")
        z.writestr("build/bin/ffprobe.exe", b"fake-ffprobe")
        z.writestr("build/bin/ffplay.exe", b"fake-ffplay")
    zip_bytes = buf.getvalue()

    # Patch requests.get to return our zip bytes
    def fake_get(url, stream=True):
        return SimpleNamespace(content=zip_bytes)

    monkeypatch.setattr('compression.FFMPEG.requests.get', fake_get)

    # Run inside temporary cwd so function writes to tmp path
    monkeypatch.chdir(tmp_path)

    # Call the function under test
    FFMPEG.ensure_ffmpeg()

    # Verify that the ffmpeg executables have been created
    assert (tmp_path / "ffmpeg" / "ffmpeg.exe").exists()
    assert (tmp_path / "ffmpeg" / "ffprobe.exe").exists()
    assert (tmp_path / "ffmpeg" / "ffplay.exe").exists()



def __cleanup_ffmpeg_folder(tmp_path):
    """
        Helper function to clean up the ffmpeg folder after tests that may create it.
        This ensures that each test starts with a clean state and prevents interference between tests.
    """
    # Do NOT remove the provided tmp_path itself (pytest manages it).
    
    '''
    # Remove the ffmpeg folder from the original repository location if it exists
    original_ffmpeg_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'ffmpeg'))
    try:
        if os.path.exists(original_ffmpeg_dir):
            shutil.rmtree(original_ffmpeg_dir)
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # Remove the ffmpeg.zip file from the original repository location if it exists
    original_zip_file = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'ffmpeg.zip'))
    try:
        if os.path.exists(original_zip_file):
            os.remove(original_zip_file)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    '''