import asyncio
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from xml.dom.minidom import Entity

from dbJson.file_message import FileMessage
from file_manager.file_manager_main import FileManager
from compression.FFMPEG import FFMPEG
from file_types.file import File
from config import API_ID, API_HASH, CHANNEL_NAME
from ui.pop_up_textinput import PopUpTextInput
from ui.file_browser_pane import FileBrowserPane
from telegram.telegram_manager_client import TelegramManagerClient

# === Global state ===

# Initialize the Telegram client instance
client = TelegramManagerClient('Telegram-UI', API_ID, API_HASH)
# Chat entity that the user want to use as Database
target_chat_instance : Entity = None

# Class to browse the file structure
file_browser_pane : FileBrowserPane = None

# === Telegram async initializer ===
async def init():
    """
    Initialize the Telegram client, fetch dialogs and set up the initial file browser pane
    """
    global file_browser_pane
    global client
    
    # List of dialogs (chats)
    dialog_dict = {}
    
    # Init client
    await client.start()
    await client.initialize()
    
    # Save the dialogs in a dict
    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group or dialog.is_user:
            dialog_dict[dialog.name] = dialog.entity
    
    # Initial the root of the file browser pane with the chat instance
    file_browser_pane = FileBrowserPane(root, await _get_chat_instance())
    await file_browser_pane.init_root(client)
    
async def _get_chat_instance():
    """
    Get the target chat entity instance
    """
    global target_chat_instance
    
    if target_chat_instance is None:
        target_chat_instance = await client.get_entity(CHANNEL_NAME)
    return target_chat_instance



#region Buttons UI Handlers

def _choose_file():
    """
    Open a file dialog to let the user choose a file
    """
    return File(filedialog.askopenfilename())

def _choose_folder():
    """
    Open a file dialog to let the user choose a folder
    """
    return filedialog.askdirectory()

def create_folder_UI():
    """
    Create a new folder in the current position of the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_create_folder_UI())
async def _create_folder_UI():
    """
    Create a new folder in the current position of the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Open the pop up to let the user insert the name
        pop_up_name = PopUpTextInput(root)
        
        # Create the folder
        message_instance = await FileManager.create_folder(
            client, 
            await _get_chat_instance(), 
            pop_up_name.value, 
            file_browser_pane.current_position
        )
        print("Folder created with message ID:", message_instance.telegram_message)
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        
def upload_file_UI():
    """
    Upload a file to the current position of the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_upload_file_UI())
    return
async def _upload_file_UI():
    """
    Upload a file to the current position of the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Open the file dialog to let the user choose a file
        selected_file = _choose_file()
    
        # Upload the file
        message_instance = await FileManager.upload_file(client, await _get_chat_instance(), selected_file, file_browser_pane.current_position)
        
        print("File uploaded with message ID:", message_instance.telegram_message)
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        
def download_file_UI():
    """
    Download a file from the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_download_file_UI())
    return
async def _download_file_UI():
    """
    Download a file from the selected file in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Download the selected file
        download_path = await FileManager.download_file(client, await _get_chat_instance(), file_browser_pane.selected)
        
        print("File downloaded to:", download_path)
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def see_preview_UI():
    """
    See a preview of the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_see_preview_UI())
    return
async def _see_preview_UI():
    """
    See a preview of the selected file in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # TODO
        pass
    except Exception as e:
        messagebox.showerror("Error", str(e))
       
