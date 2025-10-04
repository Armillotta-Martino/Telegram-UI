import os
import re
import shutil
from telegram_upload.exceptions import TelegramEnvironmentError

def free_disk_usage(
    directory : str = '.'
    ) -> int:
    """
    Get total disk free space
    """
    return shutil.disk_usage(directory)[2]

def size_value_to_human(
    num : int, 
    suffix : str = 'B'
    ) -> str:
    """
    Convert file size to a more human readable way
    """
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def phone_match(
    value: str
    ) -> str:
    """
    Validate a phone number

    Args:
        value (_type_): _description_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    match = re.match(r'\+?[0-9.()\[\] \-]+', value)
    if match is None:
        raise ValueError('{} is not a valid phone'.format(value))
    return value

def get_environment_value(environment_name: str, default_value):
    """
    Get an environment variable from .env or system and convert it
    to the same type as default_value.
    """
    raw_value = os.getenv(environment_name)

    # If not found, return default
    if raw_value is None:
        return default_value

    target_type = type(default_value)

    # Try to convert depending on type
    try:
        if target_type is bool:
            return raw_value.lower() in ("1", "true", "yes", "on")

        elif target_type is int:
            return int(raw_value)

        elif target_type is float:
            return float(raw_value)

        elif target_type is str:
            return raw_value

        else:
            # Optional: try to eval or JSON parse for custom types
            import json
            try:
                return json.loads(raw_value)
            except Exception:
                raise TelegramEnvironmentError(
                    f"Cannot convert {environment_name}='{raw_value}' to {target_type.__name__}"
                )

    except Exception as e:
        raise TelegramEnvironmentError(
            f"Environment variable {environment_name} must be of type {target_type.__name__}, got '{raw_value}'"
        ) from e