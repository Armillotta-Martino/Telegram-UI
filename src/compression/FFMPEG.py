from ctypes import c_int64
import os
import re
import shutil
import subprocess
from threading import Thread
import time
from typing import List
import zipfile
import requests

# Import constants from config
from config import FFMPEG_RELATIVE_PATH, FFPROBE_RELATIVE_PATH

from file_manager.file_manager_utils import FileManager_Utils

class FFMPEG():
    """
    Class responsible for ensuring ffmpeg is installed and providing methods to call ffmpeg and 
    ffprobe commands
    """
    
    @staticmethod
    def ensure_ffmpeg():
        """
        Ensure ffmpeg is installed and at the last version, if not download and install it
        
        Raises:
            FileNotFoundError: If ffmpeg could not be found or installed
        """
        
        # TODO Check if ffmpeg is up to date, if not update it
        
        # Determine whether installation/update is needed: require all three executables
        ffplay_rel = os.path.join(os.path.dirname(FFMPEG_RELATIVE_PATH), 'ffplay.exe')
        # Check if ffmpeg, ffprobe, and ffplay exist in the expected locations
        installed = (
            os.path.exists(FFMPEG_RELATIVE_PATH) and 
            os.path.exists(FFPROBE_RELATIVE_PATH) and 
            os.path.exists(ffplay_rel)
        )
        
        # Check if ffmpeg and ffprobe are in the environment variables
        ffmpeg_installed = FFMPEG.__validate_executable('ffmpeg')[0]
        ffprobe_installed = FFMPEG.__validate_executable('ffprobe')[0]
        
        # Check if ffmpeg and ffprobe are functional
        environment_set = (
            ffmpeg_installed and
            ffprobe_installed
        )

        # Check if ffmpeg folder exists or needs update
        if not installed and not environment_set:
            # Download and install ffmpeg
            print("Downloading ffmpeg...")
            os.makedirs(os.path.dirname(FFMPEG_RELATIVE_PATH), exist_ok=True)
            
            # Define paths
            zip_path = "ffmpeg.zip"
            temp_extract_dir = "ffmpeg_temp"

            target_dir = os.path.dirname(FFMPEG_RELATIVE_PATH)
            target_dir_abs = os.path.abspath(target_dir)
            dir_preexisting = os.path.exists(target_dir_abs)
            os.makedirs(target_dir_abs, exist_ok=True)
                
            try:
                ## Download and extract ffmpeg
                
                # Download zip
                url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                r = requests.get(url, stream=True)
                with open(zip_path, "wb") as f:
                    f.write(r.content)

                # Extract zip
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_extract_dir)

                # Find the bin folder dynamically
                bin_folder = None
                for root, dirs, files in os.walk(temp_extract_dir):
                    if "ffmpeg.exe" in files:
                        bin_folder = root
                        break

                if not bin_folder:
                    raise FileNotFoundError("Could not find ffmpeg.exe in the extracted zip")

                # Move binaries to 'ffmpeg' folder
                for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                    shutil.move(os.path.join(bin_folder, exe), os.path.join(target_dir_abs, exe))
                    
                # Clean up the zip file
                try:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                except Exception:
                    pass
                
                # Clean up the extracted temp folder
                try:
                    if os.path.exists(temp_extract_dir):
                        shutil.rmtree(temp_extract_dir)
                except Exception:
                    pass

                print("ffmpeg installed successfully.")
            except Exception as e:
                ## Cleanup on failure
                print(f"Failed to install ffmpeg: {e}")
                
                # Clean up the zip file
                try:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                except Exception:
                    pass
                    
                # Clean up the extracted temp folder
                try:
                    if os.path.exists(temp_extract_dir):
                        shutil.rmtree(temp_extract_dir)
                except Exception:
                    pass
                
                # Remove target dir only if it did not exist before we ran
                try:
                    if not dir_preexisting and os.path.exists(target_dir_abs):
                        # Attempt to remove known binaries first (best-effort)
                        for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                            try:
                                # Generate path
                                p = os.path.join(target_dir_abs, exe)
                                # Attempt to remove the file if it exists
                                if os.path.exists(p):
                                    os.remove(p)
                            except Exception:
                                pass
                        
                        # Second attempt: remove the directory if it is empty or contains only the expected files (best-effort)
                        try:
                            shutil.rmtree(target_dir_abs)
                        except Exception:
                            # Final attempt: remove directory if empty
                            try:
                                os.rmdir(target_dir_abs)
                            except Exception:
                                pass
                except Exception:
                    pass
                
                # Re-raise the original exception to ensure the caller is aware of the failure
                raise e
    
    @classmethod
    def __validate_executable(self, path: str, timeout: float = 5.0) -> tuple[bool, str | None]:
        """
        Run `path -version` to verify the executable works
        
        Args:
            path (str): The path to the executable
            timeout (float): The maximum time to wait for the command to complete
        Returns:
            tuple (bool, str | None): A tuple containing a boolean indicating success and the output or error message
        """
        try:
            proc = subprocess.run(
                [path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            out = proc.stdout.strip() or proc.stderr.strip()
            return (proc.returncode == 0, out)
        except FileNotFoundError:
            return (False, None)
        except subprocess.TimeoutExpired:
            return (False, "timeout")
        except Exception as e:
            return (False, str(e))
    
    @classmethod    
    def __get_command_path(self, exe_path_json : str, exe_name : str) -> str:
        """
        Function for get the exe path
        This is designed to be used for find the ffmpeg and ffprobe file
            
        Args:
            exe_path_json (str): The environment variable name where the path is stored
            exe_name (str): The executable name to search
        Returns:
            str: The path of the executable
        """
        resultPath = None

        # Normalize executable name (use basename for PATH/dir checks)
        exe_base = os.path.basename(exe_name)
        
        # 1) Execute the ffmpeg command to check if it is already set up correctly in the environment variables
        ok, output_or_error = self.__validate_executable(exe_path_json.lower())
        if ok:
            return exe_path_json.lower()
        
        # 2) If exe_name itself is a path in cwd or absolute path, use it
        if os.path.exists(exe_name) and not os.path.isdir(exe_name):
            return os.path.abspath(exe_name)
        # If only the basename exists in cwd, use that
        if exe_base and os.path.exists(exe_base) and not os.path.isdir(exe_base):
            return os.path.abspath(exe_base)

        # 3) As a last option, try to install ffmpeg
        try:
            self.ensure_ffmpeg()
        except Exception:
            # ignore install failures here; caller will handle a missing path
            pass

        if os.path.exists(exe_name):
            return os.path.abspath(exe_name)

        # Not found
        return None

    @classmethod
    def call_ffmpeg(self, args : List[str]) -> subprocess.Popen:
        """
        Function for execute a ffmpeg command
        
        Args:
            args (List[str]): The ffmpeg arguments
        Returns:
            subprocess.Popen: The ffmpeg process
        Raises:
            FileNotFoundError: If ffmpeg command is not available
        """
        try:
            # Get the ffmpeg path
            ffmpegPath = self.__get_command_path("FFMPEG", FFMPEG_RELATIVE_PATH)
            
            # Check if ffmpeg path was found
            if not ffmpegPath:
                raise FileNotFoundError('ffmpeg executable not found')
            
            # Build the command with the provided arguments
            ffmpegScript = [ffmpegPath] + args
            
            # Execute the command
            proc = subprocess.Popen(
                ffmpegScript,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            return proc
        except FileNotFoundError:
            # Re-raise with a clear message
            raise FileNotFoundError('ffmpeg executable not found')
        except Exception as e:
            # Re-raise the original exception to ensure the caller is aware of the failure
            raise e
    
    @classmethod
    def call_ffprobe(self, args : List[str]) -> subprocess.Popen:
        """
        Function for execute a ffprobe command
        
        Args:
            args (List[str]): The ffprobe arguments
        Returns:
            subprocess.Popen: The ffprobe process
        Raises:
            FileNotFoundError: If ffprobe command is not available
        """
        try:
            # Get the ffprobe path
            ffProbePath = self.__get_command_path("FFPROBE", FFMPEG_RELATIVE_PATH)
            
            # Check if ffprobe path was found
            if not ffProbePath:
                raise FileNotFoundError('ffprobe executable not found')
            
            # Build the command with the provided arguments
            ffprobeScript = [ffProbePath] + args
            
            # Execute the command
            proc = subprocess.Popen(
                ffprobeScript,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            return proc
        except FileNotFoundError:
            # Re-raise with a clear message
            raise FileNotFoundError('ffprobe executable not found')
        except Exception as e:
            # Re-raise the original exception to ensure the caller is aware of the failure
            raise e
    
    @classmethod
    def ffmpeg_progress_bar(self, file_name : str, process : subprocess.Popen, total_duration_s : int) -> None:
        """
        Create the ffmpeg progress bar

        This is different from the normal progress bar as i use a thread for read the value from the process
            
        Args:
            file_name (str): The name of the video file
            process (subprocess.Popen): The ffmpeg process
            total_duration_s (int): The total duration of the video in seconds
        Returns:
            None
        """
        
        def progress_reader(proc : subprocess.Popen, q : list) -> None:
            """
            Read the ffmpeg output frame number and save it
            
            Args:
                proc (subprocess.Popen): The ffmpeg process
                q (list): The queue to store the frame number
            """
            
            # Loop until the process is closed
            while True:
                # Check if the process is closed
                if proc.poll() is not None:
                    # Stop the loop
                    break
                
                # Read line from the pipe
                progress_text = proc.stdout.readline()

                # Break the loop if progress_text is None
                if progress_text is None:
                    break
                
                ## Get the out_time_ms and out_time from the progress text
                
                # Get the out_time_ms value using regex
                m_out_ms = re.search(r"^out_time_ms=\s*(\d+)$", progress_text.strip())
                if m_out_ms:
                    try:
                        ## Update the queue with the new out_time_ms value
                        
                        q_dict = q[0]
                        # NOTE: I don't know why but the out_time_ms value is in microseconds, so I divide by 1000 to 
                        # get milliseconds
                        q_dict['out_time_ms'] = int(m_out_ms.group(1)) / 1000
                        q[0] = q_dict
                    except Exception:
                        pass
                
                # Get the out_time value using regex
                m_out = re.search(r"^out_time=\s*([0-9:.]+)$", progress_text.strip())
                if m_out:
                    try:
                        # Parse the out_time value in the format HH:MM:SS.mmm and convert it to seconds
                        timestr = m_out.group(1)
                        parts = timestr.split(':')
                        secs = 0.0
                        if len(parts) == 3:
                            secs = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                        
                        ## Update the queue with the new out_time value
                        
                        q_dict = q[0]
                        q_dict['out_time'] = secs
                        q[0] = q_dict
                    except Exception:
                        pass

        def progress_bar_execution(action: str, file_name : str, p : subprocess.Popen, q : list, total_duration_s : int, update_time_s : float = 1) -> None:
            """
            Execute the ffmpeg progress loop that updates every `update_time_s` seconds

            Uses `FileManager_Utils.progress` (GUI if available) to display progress
            
            Args:
                action (str): The action being performed (e.g. "Compressing file")
                file_name (str): The name of the file being processed
                p (subprocess.Popen): The ffmpeg process
                q (list): The queue to store progress information
                total_duration_s (int): The total duration of the video in seconds
                update_time_s (float): The time interval for updating the progress (default is 1 second)
            """
            # Initialize the last current time
            last_current = c_int64(0)
            
            # Loop until the process is closed
            while True:
                # Check if the process is closed
                if p.poll() is not None:
                    # Stop the loop
                    break

                # Wait for the update time
                time.sleep(update_time_s)

                # Use out_time_ms for progress
                out_time_ms = int(q[0]["out_time_ms"])
                
                # If out_time_ms is not available, use out_time in seconds
                if out_time_ms is None or out_time_ms < 0:
                    # Use out_time in seconds if out_time_ms is not available
                    out_time_ms = int(q[0]["out_time"] * 1000)
                
                # If we still don't have a valid out_time, skip this update
                if out_time_ms < last_current.value:
                    return
                
                # Update the last current time
                last_current.value = out_time_ms

                # GUI progress in ms
                FileManager_Utils.progress(last_current.value, total_duration_s * 1000, f"{action} {file_name}")

        # Initialize the shared queue for progress updates
        q = [{"out_time_ms": 0, "out_time": 0.0}]

        # Initialize progress reader thread
        progress_reader_thread = Thread(target=progress_reader, args=(process, q))
        # Start the thread
        progress_reader_thread.start()
        
        # Execute the progress bar
        progress_bar_execution("Compressing file", file_name, process, q, total_duration_s)