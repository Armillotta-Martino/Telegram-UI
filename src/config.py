import json
import os
import click

# -------------------------------------
# Versions
# I put versions here to be able to handle changes in the future
# -------------------------------------

# Version of the caption
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

BOT_USER_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
USER_MAX_FILE_SIZE = 2 * 1000 * 1024 * 1024  # 2000MB
LRV_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500GB
#USER_MAX_FILE_SIZE = 52428800  # 50MB
PREMIUM_USER_MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
USER_MAX_CAPTION_LENGTH = 1024
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

def prompt_config(
    config_file : str
    ):
    """
    Create the file in the directory and write the API config
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