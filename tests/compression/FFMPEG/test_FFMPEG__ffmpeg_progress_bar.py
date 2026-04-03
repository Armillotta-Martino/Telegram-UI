import threading
import time
from types import SimpleNamespace
import os
import sys
import pytest

# Ensure tests import the local `src/` package during test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from compression.FFMPEG import FFMPEG

def test_ffmpeg_progress_bar():
    """
    Test the ffmpeg_progress_bar function by simulating a long-running ffmpeg process that outputs progress information
    """
        
    # Create a pair of OS pipes so the test writer can write progress lines
    read_fd, write_fd = os.pipe()

    # Create a dummy process-like object with a readable stdout
    process = SimpleNamespace()
    process.stdout = os.fdopen(read_fd, 'r', buffering=1)
    process.stderr = None
    process._write_fd = write_fd
    process._finished = False
    def poll():
        return 0 if process._finished else None
    process.poll = poll
    def wait():
        # block until writer is closed
        while not process._finished:
            time.sleep(0.01)
    process.wait = wait

    q = [None]  # Use a list to allow modification from the thread

    def simulate_progress_output(proc : SimpleNamespace, q : list) -> None:
        # Write progress updates to the write end of the pipe
        for i in range(0, 11):
            # Simulate time taken for processing
            time.sleep(1)
            os.write(proc._write_fd, f'out_time_ms={i * 1000 * 1000}\n'.encode('utf-8'))
            q[0] = {'out_time_ms': i}
        # Close the writer and mark finished so the reader can exit
        os.close(proc._write_fd)
        proc._finished = True

    # Simulate the progress output in a separate thread
    progress_reader_thread = threading.Thread(target=simulate_progress_output, args=(process, q))
    progress_reader_thread.start()

    # Call the progress bar function (this will block until the process finishes)
    FFMPEG.ffmpeg_progress_bar("Test File", process, 10)

    # Wait for the progress reader thread to finish
    progress_reader_thread.join()
    
    # Check that the progress was updated correctly
    assert q[0] is not None
    assert 'out_time_ms' in q[0]
    assert q[0]['out_time_ms'] == 10  # Final progress should be 10 seconds
    