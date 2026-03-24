import tkinter as tk
from tkinter import ttk

import threading
import queue

class PopUp_Progress_Bar:
    """
    Threaded, non-blocking popup progress bar singleton.

    Usage:
        win = PopUp_Progress_Bar.instance()
        win.update(pct, text)
        win.close()
    """

    _instance = None

    def __init__(self) -> None:
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    @classmethod
    def instance(cls) -> 'PopUp_Progress_Bar':
        # Recreate instance if none exists or thread stopped
        if cls._instance is None:
            cls._instance = cls()
        else:
            inst = cls._instance
            # If tkinter is available and the thread died, recreate
            if tk is not None and getattr(inst, '_thread', None) is not None and not inst._thread.is_alive():
                cls._instance = cls()
        return cls._instance

    def _run(self) -> None:
        if tk is None:
            # tkinter not available; thread exits quietly
            return

        self.root = tk.Tk()
        self.root.title('Progress')
        self.root.geometry('420x100')
        # Try to make the window appear on top even when the main app is unfocused
        try:
            try:
                self.root.attributes('-topmost', True)
            except Exception:
                try:
                    self.root.wm_attributes('-topmost', True)
                except Exception:
                    pass
            self.root.lift()
            try:
                self.root.focus_force()
            except Exception:
                pass
            # remove topmost after a short delay so it doesn't stay always on top
            try:
                self.root.after(500, lambda: self.root.attributes('-topmost', False))
            except Exception:
                pass
        except Exception:
            pass

        self._bar = ttk.Progressbar(self.root, orient='horizontal', length=380, mode='determinate')
        self._bar.pack(padx=10, pady=(10, 5))
        self._label = tk.Label(self.root, text='')
        self._label.pack(padx=10, pady=(0, 10))

        self._poll()
        # Ensure we clear the singleton when the window is closed
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass
        self.root.mainloop()

        # mainloop finished -> clear singleton so a new window can be created later
        try:
            PopUp_Progress_Bar._instance = None
        except Exception:
            pass

    def _poll(self) -> None:
        try:
            while True:
                pct, text = self._q.get_nowait()
                try:
                    self._bar['value'] = pct
                    self._label.config(text=f"{pct:.2f}% {text}" if text else f"{pct:.2f}%")
                except Exception:
                    pass

                # Auto-close on 100%
                try:
                    if pct >= 100:
                        if tk is not None:
                            self.root.after(500, self.root.destroy)
                        with self._q.mutex:
                            self._q.queue.clear()
                        return
                except Exception:
                    pass
        except queue.Empty:
            pass

        if tk is not None:
            self.root.after(100, self._poll)

    def update(self, pct: float, text: str = '') -> None:
        try:
            self._q.put_nowait((pct, text))
        except Exception:
            pass

    def close(self) -> None:
        if tk is None:
            return
        try:
            if hasattr(self, 'root'):
                self.root.after(0, self.root.destroy)
        except Exception:
            pass

    def _on_close(self) -> None:
        """Handle user closing the window: destroy and clear singleton."""
        try:
            PopUp_Progress_Bar._instance = None
        except Exception:
            pass
        try:
            if hasattr(self, 'root'):
                self.root.destroy()
        except Exception:
            pass