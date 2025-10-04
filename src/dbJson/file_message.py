from enum import Enum
import json
import re
from xml.dom.minidom import Entity
from telethon.tl.custom.message import Message
from telegram.telegram_manager_client import TelegramManagerClient


class FileMessageType(Enum):
    ROOT = "ROOT"
    FOLDER = "FOLDER"
    FILE = "FILE"
    LRV = "LRV"


class FileMessage(Message):
    
    __message: Message
    __type: FileMessageType
    
    def __init__(self, message: Message, type: FileMessageType | None = None):
        self.__message = message

        if not self.__message or not self.__message.message:
            raise ValueError("Message is empty or has no text")

        if type is None:
            # infer type from the message
            json_message = json.loads(self.__message.message)
            if "Type" not in json_message:
                raise ValueError("Message does not contain Type")
            self.__type = FileMessageType(json_message["Type"].upper())
        else:
            # use explicitly provided type
            self.__type = type

    
    @property
    def telegram_message(self) -> Message:
        return self.__message
        
    @property
    def is_folder(self) -> bool:
        if not self.__message or not self.__message.message:
            # TODO This case is an error
            print("Message is empty or has no text")
            return None

        json_message = json.loads(self.__message.message)
        
        if "Type" not in json_message:
            # TODO This case is an error
            print("Message does not contain Type")
            return None
        
        if json_message["Type"] == FileMessageType.FOLDER.value or json_message["Type"] == FileMessageType.ROOT.value:
            return True
        
        return False
    
    @property
    def version(self) -> str:
        if not self.__message or not self.__message.message:
            # TODO This case is an error
            print("Message is empty or has no text")
            return None

        json_message = json.loads(self.__message.message)
        
        if "Version" not in json_message:
            # TODO This case is an error
            print("Message does not contain Name")
            return None
        
        return json_message["Version"]
    
    @property
    def file_name(self) -> str:
        if not self.__message or not self.__message.message:
            # TODO This case is an error
            print("Message is empty or has no text")
            return None

        json_message = json.loads(self.__message.message)
        
        if "Name" not in json_message:
            # TODO This case is an error
            print("Message does not contain Name")
            return None
        
        return json_message["Name"]
    
    @property
    def type(self) -> FileMessageType:
        return self.__type
    
    @staticmethod
    def generate_json_caption(type : FileMessageType, file_name : str) -> dict[str, any]:
        """                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
            Get the json representation of the file message
        """
        match(type):
            case FileMessageType.ROOT:
                return {
                    "Version": 1,
                    "Type": FileMessageType.ROOT.value,
                    "Name": file_name,
                    "Children": []
                }
            case FileMessageType.FOLDER:
                return {
                    "Version": 1,
                    "Type": FileMessageType.FOLDER.value,
                    "Name": file_name,
                    "Children": [],
                    "Parent": None
                }
            case FileMessageType.FILE:
                return {
                    "Version": 1,
                    "Type": FileMessageType.FILE.value,
                    "Name": file_name,
                    "Children": [],
                    "Parent": None
                }
            case FileMessageType.LRV:
                return {
                    "Part" : "LRV"
                }
            case _:
                raise ValueError(f"Unknown FileMessageType: {type}")
    
    async def get_childrens(self, client : TelegramManagerClient):
        if not self.__message or not self.__message.message:
            # TODO This case is an error
            print("Message is empty or has no text")
            return None

        json_message = json.loads(self.__message.message)
        
        if "Children" not in json_message:
            # TODO This case is an error
            print("Message does not contain Children list")
            return None
        
        children_messages_list : list[FileMessage] = []
        for child_link in json_message["Children"]:
            child_message = await self.get_filemessage_from_link(client, child_link)
            children_messages_list.append(child_message)
        
        return children_messages_list
    
    async def add_children(
        self,
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        message_link : str
        ):
        """
            Add a link to the message to the parent message children

            Args:
                client (TelegramManagerClient): _description_
                chat_instance (Entity): _description_
                parent_message (FileMessage): _description_
                message_link (str): _description_
        """
        if self.__message == None or self.__message.message == None:
            return
        
        json_new_parent_message_data = json.loads(self.telegram_message.message)
        json_new_parent_message_data['Children'].append(message_link)
        json_new_parent_new_message = json.dumps(json_new_parent_message_data, indent=4)
        await client.edit_message(chat_instance, self.telegram_message, json_new_parent_new_message)
        
    async def remove_children(
        self,
        client : TelegramManagerClient, 
        chat_instance : Entity, 
        message_link : str
        ):
        """
            Remove a link to the message from the parent message children

            Args:
                client (TelegramManagerClient): _description_
                chat_instance (Entity): _description_
                old_parent_message (FileMessage): _description_
                message_link (str): _description_
        """
        
        if self.__message == None or self.__message.message == None:
            return

        json_old_parent_message_data = json.loads(self.__message.message)
        # Remove link from the childrens
        for c in json_old_parent_message_data['Children']:
            if c == message_link:
                json_old_parent_message_data["Children"].remove(c)
        
        # Edit the message
        json_old_parent_new_message = json.dumps(json_old_parent_message_data, indent=4)
        await client.edit_message(chat_instance, self.telegram_message, json_old_parent_new_message)
    
    @staticmethod
    async def get_filemessage_from_link(client : TelegramManagerClient, message_link : str):
        # Handle private link: https://t.me/c/<chat_id>/<message_id>
        match_private = re.search(r"t\.me/c/(\d+)/(\d+)", message_link)
        if match_private:
            raw_chat_id = int(match_private.group(1))
            message_id = int(match_private.group(2))
            full_chat_id = int(f"-100{raw_chat_id}")
            return FileMessage(await client.get_messages(full_chat_id, ids=message_id))

        # Handle public link: https://t.me/<username>/<message_id>
        match_public = re.search(r"t\.me/([^/]+)/(\d+)", message_link)
        if match_public:
            username = match_public.group(1)
            message_id = int(match_public.group(2))
            entity = await client.get_entity(username)
            return FileMessage(await client.get_messages(entity, ids=message_id))

        raise ValueError("Unsupported or invalid Telegram message link format")
    
    async def refresh(self, client : TelegramManagerClient, chat_instance : Entity):
        if self.__message == None:
            return None
        
        self.__message = await client.get_messages(chat_instance, ids=self.__message.id)
    
    async def get_parent(self, client : TelegramManagerClient):
        if not self.__message or not self.__message.message:
            # TODO This case is an error
            print("Message is empty or has no text")
            return None

        json_message = json.loads(self.__message.message)
        
        if "Parent" not in json_message:
            # TODO This case is an error
            print("Message does not contain Name")
            return None
        
        return await self.get_filemessage_from_link(client, json_message["Parent"])
    