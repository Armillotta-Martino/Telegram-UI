import asyncio
import tkinter as tk
from tkinter import Image, ttk
from xml.dom.minidom import Entity

from file_manager import FileManager
from dbJson.file_message import FileMessage
from telegram.telegram_manager_client import TelegramManagerClient
from PIL import Image, ImageTk

class FileBrowserPane:
    """ 
        A pane for browsing files in a Telegram chat.
        It allows navigating through folders, selecting files, and displaying their contents.
    """
    ICON_SIZE = (64, 64)
    GRID_COLUMNS = 4
    FILE_ICONS = {
        'folder': 'icons/folder.png',
        'default': 'icons/file.png'
    }
    
    # Parent thinker element
    __parent : tk.Tk = None
    
    # Root message. It is the root of the folders
    __root : FileMessage = None
    # Current folder position
    __current : FileMessage = None
    # Selected element
    __selected_button : tk.Button = None
    
    __chat_instance : Entity = None
    
    __path_var : tk.StringVar = None
    __scroll_frame : tk.Frame = None
    
    @property
    def current_position(self) -> FileMessage:
        return self.__current
    
    @property
    def selected(self) -> FileMessage:
        return self.__selected_button.message
        
    async def go_to_path(
        self,
        client : TelegramManagerClient,
        message : FileMessage
        ):
        """
            Navigate to the specified folder message

            Args:
                message (FileMessage): _description_
        """
        # Update the path bar text
        folder_name = message.file_name
        current_path = self.__path_var.get()
        new_path = current_path + "\\" + folder_name if current_path else folder_name
        # Update the path
        self.__path_var.set(new_path)
        
        # TODO Check if it is a valid child
        
        # Update the current positon
        self.__current = message
        await self.render_current_folder(client)
    
    async def go_back_path(
        self,
        client : TelegramManagerClient
        ):
        """
            Navigate back to the parent folder
        """
        # Update the path bar text
        if '\\' in self.__path_var.get():
            split = self.__path_var.get().rsplit('\\', 1)
            self.__path_var.set(split[0])
        else:
            self.__path_var.set("")
        
        
        # Update the current positon
        parent = await self.__current.get_parent(client)
        self.__current = parent
        
        await self.render_current_folder(client)

    def __init__(
        self, 
        parent,
        chat_instance : Entity
        ):
        """
            Initialize the FileBrowserPane

        Args:
            parent (_type_): _description_
            chat_instance (Entity): _description_
        """
        self.__parent = parent
        
        self.__chat_instance = chat_instance

        self.icons = {
            'folder': self.__load_icon(self.FILE_ICONS['folder'], self.ICON_SIZE),
            'default': self.__load_icon(self.FILE_ICONS['default'], self.ICON_SIZE)
        }

        self.__init_ui()
        
    def __init_ui(
        self
        ):
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

        canvas = tk.Canvas(main_frame, background="white")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.__scroll_frame = tk.Frame(canvas)

        self.__scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.__scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    async def init_root(
        self,
        client : TelegramManagerClient
        ):
        """
            Initialize the root folder by fetching or creating the root message
        """
        # Get the pinned message
        root_message = await FileManager.get_root(client, self.__chat_instance)
        
        if root_message is None or root_message.telegram_message is None:
            # Create the root message and pin it
            root_message = await FileManager.create_root(client, self.__chat_instance)
        
        self.__root = root_message
        self.__current = root_message
        
        # Render the root folder
        asyncio.create_task(self.render_current_folder(client))
    
    def __load_icon(
        self, 
        path, 
        size
        ):
        """
            Load and resize an icon image from the specified path

        Args:
            path (_type_): _description_
            size (_type_): _description_

        Returns:
            _type_: _description_
        """
        img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
        
    async def render_current_folder(
        self,
        client : TelegramManagerClient
        ):
        """
            Render the contents of the current folder in the UI
        """
        
        # Get the children of the current folder
        children = await self.__current.get_childrens(client)
        
        # Clear the view
        for widget in self.__scroll_frame.winfo_children():
            widget.destroy()

        row = 0
        col = 0
        for item in children:
            is_dir = item.is_folder
            name = item.file_name
            icon = self.icons['folder'] if is_dir else self.icons['default']

            frame = tk.Frame(self.__scroll_frame, width=100, height=100)
            frame.grid(row=row, column=col, padx=15, pady=15)

            btn = tk.Button(frame, image=icon, text=name, compound="top", wraplength=80, relief='flat', background="white")
            btn.message = item
            # Bind single click to selection
            btn.bind("<Button-1>", lambda event, b=btn: self.on_item_select(b))
            # Bind double click to open
            btn.bind("<Double-Button-1>", lambda event, p=item: self.on_item_double_click(client, p))
            
            btn.image = icon
            btn.pack()

            col += 1
            if col >= self.GRID_COLUMNS:
                col = 0
                row += 1

    def on_item_select(
        self, 
        button : tk.Button
        ):
        """
            Handle the selection of an item in the file browser
            
            Args:
                button (tk.Button): The button representing the selected item
        """
        
        # Deselect the previously selected button if it still exists
        if self.__selected_button and self.__selected_button.winfo_exists():
            self.__selected_button.config(bg="SystemButtonFace")
        
        # Example visual feedback (e.g., border or background color change)
        # Change color to show selection
        button.config(bg="#cceeff")
        
        # Save the selected item in a variable
        self.__selected_button = button

    def on_item_double_click(
        self,
        client : TelegramManagerClient,
        message : FileMessage
        ):
        """
            Handle the double-click action on an item in the file browser
            
            Args:
                message (FileMessage): The file message representing the double-clicked item
        """
        
        if message.is_folder:
            asyncio.create_task(self.go_to_path(client, message))
        else:
            # TODO Check if it is a supported file
            # TODO get the file to display (LRV, image, ecc...)
            print("Open file:", message)