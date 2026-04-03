import asyncio
import json
import os
import tempfile
import tkinter as tk
from tkinter import Image, ttk
from xml.dom.minidom import Entity
from PIL import Image, ImageTk

# Import constants from config
from config import ICON_FILE_PATH, ICON_FOLDER_PATH

from file_manager.file_manager_main import FileManager
from dbJson.telegram_message import TelegramMessage, TelegramMessageType
from telegram.telegram_manager_client import TelegramManagerClient

class FileBrowserPane:
    """ 
    A pane for browsing files in a Telegram chat.
    It allows navigating through folders, selecting files, and displaying their contents.
    """
    
    ### Constants
    
    # Icon sizes
    ICON_SIZE = (64, 64)
    # Grid configuration
    GRID_COLUMNS = 4
    # Default file icons paths
    FILE_ICONS = {
        'folder': ICON_FOLDER_PATH,
        'default': ICON_FILE_PATH
    }
    
    # Parent tkinter element
    __parent : tk.Tk = None
    
    # Root message. It is the root of the folders
    __root : TelegramMessage = None
    # Current folder position
    __current : TelegramMessage = None
    # Selected element
    __selected_button : tk.Button = None
    
    # Telegram chat instance
    __chat_instance : Entity = None
    
    # UI elements
    __path_var : tk.StringVar = None
    __scroll_frame : tk.Frame = None
    
    # region Initialization and UI Setup
    
    def __init__(self, parent, chat_instance : Entity) -> None:
        """
        Initialize the FileBrowserPane

        Args:
            parent: The parent tkinter element
            chat_instance (Entity): The Telegram chat instance
        """
        # Store the parent element
        self.__parent = parent
        # Store the chat instance
        self.__chat_instance = chat_instance
        # Load icons
        self.icons = {
            'folder': self.__load_icon(self.FILE_ICONS['folder'], self.ICON_SIZE),
            'default': self.__load_icon(self.FILE_ICONS['default'], self.ICON_SIZE)
        }
        
        # Initialize the UI
        self.__init_ui()
        
    def __init_ui(self) -> None:
        """
        Initialize the UI components of the file browser pane.
        """
        # --- Path Display (top) ---
        self.__path_var = tk.StringVar()
        path_entry = tk.Entry(self.__parent, textvariable=self.__path_var, state='readonly', width=80, relief='sunken')
        path_entry.pack(padx=10, pady=5, fill='x')

        # --- Main area ---
        main_frame = tk.Frame(self.__parent)
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas background
        canvas = tk.Canvas(main_frame, background="white")
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.__scroll_frame = tk.Frame(canvas)
        self.__scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.__scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    async def init_root(self, client : TelegramManagerClient) -> None:
        """
        Initialize the root folder by fetching or creating the root message
        
        Args:
            client (TelegramManagerClient): The Telegram client
        """
        # Get the pinned message
        root_message = await FileManager.get_root(client, self.__chat_instance)
        
        # Refresh the root message
        await root_message.refresh(client, self.__chat_instance)
        
        # Set the root and current positions
        self.__root = root_message
        self.__current = root_message
        
        # Render the root folder
        await self.render_current_folder(client)
    
    def __load_icon(self, path: str, size: tuple) -> ImageTk.PhotoImage:
        """
        Load and resize an icon image from the specified path
        
        This is used to load icons for files and folders in the file browser
        
        Args:
            path (str): The path to the icon image
            size (tuple): The desired size (width, height) of the icon
        Returns:
            ImageTk.PhotoImage: The loaded and resized icon image
        """
        img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    
    # endregion
    
    @property
    def current_position(self) -> TelegramMessage:
        """
        Get the current folder position
        
        Returns:
            TelegramMessage: The current folder message
        """
        return self.__current
    
    @property
    def selected(self) -> TelegramMessage:
        """
        Get the currently selected file message
        
        Returns:
            TelegramMessage: The currently selected file message
        """
        return self.__selected_button.message
    
    # region Navigation
      
    async def go_to_path(self, client : TelegramManagerClient, message : TelegramMessage) -> None:
        """
        Navigate to the specified folder message

        Args:
            client (TelegramManagerClient): The Telegram client
            message (TelegramMessage): The folder message to navigate to
        Returns:
            None
        """
        # Calculate the new path
        folder_name = message.file_name
        current_path = self.__path_var.get()
        new_path = current_path + "\\" + folder_name if current_path else folder_name
        
        # Update the path
        self.__path_var.set(new_path)
        
        # TODO Check if it is a valid child
        
        # Update the current position
        self.__current = message
        
        # Render the new folder
        await self.render_current_folder(client)
    
    async def go_back_path(self, client : TelegramManagerClient) -> None:
        """
        Navigate back to the parent folder
        
        Args:
            client (TelegramManagerClient): The Telegram client
        Returns:
            None
        """
        # Calculate the new path
        if '\\' in self.__path_var.get():
            split = self.__path_var.get().rsplit('\\', 1)
            self.__path_var.set(split[0])
        else:
            self.__path_var.set("")
        
        
        # Update the current position
        parent = await self.__current.get_parent(client)
        self.__current = parent
        
        # Render the new folder
        await self.render_current_folder(client)
    
    # endregion
    
    # region Rendering
    
    async def render_current_folder(self, client : TelegramManagerClient) -> None:
        """
        Render the contents of the current folder in the UI
        
        Args:
            client (TelegramManagerClient): The Telegram client
        Returns:
            None
        """
        
        # Get the children of the current folder
        children = await self.__current.get_children(client)
        
        # Clear the view
        for widget in self.__scroll_frame.winfo_children():
            widget.destroy()

        row = 0
        col = 0
        # Render each child item
        for item in children:
            # Get the icon for the item (folder or file)
            icon = await self.render_file_icon(client, item)
            
            # Create a frame for each item
            frame = tk.Frame(self.__scroll_frame, width=100, height=100)
            frame.grid(row=row, column=col, padx=15, pady=15)
            
            # Create the button with icon and name
            btn = tk.Button(frame, image=icon, text=item.file_name, compound="top", wraplength=80, relief='flat', background="white")
            btn.message = item
            # Bind single click to selection
            btn.bind("<Button-1>", lambda event, b=btn: self.on_item_select(b))
            # Bind double click to open
            btn.bind("<Double-Button-1>", lambda event, p=item: asyncio.create_task(self.on_item_double_click(client, p)))
            
            btn.image = icon
            btn.pack()

            col += 1
            if col >= self.GRID_COLUMNS:
                col = 0
                row += 1

    async def render_file_icon(self, client : TelegramManagerClient , file_message : TelegramMessage) -> ImageTk.PhotoImage:
        """
        Get the appropriate icon for a file message, downloading the thumbnail if available

        Args:
            client (TelegramManagerClient): The Telegram client
            file_message (TelegramMessage): The file message to get the icon for
        Returns:
            ImageTk.PhotoImage: The icon image
        """
        ## Icon
            
        # Load the default icon based on the item type (folder or file)
        icon = self.icons['folder'] if file_message.is_folder else self.icons['default']
            
        # Download the thumbnail if it is a file and has a thumbnail
        # Iterate through the messages to find the file message
        async for message in client.iter_messages(self.__chat_instance, reply_to=file_message.telegram_message.id):
            # Find the file message
            json_message = json.loads(message.message)
            if json_message.get("Type") == TelegramMessageType.THUMBNAIL.value:
                # Create a temporary file to store the thumbnail
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                tmp.close()
                # Download the thumbnail media to the temporary file
                await client.download_media(message.media, file=tmp.name)
                # Override the icon with the thumbnail
                icon = ImageTk.PhotoImage(Image.open(tmp.name).resize(self.ICON_SIZE, Image.Resampling.LANCZOS))
                # Remove the temporary file
                os.remove(tmp.name)
                break
            
        return icon
    
    # endregion
    
    # region Item Selection and Actions
    
    def on_item_select(self, button : tk.Button) -> None:
        """
        Handle the selection of an item in the file browser
            
        Args:
            button (tk.Button): The button representing the selected item
        Returns:
            None
        """
        
        # Deselect the previously selected button if it still exists
        if self.__selected_button and self.__selected_button.winfo_exists():
            self.__selected_button.config(bg="SystemButtonFace")
        
        # Example visual feedback (e.g., border or background color change)
        # Change color to show selection
        button.config(bg="#cceeff")
        
        # Save the selected item in a variable
        self.__selected_button = button

    async def on_item_double_click(self, client : TelegramManagerClient, message : TelegramMessage) -> None:
        """
        Handle the double-click action on an item in the file browser
            
        Args:
            client (TelegramManagerClient): The Telegram client
            message (TelegramMessage): The file message representing the double-clicked item
        Returns:
            None
        """
        
        if message.is_folder:
            await self.go_to_path(client, message)
        else:
            # TODO Check if it is a supported file
            # TODO get the file to display (LRV, image, ecc...)
            print("Open file:", message)
    
    # endregion