import getpass
import click
import click

from config import BOT_USER_MAX_FILE_SIZE, PREMIUM_USER_MAX_CAPTION_LENGTH, PREMIUM_USER_MAX_FILE_SIZE, USER_MAX_CAPTION_LENGTH, USER_MAX_FILE_SIZE

from telethon import TelegramClient
from telethon.errors import ApiIdInvalidError

from utils import phone_match

class TelegramManagerClient(TelegramClient):
    """
        A Telegram client that manages user sessions and provides easy access to user properties.
        This client is designed to be used with the Telethon library and provides additional functionality
        such as automatic session management, user information retrieval, and file size limits based on user type
        (regular user, bot, or premium user).
        
    Args:
        session (str): The session name or path.
        api_id (int): The API ID for the Telegram application.
        api_hash (str): The API hash for the Telegram application.
    """
    
    def __init__(self, session : str, api_id : int, api_hash : str):
        """
        Initializes the TelegramManagerClient with the given session, API ID, and API hash.

        Args:
            session (str): The session name or path
            api_id (int): The API ID for the Telegram application
            api_hash (str): The API hash for the Telegram application
        """
        super().__init__(session, api_id, api_hash)
        # Internal variable to store user informations
        self._me = None
    
    def start(
        self,
        phone=lambda: click.prompt('Please enter your phone', type= phone_match),
        password=lambda: getpass.getpass('Please enter your password: '),
        *,
        bot_token=None, 
        force_sms=False, 
        code_callback=None,
        first_name='New User', 
        last_name='', 
        max_attempts=3):
        """
            Starts the Telegram client session, prompting for phone number and password if not provided.
            This method handles the authentication process and initializes the client.
            
            I use this instead of the parent start method to catch the ApiIdInvalidError, check phone and raise a more user-friendly exception.
            
            Args:
                phone (callable): A callable that returns the phone number. Defaults to prompting the user.
                password (callable): A callable that returns the password. Defaults to prompting the user.
                bot_token (str): The bot token if starting a bot session.
                force_sms (bool): Whether to force SMS verification.
                code_callback (callable): A callback function for handling the verification code.
                first_name (str): The first name of the user.
                last_name (str): The last name of the user.
                max_attempts (int): The maximum number of attempts for authentication.
            Returns:
                The Telegram client instance after successful authentication.
            Raises:
                Exception: If the API ID is invalid or if the client fails to start.
            """
        try:
            return super().start(phone=phone, password=password, bot_token=bot_token, force_sms=force_sms,
                                 first_name=first_name, last_name=last_name, max_attempts=max_attempts)
        except ApiIdInvalidError:
            raise Exception(self.config_file)
        
    async def initialize(self):
        """
            Initializes the Telegram client by connecting to the Telegram servers and retrieving user informations.
            This method should be called after the client is started to ensure that user informations are available.
        """
        self._me = await self.get_me()
        
    @property
    def me(self):
        if self._me is None:
            raise Exception("Client not initialized. Call initialize() first.")
        return self._me
    
    @property
    def max_file_size(self):
        """ 
            Returns the maximum file size allowed for uploads based on user type.
            - Premium users have a higher limit.
            - Bot users have a specific limit.
            - Regular users have a standard limit.
        """
        if hasattr(self.me, 'premium') and self.me.premium:
            return PREMIUM_USER_MAX_FILE_SIZE
        elif self.me.bot:
            return BOT_USER_MAX_FILE_SIZE
        else:
            return USER_MAX_FILE_SIZE

    @property
    def max_caption_length(self):
        """ 
            Returns the maximum caption length allowed for messages based on user type.
            - Premium users have a higher limit.
            - Regular users have a standard limit.
        """
        if hasattr(self.me, 'premium') and self.me.premium:
            return PREMIUM_USER_MAX_CAPTION_LENGTH
        else:
            return USER_MAX_CAPTION_LENGTH