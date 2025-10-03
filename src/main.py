import asyncio
import tkinter as tk

def back_UI():
    return

def create_folder_UI():
    return

def upload_file_UI():
    return

def rename_UI():
    return

def delete_UI():
    return


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
        
def run_app():
    loop.run_until_complete(asyncio.gather(
        run_tk()       # Tkinter in separate task
    ))

async def run_tk():
    while True:
        root.update()
        await asyncio.sleep(0.01)

# Run
run_app()