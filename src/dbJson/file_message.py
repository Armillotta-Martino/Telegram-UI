from enum import Enum
import json
import re
from xml.dom.minidom import Entity
from telethon.tl.custom.message import Message
from telegram.telegram_manager_client import TelegramManagerClient

from config import FILE_CAPTION_VERSION

class FileMessageType(Enum):
    """
        Enum representing the type of file message
    """
    
    ROOT = "ROOT"
    FOLDER = "FOLDER"
    FILE = "FILE"
    LRV = "LRV"


class FileMessage(Message):
    """
        Class representing a file message in the telegram database
        One message on telegram represents one instance of this class
        
        Args:
            message: Telegram message data
    """
    
    ### Private members
    
    # The telegram message
    __message: Message
    # The file message type
    __type: FileMessageType
    
    def __init__(self, message: Message):
        """
        Constructor
        
        Args:
            message: Telegram message data
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Type
        """
        # Save the message
        self.__message = message
        
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")

        # Infer type from the message
        json_message = json.loads(self.__message.message)
        if "Type" not in json_message:
            raise ValueError("Message does not contain Type")
        # Set the type
        self.__type = FileMessageType(json_message["Type"].upper())

    
    @property
    def telegram_message(self) -> Message:
        """
        Get the telegram message
            
        I decided to use the name telegram_message instead of message to avoid confusion with the base 
        Message class message property
        
        Args:
            self: Description
        Returns:
            Message: The telegram message
        """
        return self.__message
    
    @property
    def type(self) -> FileMessageType:
        """
        Get the file message type
        
        Args:
            self: Description
        Returns:
            FileMessageType: The type of the file message
        """        
        # Return type
        return self.__type
        
    @property
    def is_folder(self) -> bool:
        """
        Check if the message is a folder
        
        Args:
            self: Description
        Returns:
            bool: True if the message is a folder, False otherwise
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Type
        """
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.__message.message)
        
        # Check type
        if "Type" not in json_message:
            raise ValueError("Message does not contain Type")
        
        # Return true if folder or root
        if json_message["Type"] == FileMessageType.FOLDER.value or json_message["Type"] == FileMessageType.ROOT.value:
            return True
        
        return False
    
    @property
    def version(self) -> str:
        """
        Get the version of the file message
        
        Args:
            self: Description
        Returns:
            str: The version of the file message
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Version
        """
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.__message.message)
        
        # Check version
        if "Version" not in json_message:
            raise ValueError("Message does not contain Version")
        
        # Return version
        return json_message["Version"]
    
    @property
    def file_name(self) -> str:
        """
        Get the file name from the message
        
        Params:
            self: Description
        Returns:
            str: The file name from the message
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Name
        """
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.__message.message)
        
        # Check name
        if "Name" not in json_message:
            raise ValueError("Message does not contain Name")
        
        # Return name
        return json_message["Name"]
    
    @property
    def extension(self) -> str:
        """
        Get the file extension from the file name
        
        Args:
            self: Description
        Returns:
            str: The file extension
        """
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
        
        Args:
            self: Description
        Returns:
            str: The file name without the extension
        """
        # Split the file name by dot
        split_name = self.file_name.rsplit('.', 1)
        # Return the name without extension
        return split_name[0]
    
    @property
    def file_size(self) -> str:
        """
        Get the size of the document attached to the message
        
        Args:
            self: Description
        Returns:
            str: The size of the document
        """
        # Return the size of the document
        return self.document.size
    
    async def get_parent(self, client : TelegramManagerClient):
        """
        Get the parent message of the current message
            
        This could be a property, but I prefer to keep it as a method since it is async
        
        Args:
            self: Description
            client: Telegram manager client
        Returns:
            FileMessage: The parent message
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Parent
        """
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.__message.message)
        
        # Check parent
        if "Parent" not in json_message:
            raise ValueError("Message does not contain Parent")
        
        return await self.get_FileMessage_from_link(client, json_message["Parent"])
    
    async def get_children(self, client : TelegramManagerClient):
        """
        Get the children messages of the current message
            
        This could be a property, but I prefer to keep it as a method since it is async
        
        Args:
            self: Description
            client: Telegram manager client
        Returns:
            list[FileMessage]: The list of children messages
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Children
        """
        
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.__message.message)
        
        # Check children
        if "Children" not in json_message:
            raise ValueError("Message does not contain Children list")
        
        # Get children
        children_messages_list : list[FileMessage] = []
        for child_link in json_message["Children"]:
            # Get the child message from the link
            child_message = await self.get_FileMessage_from_link(client, child_link)
            children_messages_list.append(child_message)
        
        # Return children
        return children_messages_list
    
    async def get_children_by_file_name(self, client : TelegramManagerClient, name : str):
        """
        Get the children messages of the current message that match a specific file name
            
        This could be a property, but I prefer to keep it as a method since it is async
        
        Args:
            self: Description
            client: Telegram manager client
            name: The file name to filter children messages by
        Returns:
            list[FileMessage]: The list of children messages that match the file name
        Raises:
            ValueError: If the message is empty or has no text, or does not contain Children
        """
        
        # Get all children
        children = await self.get_children(client)
        
        # Filter children by name
        filtered_children = [child for child in children if child.file_name == name]
        return filtered_children
    
    async def add_children(self, client : TelegramManagerClient, chat_instance : Entity, message_link : str):
        """
        Add a child message link to the current message
        Add a link to the message as a child of the current message
        
        Args:
            self: Description
            client: Telegram manager client
            chat_instance: Chat instance
            message_link: Message link
        Returns:
            None
        Raises:
            ValueError: If the message is empty or has no text
        """
        
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")
        
        # Parse the message
        json_message = json.loads(self.__message.message)
        # Add link to the children
        json_message['Children'].append(message_link)
        # Convert back to json string
        json_message = json.dumps(json_message, indent=4)
        # Edit the message
        await client.edit_message(chat_instance, self.telegram_message, json_message)
        
    async def remove_children(self, client : TelegramManagerClient, chat_instance : Entity, message_link : str):
        """
        Remove a child message link from the current message
        
        Args:
            self: Description
            client: Telegram manager client
            chat_instance: Chat instance
            message_link: Message link
        Returns:
            None
        Raises:
            ValueError: If the message is empty or has no text
        """
        
        # Check message validity
        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")

        # Parse the message
        json_message = json.loads(self.__message.message)

        # Remove link from the children
        for c in json_message['Children']:
            if c == message_link:
                json_message["Children"].remove(c)
        
        # Convert back to json string
        json_message = json.dumps(json_message, indent=4)
        # Edit the message
        await client.edit_message(chat_instance, self.telegram_message, json_message)
    
    async def refresh(self, client : TelegramManagerClient, chat_instance : Entity):
        """
        Refresh the telegram message data
        
        Args:
            client: Telegram manager client
            chat_instance: Chat instance
        Returns:
            None
        """
        
        # Check message validity
        if self.__message == None:
            return None
        
        # Get the updated message
        self.__message = await client.get_messages(chat_instance, ids=self.__message.id)
    
    @staticmethod
    def calculate_message_link(chat : Entity, message : 'FileMessage') -> str:
        """
        Calculate the link to a message in a channel or group
        
        Args:
            chat: The chat entity (channel or group)
            message: The message to calculate the link for
        Returns:
            str: The link to the message
        """
        
        # Check message validity
        if not message or not message.telegram_message:
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
    async def get_FileMessage_from_link(client : TelegramManagerClient, message_link : str):
        """
        Get a FileMessage instance from a telegram message link
        
        Args:
            client: Telegram manager client
            message_link: Telegram message link
        Returns:
            FileMessage instance
        Raises:
            ValueError: If the message link format is unsupported or invalid
        """
        
        # Handle private link: https://t.me/c/<chat_id>/<message_id>
        match_private = re.search(r"t\.me/c/(\d+)/(\d+)", message_link)
        if match_private:
            raw_chat_id = int(match_private.group(1))
            message_id = int(match_private.group(2))
            full_chat_id = int(f"-100{raw_chat_id}")
            # Create the new FileMessage
            return FileMessage(await client.get_messages(full_chat_id, ids=message_id))

        # Handle public link: https://t.me/<username>/<message_id>
        match_public = re.search(r"t\.me/([^/]+)/(\d+)", message_link)
        if match_public:
            username = match_public.group(1)
            message_id = int(match_public.group(2))
            entity = await client.get_entity(username)
            # Create the new FileMessage
            return FileMessage(await client.get_messages(entity, ids=message_id))

        raise ValueError("Unsupported or invalid Telegram message link format")
    
    @staticmethod
    def generate_json_caption(type : FileMessageType, file_name : str) -> dict[str, any]:
        """
        Generate a JSON caption for the file message
        
        Args:
            type: FileMessageType
            file_name: Name of the file
        Returns:
            dict[str, any]: The generated JSON caption
        Raises:
            ValueError: If the FileMessageType is unknown
        """
        
        # Generate the caption based on the type
        match(type):
            case FileMessageType.ROOT:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type": FileMessageType.ROOT.value,
                    "Name": file_name,
                    "Children": []
                }
            case FileMessageType.FOLDER:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type": FileMessageType.FOLDER.value,
                    "Name": file_name,
                    "Children": [],
                    "Parent": None
                }
            case FileMessageType.FILE:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Type": FileMessageType.FILE.value,
                    "Name": file_name,
                    "Children": [],
                    "Parent": None
                }
            case FileMessageType.LRV:
                return {
                    "Version": FILE_CAPTION_VERSION,
                    "Part" : "LRV"
                }
            case _:
                raise ValueError(f"Unknown FileMessageType: {type}")