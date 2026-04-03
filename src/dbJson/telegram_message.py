from enum import Enum
import json
import re
from xml.dom.minidom import Entity

from telethon.tl.custom.message import Message
from telegram.telegram_manager_client import TelegramManagerClient

from config import FILE_CAPTION_VERSION

class TelegramMessageType(Enum):
    """
    Enum representing the type of file message
    """
    
    ROOT = "ROOT"
    FOLDER = "FOLDER"
    FILE = "FILE"
    LRV = "LRV"
    THUMBNAIL = "THUMBNAIL"

class TelegramMessage(Message):
    """
    Class representing a file message in the telegram database
    One message on telegram represents one instance of this class
        
    Args:
        message (Message): Telegram message data
    """
    
    ### Private members
    
    # The telegram message
    __message: Message
    # The file message type
    __type: TelegramMessageType
    
    def __init__(self, message: Message) -> None:
        """
        Initialize a TelegramMessage instance
        
        Args:
            message (Message): Telegram message data
        Returns:
            None
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Type
        """
        
        # Validate message type
        if not isinstance(message, Message):
            raise ValueError("Invalid message type. Expected a Message instance.")
        
        if not message.message:
            raise ValueError("Message is empty or has no text")
        
        # TODO Validate if the text message is a valid JSON and contains the required fields (Version, Type, Name, etc.) before trying to parse it
        
        # Infer type from the message text
        json_message = json.loads(message.message)
        if "Type" not in json_message:
            raise ValueError("Message does not contain Type")
        
        # Save the message
        self.__message = message
        # Set the type
        self.__type = TelegramMessageType(str(json_message["Type"]).upper())

    @property
    def telegram_message(self) -> Message:
        """
        Get the telegram message
            
        I decided to use the name telegram_message instead of message to avoid confusion with the base 
        Message class message property
        
        Returns:
            Message: The telegram message
        """
        # NOTE: Here the validity method cannot be used because it relies on the telegram_message property, which is what we 
        # are trying to access, so we need to check the validity of the message in a different way
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        return self.__message
    
    @property
    def type(self) -> TelegramMessageType:
        """
        Get the file message type
        
        Returns:
            TelegramMessageType: The type of the file message
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Return type
        return self.__type
        
    @property
    def is_folder(self) -> bool:
        """
        Check if the message is a folder
        
        Returns:
            bool: True if the message is a folder, False otherwise
        Raises:
            ValueError: If the message is empty, has no text or does not contain Type
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.telegram_message.message)
        
        # Check type
        if "Type" not in json_message:
            raise ValueError("Message does not contain Type")
        
        # Return true if folder or root
        return json_message["Type"] == TelegramMessageType.FOLDER.value or \
               json_message["Type"] == TelegramMessageType.ROOT.value
        
    @property
    def version(self) -> str:
        """
        Get the version of the file message
        
        Returns:
            str: The version of the file message
        Raises:
            ValueError: If the message is empty, has no text or does not contain Version
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.telegram_message.message)
        
        # Check version
        if "Version" not in json_message:
            raise ValueError("Message does not contain Version")
        
        # Return version
        return str(json_message["Version"])
    
    @property
    def file_name(self) -> str:
        """
        Get the file name from the message
        
        Returns:
            str: The file name from the message
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Name
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.telegram_message.message)
        
        # Check name
        if "Name" not in json_message:
            raise ValueError("Message does not contain Name")
        
        # Return name
        return str(json_message["Name"])
    
    @property
    def extension(self) -> str:
        """
        Get the file extension from the file name
        
        Returns:
            str: The file extension
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Split the file name by dot
        split_name = self.file_name.rsplit('.', 1)
        # Check if there is an extension
        if len(split_name) == 2:
            return split_name[1]
        else:
            return ""
    
    @property
    def short_name(self) -> str:
        """
        Get the file name without the extension
        
        Returns:
            str: The file name without the extension
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Split the file name by dot
        split_name = self.file_name.rsplit('.', 1)
        # Return the name without extension
        return split_name[0]
    
    @property
    def file_size(self) -> str:
        """
        Get the size of the document attached to the message
        
        # TODO NOTE This can be changed to use the main message, scan all the comments and sum all the sizes of the attached documents of the comments (when not LRV or THUMBNAIL)
        
        Returns:
            str: The size of the document
        """
        
        # TODO Check and test
        
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        # Try several common locations where Telethon stores media size
        msg = self.telegram_message

        # Document (most common for files)
        doc = getattr(msg, 'document', None) or (getattr(msg, 'media', None) and getattr(msg.media, 'document', None))
        if doc and getattr(doc, 'size', None) is not None:
            return int(doc.size)

        # Photo sizes: pick the largest available size
        photo = getattr(msg, 'photo', None)
        if photo:
            sizes = getattr(photo, 'sizes', None) or getattr(photo, 'photosizes', None)
            if sizes:
                max_size = 0
                for s in sizes:
                    if getattr(s, 'size', None) is not None:
                        max_size = max(max_size, int(s.size))
                    elif getattr(s, 'bytes', None) is not None:
                        max_size = max(max_size, int(s.bytes))
                if max_size:
                    return max_size

        # Video / audio / other media: try common fields
        media = getattr(msg, 'media', None)
        if media:
            for attr in ('file_size', 'size'):
                val = getattr(media, attr, None)
                if val is not None:
                    return int(val)

        # Some Message wrappers expose shortcuts like .video
        for field in ('video', 'audio'):
            m = getattr(msg, field, None)
            if m:
                for attr in ('file_size', 'size'):
                    val = getattr(m, attr, None)
                    if val is not None:
                        return int(val)

        # Not found
        raise ValueError('No attached media with a size was found in the message')
    
    # region Message relations methods
    
    async def get_parent(self, client : TelegramManagerClient) -> 'TelegramMessage':
        """
        Get the parent message of the current message
        
        Args:
            client (TelegramManagerClient): Telegram manager client
        Returns:
            TelegramMessage: The parent message
        Raises:
            ValueError: If the message is empty, has no text or does not contain Parent
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        # Parse the message
        json_message = json.loads(self.telegram_message.message)
        
        # Check parent
        if "Parent" not in json_message:
            raise ValueError("Message does not contain Parent")
        
        # Get the parent message from the link
        return await self.get_TelegramMessage_from_link(client, json_message["Parent"])
    
    async def get_children(self, client : TelegramManagerClient) -> list['TelegramMessage']:
        """
        Get the children messages of the current message
        
        Those are the messages linked in the Children field of the message JSON, which should be a list of telegram message links
        NOT the messages that are replying to the current message (those can be retrieved with get_comments_by_type method)
        
        Args:
            client (TelegramManagerClient): Telegram manager client
        Returns:
            list[TelegramMessage]: The list of children messages
        Raises:
            ValueError: If the message is empty, has no text or does not contain Children
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        # Parse the message
        json_message = json.loads(self.telegram_message.message)
        
        # Check children
        if "Children" not in json_message:
            raise ValueError("Message does not contain Children list")
        
        # Get children
        children_messages_list : list[TelegramMessage] = []
        for child_link in json_message["Children"]:
            # Get the child message from the link
            child_message = await self.get_TelegramMessage_from_link(client, child_link)
            children_messages_list.append(child_message)
        
        # Return children
        return children_messages_list
    
    async def get_children_by_file_name(self, client : TelegramManagerClient, name : str) -> list['TelegramMessage']:
        """
        Get the children messages of the current message that match a specific file name
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            name (str): The file name to filter children messages by
        Returns:
            list[TelegramMessage]: The list of children messages that match the file name
        Raises:
            ValueError: If the message is empty, has no text or does not contain Children
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        # Get all children
        children = await self.get_children(client)
        
        # Filter children by name
        filtered_children = [child for child in children if child.file_name == name]
        
        # Return filtered children
        return filtered_children
    
    async def add_children(self, client : TelegramManagerClient, chat_instance : Entity, message_link : str) -> None:
        """
        Add a child message link to the current message
        
        Add a link to the message as a child of the current message
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_instance (Entity): Chat instance
            message_link (str): Message link to add to the children
        Returns:
            None
        Raises:
            ValueError: If the message is empty or has no text
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        if not TelegramMessage.__valid_chat_entity(chat_instance):
            raise ValueError("Chat instance is empty or invalid")
        
        if not TelegramMessage.__valid_message_link(message_link):
            raise ValueError("Invalid message link format. Expected format: 'https://t.me/c/<chat_id>/<message_id>' or 'https://t.me/<username>/<message_id>'")
        
        # Check message link format (should be something like "https://t.me/c/123456789/123" or "https://t.me/username/123")
        if not re.match(r"^https://t\.me/(c/\d+/)?\d+$", message_link):
            raise ValueError("Invalid message link format. Expected format: 'https://t.me/c/<chat_id>/<message_id>' or 'https://t.me/<username>/<message_id>'")
        
        # Parse the message
        json_message = json.loads(self.telegram_message.message)
        # Add link to the children
        json_message['Children'].append(message_link)
        # Convert back to json string
        json_message = json.dumps(json_message, indent=4)
        # Edit the message
        await client.edit_message(chat_instance, self.telegram_message, json_message)
        
    async def remove_children(self, client : TelegramManagerClient, chat_instance : Entity, message_link : str) -> None:
        """
        Remove a child message link from the current message
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_instance (Entity): Chat instance
            message_link (str): Message link to remove from the children
        Returns:
            None
        Raises:
            ValueError: If the message is empty, has no text or does not contain Children
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        if not TelegramMessage.__valid_chat_entity(chat_instance):
            raise ValueError("Chat instance is empty or invalid")
        
        if not TelegramMessage.__valid_message_link(message_link):
            raise ValueError("Invalid message link format. Expected format: 'https://t.me/c/<chat_id>/<message_id>' or 'https://t.me/<username>/<message_id>'")

        # Parse the message
        json_message = json.loads(self.telegram_message.message)

        # Remove link from the children
        for c in json_message['Children']:
            if c == message_link:
                json_message["Children"].remove(c)
        
        # Convert back to json string
        json_message = json.dumps(json_message, indent=4)
        # Edit the message
        await client.edit_message(chat_instance, self.telegram_message, json_message)
    
    # endregion
    
    async def get_comments(self, client : TelegramManagerClient, chat_instance : Entity) -> list['TelegramMessage']:
        """
        Get the comments of the current message
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_instance (Entity): Chat instance
        Returns:
            list[TelegramMessage]: The list of comments (messages replying to the current message)
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        if not TelegramMessage.__valid_chat_entity(chat_instance):
            raise ValueError("Chat instance is empty or invalid")
        
        comments = []
        
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(chat_instance, reply_to=self.telegram_message.id):
            # Add the message as a comment
            comments.append(TelegramMessage(message))
        
        # Return comments
        return comments
    
    async def get_comments_by_type(self, client : TelegramManagerClient, chat_instance : Entity, type : TelegramMessageType) -> list['TelegramMessage']:
        """
        Get the comments of the current message that match a specific type
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_instance (Entity): Chat instance
            type (TelegramMessageType): The type to filter children messages by
        Returns:
            list[TelegramMessage]: The list of children messages that match the type
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")

        if not TelegramMessage.__valid_chat_entity(chat_instance):
            raise ValueError("Chat instance is empty or invalid")
        
        if not isinstance(type, TelegramMessageType):
            raise ValueError("Invalid type. Expected a TelegramMessageType instance.")
        
        filtered_comments = []
        
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(chat_instance, reply_to=self.telegram_message.id):
            # Find the file message
            json_message = json.loads(message.message)
            if json_message.get("Type") is not None and json_message.get("Type") == type.value:
                filtered_comments.append(TelegramMessage(message))
        
        # Return filtered comments
        return filtered_comments
    
    async def refresh(self, client : TelegramManagerClient, chat_instance : Entity) -> None:
        """
        Refresh the telegram message data
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            chat_instance (Entity): Chat instance
        Returns:
            None
        """
        if not TelegramMessage.__valid_message(self):
            raise ValueError("Message is empty or has no text")
        
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        if not TelegramMessage.__valid_chat_entity(chat_instance):
            raise ValueError("Chat instance is empty or invalid")
        
        # Get the updated message
        # NOTE: The telegram_message property is read-only, so we need to use the private member to update it
        # I plan it like this to avoid accidentally changing the message from outside the class
        self.__message = await client.get_messages(chat_instance, ids=self.telegram_message.id)
    
    @staticmethod
    def calculate_message_link(chat : Entity, message : 'TelegramMessage') -> str:
        """
        Calculate the link to a message in a channel or group
        
        Args:
            chat (Entity): The chat entity (channel or group)
            message (TelegramMessage): The message to calculate the link for
        Returns:
            str: The link to the message
        """

        if not TelegramMessage.__valid_chat_entity(chat):
            raise ValueError("Chat instance is empty or invalid")
        
        if not TelegramMessage.__valid_message(message):
            raise ValueError("Message is empty or has no text")
        
        if hasattr(chat, 'username') and chat.username:
            # Public channel/group
            link = f"https://t.me/{chat.username}/{message.telegram_message.id}"
        else:
            # Private channel/group
            
            # remove -100 prefix
            internal_id = str(chat.id).replace('-100', '')
            link = f"https://t.me/c/{internal_id}/{message.telegram_message.id}"
        
        return link
    
    @staticmethod
    async def get_TelegramMessage_from_link(client : TelegramManagerClient, message_link : str) -> 'TelegramMessage':
        """
        Get a TelegramMessage instance from a telegram message link
        
        Args:
            client (TelegramManagerClient): Telegram manager client
            message_link (str): Telegram message link
        Returns:
            TelegramMessage: TelegramMessage instance
        Raises:
            ValueError: If the message link format is unsupported or invalid
        """
        if not TelegramMessage.__valid_client(client):
            raise ValueError("Invalid Telegram client")
        
        if not TelegramMessage.__valid_message_link(message_link):
            raise ValueError("Invalid message link format. Expected format: 'https://t.me/c/<chat_id>/<message_id>' or 'https://t.me/<username>/<message_id>'")
        
        # Handle private link: https://t.me/c/<chat_id>/<message_id>
        match_private = re.search(r"t\.me/c/(\d+)/(\d+)", message_link)
        if match_private:
            raw_chat_id = int(match_private.group(1))
            message_id = int(match_private.group(2))
            full_chat_id = int(f"-100{raw_chat_id}")
            # Create the new TelegramMessage
            return TelegramMessage(await client.get_messages(full_chat_id, ids=message_id))

        # Handle public link: https://t.me/<username>/<message_id>
        match_public = re.search(r"t\.me/([^/]+)/(\d+)", message_link)
        if match_public:
            username = match_public.group(1)
            message_id = int(match_public.group(2))
            entity = await client.get_entity(username)
            # Create the new TelegramMessage
            return TelegramMessage(await client.get_messages(entity, ids=message_id))

        raise ValueError("Unsupported or invalid Telegram message link format")
    
    @staticmethod
    def generate_json_caption(type : TelegramMessageType, file_name : str) -> dict[str, any]:
        """
        Generate a JSON caption for the file message
        
        NOTE: This method can be changed to be a property of the TelegramMessage class, but for now 
        I prefer to keep it as a static method since it does not depend on any instance of the class and 
        can be used to generate captions for new messages
        
        Args:
            type (TelegramMessageType): The type of the file message
            file_name (str): Name of the file
        Returns:
            dict[str, any]: The generated JSON caption
        Raises:
            ValueError: If the TelegramMessageType is unknown
        """
        
        # Generate the caption based on the type
        match(type):
            case TelegramMessageType.ROOT:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type": TelegramMessageType.ROOT.value,
                    "Name": file_name,
                    "Children": []
                }
            case TelegramMessageType.FOLDER:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type": TelegramMessageType.FOLDER.value,
                    "Name": file_name,
                    "Children": [],
                    "Parent": None
                }
            case TelegramMessageType.FILE:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type": TelegramMessageType.FILE.value,
                    "Name": file_name,
                    "Parent": None
                }
            case TelegramMessageType.LRV:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type" : TelegramMessageType.LRV.value
                }
            case TelegramMessageType.THUMBNAIL:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type" : TelegramMessageType.THUMBNAIL.value
                }
            case _:
                raise ValueError(f"Unknown TelegramMessageType: {type}")
    
    
    @staticmethod
    def __valid_client(client : 'TelegramManagerClient') -> bool:
        """
        Check to validate if the Telegram client is valid
        
        Args:
            client (TelegramManagerClient): The Telegram client to validate
        Returns:
            bool: True if the Telegram client is valid, False otherwise
        """
        return bool(client) and hasattr(client, 'api_id') and hasattr(client, 'api_hash')
    
    @staticmethod
    def __valid_chat_entity(chat : Entity) -> bool:
        """
        Check to validate if the chat entity is valid
        
        Args:
            chat (Entity): The chat entity to validate
        Returns:
            bool: True if the chat entity is valid, False otherwise
        """
        return bool(chat) and hasattr(chat, 'id')
    
    @staticmethod
    def __valid_message(message : 'TelegramMessage') -> bool:
        """
        Check to validate if the message is valid
        
        Args:
            message (TelegramMessage): The message to validate
        Returns:
            bool: True if the message is valid, False otherwise
        """
        return bool(message) and hasattr(message, 'telegram_message') and bool(message.telegram_message) and hasattr(message.telegram_message, 'id')
    
    @staticmethod
    def __valid_message_link(link : str) -> bool:
        """
        Check to validate if the message link is valid
        
        Args:
            link (str): The message link to validate
        Returns:
            bool: True if the message link is valid, False otherwise
        """
        return bool(link) and isinstance(link, str) and link.startswith("https://t.me/")