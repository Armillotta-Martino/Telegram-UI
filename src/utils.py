import os
import re
import shutil
import json

import click

class Utils:
    @staticmethod
    def free_disk_usage(directory : str = '.') -> int:
        """
        Get the free disk usage in bytes
        
        Args:
            directory (str): The directory to check the disk usage for. Defaults to current directory.
        Returns:
            int: The free disk usage in bytes
        """
        return shutil.disk_usage(directory)[2]

    @staticmethod
    def size_value_to_human(num : int, suffix : str = 'B') -> str:
        """
        Convert a size in bytes to a human readable format
        
        TODO Not used
        
        Args:
            num (int): The size in bytes
            suffix (str): The suffix to append to the size. Defaults to 'B'.
        Returns:
            str: The size in a human readable format
        """
        for unit in ['','K','M','G','T','P','E','Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)

    @staticmethod
    def phone_match(value: str) -> str:
        """
        Validate if the given string is a valid phone number format
        
        Args:
            value (str): The phone number string to validate
        Returns:
            str: The validated phone number string
        Raises:
            ValueError: If the string is not a valid phone number format
        """
        match = re.match(r'\+?[0-9.()\[\] \-]+', value)
        if match is None:
            raise ValueError('{} is not a valid phone'.format(value))
        return value

    @staticmethod
    def get_environment_value(environment_name: str, default_value):
        """
        Get an environment variable from .env or system and convert it to the same type as default_value
        
        Args:
            environment_name: The name of the environment variable
            default_value: The default value to return if the environment variable is not set
        Returns:
            The value of the environment variable converted to the same type as default_value
        Raises:
            Exception: If the environment variable cannot be converted to the same type as default_value
        """
        # Get raw value
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
                try:
                    return json.loads(raw_value)
                except Exception:
                    raise Exception(
                        f"Cannot convert {environment_name}='{raw_value}' to {target_type.__name__}"
                    )

        except Exception as e:
            raise Exception(
                f"Environment variable {environment_name} must be of type {target_type.__name__}, got '{raw_value}'"
            ) from e

'''
    @staticmethod      
    def prompt_config(config_file : str) -> str:
        """
        Create the file in the directory and write the API config
        
        TODO Not used as the config file is created manually for now, but this can be useful in the future to create a CLI command to create the config file
        
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
'''