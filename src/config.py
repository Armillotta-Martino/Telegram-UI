import json
import os
import click

from dotenv import load_dotenv

# Reads .env and sets environment variables
load_dotenv()

from utils import get_environment_value

### Required Telegram Configurations
# Telegram channel name where to upload the files
CHANNEL_NAME = get_environment_value('TELEGRAM_UPLOAD_CHANNEL_NAME', '')
# Telegram API ID and Hash
API_ID = get_environment_value('TELEGRAM_UPLOAD_API_ID', -1)
# Telegram API Hash
API_HASH = get_environment_value('TELEGRAM_UPLOAD_API_HASH', '')

### Optional Telegram Configurations
# Number of parallel upload blocks
PARALLEL_UPLOAD_BLOCKS = get_environment_value('TELEGRAM_UPLOAD_PARALLEL_UPLOAD_BLOCKS', 4)
# Number of parallel download blocks
PARALLEL_DOWNLOAD_BLOCKS = get_environment_value('TELEGRAM_UPLOAD_PARALLEL_DOWNLOAD_BLOCKS', 10)
# Max number of retries for reconnect
MAX_RECONNECT_RETRIES = get_environment_value('TELEGRAM_UPLOAD_MAX_RECONNECT_RETRIES', 5)
# Reconnect timeout
RECONNECT_TIMEOUT = get_environment_value('TELEGRAM_UPLOAD_RECONNECT_TIMEOUT', 5)
# Time to wait before retry to connect
MIN_RECONNECT_WAIT = get_environment_value('TELEGRAM_UPLOAD_MIN_RECONNECT_WAIT', 5)

# I decided to write those values in the env file and other fixed Telegram constants here as constants because
# the Telegram constants are not going to change often, while the env values can be changed by the user if needed

# -------------------------------------
# Constants
# Fixed constants used in the code
# -------------------------------------

### Compression Constants

# FFMPEG Executable
FFMPEG_RELATIVE_PATH = "ffmpeg/ffmpeg.exe"
# FFPROBE Executable
FFPROBE_RELATIVE_PATH = "ffmpeg/ffprobe.exe"

### UI Constants

# Folder icon path
ICON_FOLDER_PATH = "icons/folder.png"
# File icon path
ICON_FILE_PATH = "icons/file.png"

# -------------------------------------
# Versions
# I put versions here to be able to handle changes in the future
# Example: If I change the caption format, I can increase the version and handle both versions in the code
# -------------------------------------

"""
Schema explanation:

Caption:
{
    "Version": FILE_CAPTION_VERSION,
    "Type": FileMessageType.ROOT.value,
    "Name": file_name,
    "Children": []
}
"""

### Current Versions

# This is the version of the file message caption
FILE_CAPTION_VERSION = 1
# Version of the full description
FILE_FULL_DESCRIPTION_VERSION = 1
# Version of the generic caption
FILE_GENERIC_CAPTION_VERSION = 1
# Version of the low resolution caption
LOW_RESOLUTION_FILE_CAPTION_VERSION = 1
# Version of the file part caption
FILE_PART_CAPTION_VERSION = 1


# -------------------------------------
# Telegram
# Telegram limits and constants
# -------------------------------------

# Max bot file size
BOT_USER_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
# Max user file size
USER_MAX_FILE_SIZE = 2 * 1000 * 1024 * 1024  # 2000MB
#USER_MAX_FILE_SIZE = 52428800  # 50MB, for testing
# Max low resolution file size
LRV_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
# Max premium user file size
PREMIUM_USER_MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
# Max part file size in KB
PART_MAX_SIZE = 512 * 1024  # 512KB
# Small file threshold
SMALL_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB

# Chunk sizes for upload.getFile must be multiples of the smallest size
MIN_CHUNK_SIZE = 4096
MAX_CHUNK_SIZE = 512 * 1024

# Max caption length
USER_MAX_CAPTION_LENGTH = 1024
# Max premium user caption length
PREMIUM_USER_MAX_CAPTION_LENGTH = 2 * 1024
# Telegram max files per album
ALBUM_FILES = 10
# Number of retries for upload
RETRIES = 3

# -------------------------------------
# Inputs
# Inputs the user has to insert
# TODO Maybe move to env
# -------------------------------------

def prompt_config(config_file : str) -> str:
    """
    Create the file in the directory and write the API config
    
    Args:
        config_file: Path to the config file
    Returns:
        The config file path
    """
    # Create the dir
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    click.echo('Go to https://my.telegram.org and create a App in API development tools')
    # Telegram API id
    api_id = click.prompt('Please Enter api_id', type=int)
    # Telegram API hash
    api_hash = click.prompt('Now enter api_hash')

    # Save the values on the json
    with open(config_file, 'w') as f:
        json.dump({'api_id': api_id, 'api_hash': api_hash}, f)

    # Return the config file path
    return config_file