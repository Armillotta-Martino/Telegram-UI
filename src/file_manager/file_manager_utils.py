import asyncio
import json
from xml.dom.minidom import Entity
import click

from config import RECONNECT_TIMEOUT
from dbJson.file_message import FileMessage
from telegram.telegram_manager_client import TelegramManagerClient

from ui.pop_up_progress_bar import PopUp_Progress_Bar

class FileManager_Utils:
    """
    Utility functions for the file manager
    """
    
    @staticmethod
    async def reconnect(
        client : TelegramManagerClient, 
        reconnecting_lock : asyncio.Lock, 
        upload_semaphore : asyncio.Semaphore
        ) -> None:
        """
        Reconnects to Telegram servers
        
        This function is used to reconnect to Telegram servers when the connection is lost
        It uses a lock to prevent multiple reconnection at the same time
            
        Args:
            client: The Telegram client to reconnect
            reconnecting_lock: A lock to prevent multiple reconnection at the same time
            upload_semaphore: A semaphore to limit the number of parallel uploads
        Raises:
            Exception: If the reconnection fails
        """
        
        # Acquire the lock
        await reconnecting_lock.acquire()
        
        # Check if the client is already connected
        if client.is_connected():
            # Reconnected in another task
            reconnecting_lock.release()
            return
        
        # Decreases the upload semaphore by one
        if upload_semaphore._value > 1:
            client.loop.create_task(upload_semaphore.acquire())
            
        try:
            # Reconnect to Telegram servers
            click.echo('Reconnecting to Telegram servers...')
            await asyncio.wait_for(client.connect(), RECONNECT_TIMEOUT)
            click.echo('Reconnected to Telegram servers.')
        except Exception:
            click.echo('InvalidBufferError connecting to Telegram servers.', err=True)
        except asyncio.TimeoutError:
            click.echo('Timeout connecting to Telegram servers.', err=True)
        finally:
            reconnecting_lock.release()
    
    @staticmethod
    async def send_telegram_message(
        client : TelegramManagerClient, 
        target_chat_instance: Entity, 
        message_json : dict[str, any]
        ) -> FileMessage:
        """
        Send a telegram message with a JSON content
        
        Args:
            client: The telegram client to use
            target_chat_instance: The chat to send the message to
            message_json: The JSON content of the message
        Returns:
            FileMessage: The sent message wrapped in a FileMessage object
        Raises:
            TypeError: If the message_json is not a dict
        """
        # Validate input
        if not isinstance(message_json, dict):
            raise TypeError(
                f"__send_telegram_message expects a JSON dict, got {type(message_json).__name__}"
            )
        
        # Convert dict to JSON string
        json_text = json.dumps(message_json, ensure_ascii=False, indent=4)

        # Send message
        telegram_message = await client.send_message(
            entity=target_chat_instance, 
            message=json_text
        )
        
        # Wrap in FileMessage
        return FileMessage(telegram_message)
        
    @staticmethod 
    def progress(
        sent : int, 
        total : int, 
        text: str = ""
        ) -> None:
        """
        Callback function to show the progress
        
        Args:
            sent: The number of bytes processed
            total: The total number of bytes
            text: Additional text to show in the progress bar
        """
        # Guard division
        try:
            pct = sent / total * 100
        except Exception:
            pct = 0.0

        # Show GUI progress if possible
        win = PopUp_Progress_Bar.instance()
        win.update(pct, text)