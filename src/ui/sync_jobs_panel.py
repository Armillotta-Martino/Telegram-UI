import os
import json
import asyncio
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Frame

from dbJson.file_message import FileMessage
from file_manager.file_manager_main import FileManager
from telegram.telegram_manager_client import TelegramManagerClient


class SyncJobsPanel:
    """
    A small panel placed in a parent frame that shows sync jobs and exposes controls.

    Usage: create with `SyncJobsPanel(parent, loop, client)`; then call
    `start_refresher()` to begin background reloads and `stop()` to stop them.
    """

    def __init__(self, parent : Frame, loop, client : TelegramManagerClient):
        """
        Initialize the SyncJobsPanel

        Args:
            parent (Frame): The parent frame in which the panel is placed
            loop (asyncio.AbstractEventLoop): The asyncio event loop
            client (TelegramManagerClient): The Telegram client instance
        """
        self.parent = parent
        self.loop = loop
        self.client = client
        self.file_browser_pane = None

        self.sync_jobs = []
        self.sync_jobs_file = os.path.join(os.getcwd(), "sync_jobs.json")

        self._running = False

        # UI
        self.frame = tk.LabelFrame(parent, text="Sync Jobs")
        self.frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)

        lb_frame = tk.Frame(self.frame)
        lb_frame.pack(fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(lb_frame, height=6)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lb_scroll = tk.Scrollbar(lb_frame, command=self.listbox.yview)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=lb_scroll.set)

        controls = tk.Frame(self.frame)
        controls.pack(fill=tk.X)
        tk.Button(controls, text="Resume", width=6, command=lambda: self.resume_job_UI()).pack(side=tk.LEFT, padx=2, pady=4)
        tk.Button(controls, text="Restart", width=6, command=lambda: self.restart_job_UI()).pack(side=tk.LEFT, padx=2, pady=4)
        tk.Button(controls, text="Delete", width=6, command=lambda: self.delete_job_UI()).pack(side=tk.LEFT, padx=6, pady=4)

        # load initial
        self.load_sync_jobs()
        self.refresh_ui()

    # --- Persistence ---
    def load_sync_jobs(self):
        """
        Load sync jobs from the JSON file. 
        If the file doesn't exist or is invalid, start with an empty list
        """
        try:
            with open(self.sync_jobs_file, 'r', encoding='utf-8') as f:
                self.sync_jobs = json.load(f)
        except Exception:
            self.sync_jobs = []

    def save_sync_jobs(self):
        """
        Save the current sync jobs to the JSON file
        """
        try:
            with open(self.sync_jobs_file, 'w', encoding='utf-8') as f:
                json.dump(self.sync_jobs, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save sync jobs: {e}")

    # --- UI helpers ---
    def refresh_ui(self):
        """
        Refresh the UI to reflect the current state of sync jobs
        """
        sel = self.listbox.curselection()
        self.listbox.delete(0, tk.END)
        for i, job in enumerate(self.sync_jobs):
            display = job.get('pc_path') or job.get('telegram_link') or f"Job {i}"
            status = job.get('state', 'unknown')
            self.listbox.insert(tk.END, f"[{status}] {display}")
        if sel and sel[0] < self.listbox.size():
            self.listbox.select_set(sel[0])

    def get_selected_index(self):
        """
        Get the index of the currently selected sync job in the listbox.

        Returns:
            int: The index of the selected sync job, or None if no job is selected
        """
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    # --- Actions ---
    def restart_job_UI(self):
        """
        Restart the selected sync job by resetting its synced files and re-initiating the sync process
        """
        self.loop.create_task(self._restart_job_UI())
    async def _restart_job_UI(self):
        """
        Restart the selected sync job by resetting its synced files and re-initiating the sync process
        """
        idx = self.get_selected_index()
        if idx is None:
            return
        # reset synced files
        self.sync_jobs[idx]['synced_files'] = []
        self.save_sync_jobs()
        link = self.sync_jobs[idx].get('telegram_link')
        pc_path = self.sync_jobs[idx].get('pc_path')
        telegram_file_message = await FileMessage.get_FileMessage_from_link(self.client, link)
        await FileManager.sync(self.client, await self.client.get_entity(""), pc_path, telegram_file_message)
        # Note: we don't change UI state for the file browser here

    def resume_job_UI(self):
        """
        Resume the selected sync job by continuing the sync process from where it left off
        """
        self.loop.create_task(self._resume_job_UI())
    async def _resume_job_UI(self):
        """
        Resume the selected sync job by continuing the sync process from where it left off
        """
        idx = self.get_selected_index()
        if idx is None:
            return
        link = self.sync_jobs[idx].get('telegram_link')
        pc_path = self.sync_jobs[idx].get('pc_path')
        telegram_file_message = await FileMessage.get_FileMessage_from_link(self.client, link)
        await FileManager.sync(self.client, await self.client.get_entity(""), pc_path, telegram_file_message)

    def delete_job_UI(self):
        """
        Delete the selected sync job from the list and update the UI
        """
        idx = self.get_selected_index()
        if idx is None:
            return
        if messagebox.askyesno("Delete", "Delete selected sync job?"):
            del self.sync_jobs[idx]
            self.save_sync_jobs()
            self.refresh_ui()

    # --- Background refresher ---
    async def _refresher(self):
        """
        Background task that periodically reloads sync jobs from disk and refreshes the UI
        """
        while self._running:
            try:
                self.load_sync_jobs()
                self.refresh_ui()
            except Exception:
                pass
            await asyncio.sleep(1)

    def start_refresher(self):
        """
        Start the background refresher task if it's not already running
        """
        if not self._running:
            self._running = True
            self.loop.create_task(self._refresher())

    def stop(self):
        """
        Stop the background refresher task
        """
        self._running = False
        try:
            self.save_sync_jobs()
        except Exception:
            pass

    def set_file_browser_pane(self, fb):
        """
        Set the file browser pane reference for this panel, allowing it to update the file browser when sync jobs are resumed/restarted

        Args:
            fb (_type_): _description_
        """
        self.file_browser_pane = fb
