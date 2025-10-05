from ctypes import c_int64
import json
import os
import re
import shutil
import subprocess
from threading import Thread
import time
from typing import List
import zipfile
import click

from typing import TYPE_CHECKING

import requests
if TYPE_CHECKING:
    from video import Video

# FFMPEG
FFMPEG_NAME = "ffmpeg.exe"
FFMPEG_PATH_JSON = "ffmpegPath"
# FFPROBE
FFPROBE_NAME = "ffprobe.exe"
FFPROBE_PATH_JSON = "ffprobePath"

class FFMPEG():
    @staticmethod
    def ensure_ffmpeg():
        ffmpeg_dir = "ffmpeg"
        if not os.path.exists(os.path.join(ffmpeg_dir, "ffmpeg.exe")):
            print("Downloading ffmpeg...")
            os.makedirs(ffmpeg_dir, exist_ok=True)

            # Download zip
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            r = requests.get(url, stream=True)
            zip_path = "ffmpeg.zip"
            with open(zip_path, "wb") as f:
                f.write(r.content)

            # Extract zip
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall("ffmpeg_temp")

            # Find the bin folder dynamically
            bin_folder = None
            for root, dirs, files in os.walk("ffmpeg_temp"):
                if "ffmpeg.exe" in files:
                    bin_folder = root
                    break

            if not bin_folder:
                raise FileNotFoundError("Could not find ffmpeg.exe in the extracted zip!")

            # Move binaries to 'ffmpeg' folder
            for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                shutil.move(os.path.join(bin_folder, exe), os.path.join(ffmpeg_dir, exe))

            # Cleanup
            shutil.rmtree("ffmpeg_temp")
            os.remove(zip_path)

            print("ffmpeg installed successfully.")
        
    @classmethod
    def __get_command_path(
        self, 
        exe_path_json : str, 
        exe_name : str
        ):
        """
            Function for get the exe path
            This is designed to be used for find the ffmpeg and ffprobe file
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

            # Save the path on the enviroment variables
            os.environ[exe_path_json] = resultPath
        
        # Return the result path
        return resultPath

    @classmethod
    def call_ffmpeg(
        self, 
        args : List[str]
        ):
        """
            Function for execute a ffmpeg command
        """
        try:
            ffmpegScript = [self.__get_command_path(FFMPEG_PATH_JSON, FFMPEG_NAME)] + args
            return subprocess.Popen(ffmpegScript, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        except FileNotFoundError:
            raise Exception('ffmpeg command is not available. Thumbnails for videos are not available!')
    
    @classmethod
    def call_ffprobe(
        self, 
        args : List[str]
        ):
        """
            Function for execute a ffprobe command
        """
        try:
            ffprobeScript = [self.__get_command_path(FFPROBE_PATH_JSON, FFPROBE_NAME)] + args
            return subprocess.Popen(ffprobeScript, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise Exception('ffprobe command is not available. Thumbnails for videos are not available!')

    @classmethod
    def get_ffprobe_file_details(
        self, 
        file : 'Video'
        ):
        """
            Get the file details using ffprobe

            Args:
                file (Video): _description_

            Returns:
                _type_: _description_
        """
        # ffprobe call for get the file info as json
        p = self.call_ffprobe([
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file.path
        ])
        jsonResult = json.loads(p.communicate()[0].decode('utf-8'))
        
        # DEBUG print(jsonResult)

        # Format the result
        streams = []
        # Save the informations i need
        for s in jsonResult['streams']:
            stream = {}
            stream["index"] = s['index']
            if 'codec_name' in s:
                stream["codec_name"] = s['codec_name']
            if 'codec_long_name' in s:
                stream["codec_long_name"] = s['codec_long_name']
            if 'codec_type' in s:
                stream["codec_type"] = s['codec_type']
            if 'codec_tag_string' in s:
                stream["codec_tag_string"] = s['codec_tag_string']
            if 'duration' in s:
                stream["duration"] = s['duration']
            if 'bit_rate' in s:
                stream["bit_rate"] = s['bit_rate']
            if 'tags' in s:
                if 'creation_time' in s['tags']:
                    stream["creation_time"] = s['tags']['creation_time']

            # Only video info
            if 'width' in s:
                stream["width"] = s['width']
            if 'height' in s:
                stream["height"] = s['height']
            if 'display_aspect_ratio' in s:
                stream["display_aspect_ratio"] = s['display_aspect_ratio']
            if 'r_frame_rate' in s:
                stream["r_frame_rate"] = s['r_frame_rate']
            if 'avg_frame_rate' in s:
                stream["avg_frame_rate"] = s['avg_frame_rate']
            if 'bits_per_raw_sample' in s:
                stream["bits_per_raw_sample"] = s['bits_per_raw_sample']

            # Only audio info
            if 'sample_fmt' in s:
                stream["sample_fmt"] = s['sample_fmt']
            if 'sample_rate' in s:
                stream["sample_rate"] = s['sample_rate']

            # Only image info
            if 'pix_fmt' in s:
                stream["pix_fmt"] = s['pix_fmt']
            if 'color_range' in s:
                stream["color_range"] = s['color_range']
            if 'color_space' in s:
                stream["color_space"] = s['color_space']
            if 'chroma_location' in s:
                stream["chroma_location"] = s['chroma_location']

            # Add stream to streams list
            streams.append(stream)

        format = {}
        if 'format' in jsonResult:
            if 'filename' in jsonResult['format']:
                format["filename"] = jsonResult['format']['filename']

            # Only image info
            if 'format_name' in jsonResult['format']:
                format["format_name"] = jsonResult['format']['format_name']
            if 'format_long_name' in jsonResult['format']:
                format["format_long_name"] = jsonResult['format']['format_long_name']

            if 'size' in jsonResult['format']:
                format["size"] = jsonResult['format']['size']
            if 'bit_rate' in jsonResult['format']:
                format["bit_rate"] = jsonResult['format']['bit_rate']
            if 'tags' in jsonResult['format']:
                if 'major_brand' in jsonResult['format']:
                    format["major_brand"] = jsonResult['format']['tags']['major_brand']
                if 'creation_time' in jsonResult['format']:
                    format["creation_time"] = jsonResult['format']['tags']['creation_time']

        result = {
            "streams": streams,
            "format": format
        }
        return result
    
    @classmethod
    def ffmpeg_progress_bar(
        self, 
        file : 'Video', 
        process, 
        tot_n_frames : int
        ):
        """
            Create the ffmpeg progress bar

            This is different from the normal progress bar as i use a thread for read the value from the process
        """
        def progress_reader(procs, q):
            """
            Read the ffmpeg output frame number and save it
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

        def progress_bar_execution(action, file, p, q, tot_n_frames : int, update_time_s = 1):
            """
            Execute the ffpeg progress bar that update every 1s
            """
            bar = click.progressbar(label='{} "{}"'.format(action, file.file_name), length=tot_n_frames)
            last_current = c_int64(0)
            while True:
                if p.poll() is not None:
                    break  # Break if FFmpeg sun-process is closed

                time.sleep(update_time_s)  # Sleep 1 second (do some work...)

                n_frame = q[0]  # Read last element from progress_reader - current encoded frame
                if n_frame < last_current.value:
                    return
                bar.pos = 0
                bar.update(n_frame)
                last_current.value = n_frame

            bar.render_finish()

        q = [0]

        # Initialize progress reader thread
        progress_reader_thread = Thread(target=progress_reader, args=(process, q))
        # Start the thread
        progress_reader_thread.start()

        progress_bar_execution("Compressing video", file, process, q, tot_n_frames)
    
    def get_video_resolution(
        video : 'Video'
        ):
        """
            Get the video resolution using ffprobe

            Args:
                video (Video): _description_

            Returns:
                _type_: _description_
        """
        
        p = FFMPEG.call_ffmpeg([
            '-i', video.path,
        ])
        stdout, stderr = p.communicate()
        video_lines = re.findall(': Video: ([^\n]+)', stdout)
        
        if not video_lines:
            return
        
        matchs = re.findall("(\d{2,6})x(\d{2,6})", video_lines[0])
        if matchs:
            return [int(x) for x in matchs[0]]