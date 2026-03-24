import asyncio
import tkinter as tk
from tkinter import messagebox, filedialog
from xml.dom.minidom import Entity

from file_manager.file_manager_main import FileManager
from compression.FFMPEG import FFMPEG
from file_types.file import File
from config import API_ID, API_HASH, CHANNEL_NAME
from ui.pop_up_textinput import PopUpTextInput
from ui.file_browser_pane import FileBrowserPane
from ui.sync_jobs_panel import SyncJobsPanel
from telegram.telegram_manager_client import TelegramManagerClient

# === Global state ===

# Initialize the Telegram client instance
client = TelegramManagerClient('Telegram-UI', API_ID, API_HASH)
# Chat entity that the user want to use as Database
target_chat_instance : Entity = None

# Class to browse the file structure
file_browser_pane : FileBrowserPane = None

# App running flag (used to stop background loops on close)
app_running = True

# Sync panel instance (created after UI frame exists)
sync_panel = None

# === Telegram async initializer ===
async def init() -> None:
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
    # give the sync panel a reference to the file browser pane so actions can refresh it
    try:
        if sync_panel:
            sync_panel.set_file_browser_pane(file_browser_pane)
    except Exception:
        pass
    
async def _get_chat_instance() -> Entity:
    """
    Get the target chat entity instance
    
    The function caches the chat instance in a global variable after the first fetch to avoid multiple calls to Telegram for the same entity
        
    Returns:
        Entity: the Telegram entity instance of the target chat (channel/group/user) specified by CHANNEL_NAME in the config
    """
    # Use the global variable to cache the chat instance after the first fetch
    global target_chat_instance
    
    # If the chat instance is not cached, fetch it from Telegram using the channel name
    if target_chat_instance is None:
        target_chat_instance = await client.get_entity(CHANNEL_NAME)
    
    # Return the cached chat instance
    return target_chat_instance



#region Buttons UI Handlers

def _choose_file() -> File:
    """
    Open a file dialog to let the user choose a file
    """
    return File(filedialog.askopenfilename())

def _choose_folder() -> str:
    """
    Open a file dialog to let the user choose a folder
    """
    return filedialog.askdirectory()

def create_folder_UI() -> None:
    """
    Create a new folder in the current position of the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_create_folder_UI())
async def _create_folder_UI() -> None:
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
        
def upload_file_UI() -> None:
    """
    Upload a file to the current position of the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_upload_file_UI())
    return
async def _upload_file_UI() -> None:
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
        
def download_file_UI() -> None:
    """
    Download a file from the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_download_file_UI())
    return
async def _download_file_UI() -> None:
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
       
def back_UI() -> None:
    """
    Go back to the previous folder in the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_back_UI())
async def _back_UI() -> None:
    """
    Go back to the previous folder in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        asyncio.create_task(file_browser_pane.go_back_path(client))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def rename_UI() -> None:
    """
    Rename the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_rename_UI())
async def _rename_UI() -> None:
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

def delete_UI() -> None:
    """
    Delete the selected file in the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_delete_UI())
async def _delete_UI() -> None:
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
        
def open_preview_UI() -> None:
    """
    Open a preview of the selected file in the file browser pane
    
    This is the UI handler that wraps the async function
    """
    loop.create_task(_open_preview_UI())
async def _open_preview_UI() -> None:
    """
    Open a preview of the selected file in the file browser pane
    """
    global file_browser_pane
    global client
    
    try:
        # Open a preview of the selected file inside the popup
        await FileManager.open_preview(client, await _get_chat_instance(), file_browser_pane.selected)
        
        print("File preview opened")
        
        # Refresh current position
        await file_browser_pane.current_position.refresh(client, await _get_chat_instance())
        # Refresh UI
        await file_browser_pane.render_current_folder(client)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def move_UI() -> None:
    """
    Move the selected file in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_move_UI())
async def _move_UI() -> None:
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
    
def sync_UI() -> None:
    """
    Sync the current folder in the file browser pane

    This is the UI handler that wraps the async function
    """
    loop.create_task(_sync_UI())
async def _sync_UI() -> None:
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

def on_close() -> None:
    """
    Window close handler: stop background routines and persist state
    """
    global app_running
    
    # Set the running flag to false to stop background loops
    app_running = False
    try:
        if sync_panel:
            sync_panel.stop()
    except Exception:
        pass

# Wire the close handler
try:
    root.protocol("WM_DELETE_WINDOW", on_close)
except Exception:
    pass

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
    ("Open preview", open_preview_UI, tk.NORMAL),
    ("Rename", rename_UI, tk.NORMAL),
    ("Move", move_UI, tk.NORMAL),
    ("Sync", sync_UI, tk.NORMAL),
    ("Delete", delete_UI, tk.NORMAL)
]
for txt, cmd, state in btns:
    tk.Button(frame, text=txt, command=cmd, state=state).pack(pady=5)
    
# Main asyncio event loop
loop = asyncio.get_event_loop()

# Instantiate Sync Jobs panel
sync_panel = SyncJobsPanel(frame, loop, client)

async def wait_window_async(win: tk.Toplevel) -> None:
    """
    Asynchronously wait for a Tk `Toplevel` window to close without blocking the asyncio loop.

    The function returns when the window is destroyed or its WM_DELETE_WINDOW is invoked.
    """
    # Create a future that will be set when the window is closed
    future = loop.create_future()

    def _on_close(*_) -> None:
        """
        Stop the event loop when the window is closed, either by the user or programmatically
        """
        if not future.done():
            future.set_result(None)

    try:
        win.protocol("WM_DELETE_WINDOW", _on_close)
    except Exception:
        pass

    # If the toplevel itself is destroyed, fire the future.
    # Ignore Destroy events coming from child widgets (they bubble up).
    def _on_destroy(event=None) -> None:
        """
        Handle the destroy event for the toplevel window and set the future result to unblock the waiting coroutine
        """

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
async def main_async() -> None:
    """
    Main async function to initialize the Telegram client and keep the loop running
    """
    await init()
    
    # start background refresher for sync jobs UI
    try:
        if sync_panel:
            sync_panel.start_refresher()
    except Exception:
        pass
    
    # Keep the loop running until the app is closed
    while app_running:
        await asyncio.sleep(0.1)

def run_app() -> None:
    """
    Run the Tkinter application with the asyncio event loop
    """
    # Ensure FFMPEG is available
    FFMPEG.ensure_ffmpeg()
    # Run the main async function and Tkinter main loop
    try:
        loop.run_until_complete(
            asyncio.gather(
                main_async(),
                run_tk()
            )
        )
    finally:
        # final cleanup: persist jobs, destroy UI and close loop
        try:
            if sync_panel:
                sync_panel.stop()
        except Exception:
            pass
        try:
            if root.winfo_exists():
                root.destroy()
        except Exception:
            pass
        try:
            loop.close()
        except Exception:
            pass

async def run_tk() -> None:
    """
    Run the Tkinter main loop asynchronously
    """
    try:
        while app_running:
            root.update()
            await asyncio.sleep(0.01)
    except Exception:
        # if root is destroyed or update fails, exit
        return

# Run
run_app()