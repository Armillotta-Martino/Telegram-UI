import asyncio
import tkinter as tk
from tkinter import messagebox, filedialog
from xml.dom.minidom import Entity

from file_manager import FileManager
from file_types.file import File
from config import API_ID, API_HASH, CHANNEL_NAME
from ui.pop_up_textinput import PopUpTextInput
from ui.file_browser_pane import FileBrowserPane
from telegram.telegram_manager_client import TelegramManagerClient

client = TelegramManagerClient('Telegram-UI', API_ID, API_HASH)

# Chat entity that the user want to use as Database
target_chat_instance : Entity = None


# Main asyncio event loop
loop = asyncio.get_event_loop()

# === Global state ===
# List of dialogs (chats)
dialog_dict = {}
# Class to browse the file structure
file_browser_pane : FileBrowserPane = None

# === Telegram async initializer ===
async def init():
    global file_browser_pane
    global client
    
    # Init client
    await client.start()
    await client.initialize()
    # Save the dialogs (chats)
    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group or dialog.is_user:
            dialog_dict[dialog.name] = dialog.entity
    
    # Initial directory
    file_browser_pane = FileBrowserPane(root, await __get_chat_instance())
    await file_browser_pane.init_root(client)
    
async def __get_chat_instance():
    global target_chat_instance
    if target_chat_instance is None:
        target_chat_instance = await client.get_entity(CHANNEL_NAME)
    return target_chat_instance




def __choose_file():
    return File(filedialog.askopenfilename())

def create_folder_UI():
    loop.create_task(_create_folder_UI())
async def _create_folder_UI():
    global file_browser_pane
    global client
    try:
        # Let the user insert the name
        pop_up_name = PopUpTextInput(root)
        # Create the folder
        message_instance = await FileManager.create_folder(
            client, 
            await __get_chat_instance(), 
            pop_up_name.value, 
            file_browser_pane.current_position
        )
        print("Folder created with message ID:", message_instance.telegram_message)
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await __get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        
def upload_file_UI():
    loop.create_task(_upload_file_UI())
    return
async def _upload_file_UI():
    global file_browser_pane
    global client
    try:
        # Let the user choose the file
        selected_file = __choose_file()
        # Upload the file
        message_instance = await FileManager.upload_file(client, await __get_chat_instance(), selected_file, file_browser_pane.current_position)
        print("File uploaded with message ID:", message_instance.telegram_message)
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await __get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        
def back_UI():
    loop.create_task(_back_UI())
async def _back_UI():
    global file_browser_pane
    global client
    try:
        asyncio.create_task(file_browser_pane.go_back_path(client))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def rename_UI():
    loop.create_task(_rename_UI())
async def _rename_UI():
    global file_browser_pane
    global client
    try:
        if file_browser_pane.selected is None:
            messagebox.showinfo("Select a file")
        
        # Let the user insert the new name
        pop_up_name = PopUpTextInput(root)
        # Rename the file
        await FileManager.rename(client, await __get_chat_instance(), file_browser_pane.selected, pop_up_name.value)
        print("File renamed")
        
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_UI():
    loop.create_task(_delete_UI())
async def _delete_UI():
    global file_browser_pane
    global client
    try:
        # Delete the selected file
        await FileManager.delete(client, await __get_chat_instance(), file_browser_pane.selected)
        print("File deleted")
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await __get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# === Tkinter UI Setup ===
root = tk.Tk()
root.title("Telegram Uploader")
root.geometry("800x500")

# --- SIDEBAR (left) ---

# Side buttons frame
frame = tk.Frame(root)
frame.pack(side=tk.LEFT, fill=tk.Y)

# Buttons
btns = [
    ("Back", back_UI),
    ("Create folder", create_folder_UI),
    ("Upload file", upload_file_UI),
    ("Rename", rename_UI),
    ("Delete", delete_UI)
]
for txt, cmd in btns:
    tk.Button(frame, text=txt, command=cmd).pack(pady=5)
    
# Main asyncio event loop
loop = asyncio.get_event_loop()

# Run the event loop in background
async def main_async():
    await init()
    while True:
        await asyncio.sleep(0.1)

def run_app():
    loop.run_until_complete(asyncio.gather(
        main_async(),  # client.start + dialog_dict
        run_tk()       # Tkinter in separate task
    ))

async def run_tk():
    while True:
        root.update()
        await asyncio.sleep(0.01)

# Run
run_app()