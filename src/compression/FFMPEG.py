import os
import shutil
import subprocess
from typing import List
import zipfile
import click
import requests

# Import constants from config
from config import FFMPEG_RELATIVE_PATH, FFPROBE_RELATIVE_PATH

class FFMPEG():
    """
    Class responsible for ensuring ffmpeg is installed and providing methods to call ffmpeg and 
    ffprobe commands
    """
    
    @staticmethod
    def ensure_ffmpeg() -> None:
        """
        Ensure ffmpeg is installed, if not download and install it
        
        Raises:
            FileNotFoundError: If ffmpeg could not be found or installed
        
        TODO I can add a simple file version check to see if ffmpeg is up to date
        """
        # Determine whether installation/update is needed: require all three executables
        ffplay_rel = os.path.join(os.path.dirname(FFMPEG_RELATIVE_PATH), 'ffplay.exe')
        need_install = not (
            os.path.exists(FFMPEG_RELATIVE_PATH) and 
            os.path.exists(FFPROBE_RELATIVE_PATH) and 
            os.path.exists(ffplay_rel)
        )

        # Check if ffmpeg folder exists or needs update
        if need_install:
            # Download and install ffmpeg
            print("Downloading ffmpeg...")

            target_dir = os.path.dirname(FFMPEG_RELATIVE_PATH)
            target_dir_abs = os.path.abspath(target_dir)
            dir_preexisting = os.path.exists(target_dir_abs)
            os.makedirs(target_dir_abs, exist_ok=True)

            zip_path = "ffmpeg.zip"
            temp_extract_dir = "ffmpeg_temp"
            try:
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
                    raise Exception("Expected ffmpeg executables not found in the zip")

                # Move binaries to target 'ffmpeg' folder
                for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                    shutil.move(os.path.join(bin_folder, exe), os.path.join(target_dir_abs, exe))

                # Cleanup
                shutil.rmtree(temp_extract_dir)
                os.remove(zip_path)

                print("ffmpeg installed successfully.")
            except Exception:
                # Best-effort cleanup of partial artifacts
                try:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                except Exception:
                    pass
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
                                p = os.path.join(target_dir_abs, exe)
                                if os.path.exists(p):
                                    os.remove(p)
                            except Exception:
                                pass
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
                raise
        
    @classmethod
    def __get_command_path(self, exe_path_json : str, exe_name : str) -> str:
        """
        Function for get the exe path
        This is designed to be used for find the ffmpeg and ffprobe file
            
        Args:
            exe_path_json: The environment variable name where the path is stored
            exe_name: The executable name to search
        Returns:
            str: The path of the executable
        """
        resultPath = None
        
        # Search in the current folder
        if os.path.exists(exe_name):
            # Set the path of the current folder
            resultPath = os.path.abspath(exe_name)
        else:
            # Let the user write the path
            exePath = str(click.prompt(f'{exe_name} not found. Write the path', err=True))
            if os.path.exists(exePath) and not os.path.isdir(exePath):
                # Set the path
                resultPath = exePath
            elif os.path.isdir(exePath) and os.path.exists(exePath + '\\' + exe_name):
                # Set the path
                resultPath = exePath + '\\' + exe_name
            else:
                # Re-ask
                self.__get_command_path(exe_path_json, exe_name)

            # Save the path on the environment variables
            os.environ[exe_path_json] = resultPath
        
        # Return the result path
        return resultPath

    @classmethod
    def call_ffmpeg(self, args : List[str]) -> subprocess.Popen:
        """
        Function for execute a ffmpeg command
        
        Args:
            args: The ffmpeg arguments
        Returns:
            subprocess.Popen: The ffmpeg process
        Raises:
            Exception: If ffmpeg command is not available
        """
        try:
            ffmpegScript = [self.__get_command_path("FFMPEG", FFMPEG_RELATIVE_PATH)] + args
            return subprocess.Popen(ffmpegScript, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        except FileNotFoundError:
            raise Exception('ffmpeg command is not available. Thumbnails for videos are not available!')
    
    @classmethod
    def call_ffprobe(self, args : List[str]) -> subprocess.Popen:
        """
        Function for execute a ffprobe command
        
        Args:
            args: The ffprobe arguments
        Returns:
            subprocess.Popen: The ffprobe process
        Raises:
            Exception: If ffprobe command is not available
        """
        try:
            ffprobeScript = [self.__get_command_path("FFPROBE", FFPROBE_RELATIVE_PATH)] + args
            return subprocess.Popen(ffprobeScript, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise Exception('ffprobe command is not available. Thumbnails for videos are not available!')
    
    '''
    @classmethod
    def ffmpeg_progress_bar(self, file : File, process, tot_n_frames : int):
        """
        Create the ffmpeg progress bar

        This is different from the normal progress bar as i use a thread for read the value from the process
            
        Args:
            file: The file object
            process: The ffmpeg process
            tot_n_frames: The total number of frames        
        """
        
        def progress_reader(procs, q):
            """
            Read the ffmpeg output frame number and save it
            
            Args:
                procs: The ffmpeg process
                q: The queue to store the frame number
            """
            while True:
                if procs.poll() is not None:
                    # Break if FFmpeg sun-process is closed
                    break
                
                # Read line from the pipe
                progress_text = procs.stdout.readline()

                # Break the loop if progress_text is None (when pipe is closed).
                if progress_text is None:
                    break

                # Look for "frame=xx"
                if progress_text.startswith("frame="):
                    # Get the frame number
                    frame = int(progress_text.partition('=')[2].partition('fps')[0])
                    # Store the last sample
                    q[0] = frame

        def progress_bar_execution(action, file : File, p, q, tot_n_frames : int, update_time_s : float = 1):
            """
            Execute the ffmpeg progress loop that updates every `update_time_s` seconds.

            Uses `FileManager_Utils.progress` (GUI if available) to display progress.
            Falls back to console printing if the GUI is unavailable.
            """
            last_current = c_int64(0)
            while True:
                if p.poll() is not None:
                    break  # Break if FFmpeg subprocess is closed

                # Wait for the update time
                time.sleep(update_time_s)

                # Read last element from progress_reader - current encoded frame
                n_frame = q[0]
                if n_frame < last_current.value:
                    return

                last_current.value = n_frame

                # Try GUI progress first, otherwise fallback to console
                try:
                    FileManager_Utils.progress(n_frame, tot_n_frames, f"{action} {file.file_name}")
                except Exception:
                    try:
                        pct = (n_frame / tot_n_frames) * 100 if tot_n_frames else 0.0
                    except Exception:
                        pct = 0.0
                    print(f"{pct:.2f}% {action} {file.file_name}")

        q = [0]

        # Initialize progress reader thread
        progress_reader_thread = Thread(target=progress_reader, args=(process, q))
        # Start the thread
        progress_reader_thread.start()
        
        # Execute the progress bar
        progress_bar_execution("Compressing file", file, process, q, tot_n_frames)
        
        '''