def back_UI():
    """
    Go back to the previous folder in the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_back_UI())
async def _back_UI():
    """
    Go back to the previous folder in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        asyncio.create_task(file_browser_pane.go_back_path(client))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def rename_UI():
    """
    Rename the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_rename_UI())
async def _rename_UI():
    """
    Rename the selected file in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Check if a file is selected
        if file_browser_pane.selected is None:
            messagebox.showinfo("Select a file")
            return
        
        # Open the pop up to let the user insert the new name
        pop_up_name = PopUpTextInput(root, file_browser_pane.selected.short_name)
        
        # Rename the file
        await FileManager.rename(client, await _get_chat_instance(), file_browser_pane.selected, pop_up_name.value + "." +file_browser_pane.selected.extension)
        
        print("File renamed")
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_UI():
    """
    Delete the selected file in the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_delete_UI())
async def _delete_UI():
    """
    Delete the selected file in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Delete the selected file
        await FileManager.delete(client, await _get_chat_instance(), file_browser_pane.selected)
        
        print("File deleted")
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def move_UI():
    """
    Move the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_move_UI())
async def _move_UI():
    """
    Move the selected file in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Check if a file is selected
        if file_browser_pane.selected is None:
            messagebox.showinfo("Select a file")
            return
        
        popup = tk.Toplevel(root)
        popup.title("Move File")
        popup.geometry("700x400")
        popup.grab_set()

        # Open a new file browser pane to choose the destination
        move_file_browser_pane = FileBrowserPane(popup, await _get_chat_instance())
        await move_file_browser_pane.init_root(client)

        # Await the popup closing without blocking the asyncio event loop
        await wait_window_async(popup)
        
        # Release the grab and destroy the popup
        popup.grab_release()
        popup.destroy()
        
        # Move the selected file
        await FileManager.move(
            client, 
            await _get_chat_instance(), 
            file_browser_pane.selected, 
            move_file_browser_pane.current_position
        )
        
        print("File moved")
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))
    
def sync_UI():
    """
    Sync the current folder in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_sync_UI())
async def _sync_UI():
    """
    Sync the current folder in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Open the file dialog to let the user choose a folder
        selected_folder = _choose_folder()
        
        # Recursive sync the folder
        await FileManager.sync(client, await _get_chat_instance(), selected_folder, file_browser_pane.current_position)
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))
#endregion



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
    ("Back", back_UI, tk.NORMAL),
    ("Create folder", create_folder_UI, tk.NORMAL),
    ("Upload file", upload_file_UI, tk.NORMAL),
    ("Download file", download_file_UI, tk.NORMAL),
    ("See preview", see_preview_UI, tk.NORMAL),
    ("Rename", rename_UI, tk.NORMAL),
    ("Move", move_UI, tk.NORMAL),
    ("Sync", sync_UI, tk.NORMAL),
    ("Delete", delete_UI, tk.NORMAL)
]
for txt, cmd, state in btns:
    tk.Button(frame, text=txt, command=cmd, state=state).pack(pady=5)
    
# Main asyncio event loop
loop = asyncio.get_event_loop()

async def wait_window_async(win: tk.Toplevel):
    """Asynchronously wait for a Tk `Toplevel` window to close without blocking the asyncio loop.

    The function returns when the window is destroyed or its WM_DELETE_WINDOW is invoked.
    """
    future = loop.create_future()

    def _on_close(*_):
        if not future.done():
            future.set_result(None)

    try:
        win.protocol("WM_DELETE_WINDOW", _on_close)
    except Exception:
        pass

    # If the toplevel itself is destroyed, fire the future.
    # Ignore Destroy events coming from child widgets (they bubble up).
    def _on_destroy(event=None):
        if event is None:
            _on_close()
            return
        # Only react when the event's widget is the toplevel itself
        try:
            if event.widget is not win:
                return
        except Exception:
            return
        _on_close()

    win.bind("<Destroy>", _on_destroy)

    # If window already destroyed, return immediately
    if not win.winfo_exists():
        return

    await future

# Run the event loop in background
async def main_async():
    """
    Main async function to initialize the Telegram client and keep the loop running
    """
    await init()
    while True:
        await asyncio.sleep(0.1)

def run_app():
    """
    Run the Tkinter application with the asyncio event loop
    """
    # Ensure FFMPEG is available
    FFMPEG.ensure_ffmpeg()
    
    # Run the main async function and Tkinter main loop
    loop.run_until_complete(
        asyncio.gather(
            main_async(),
            run_tk()
        )
    )

async def run_tk():
    """
    Run the Tkinter main loop asynchronously
    """
    while True:
        root.update()
        await asyncio.sleep(0.01)

# Run
run_app()