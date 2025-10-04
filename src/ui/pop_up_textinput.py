import tkinter as tk

class PopUpTextInput:
    """
        A simple popup dialog for entering text.
        This class creates a modal dialog that allows the user to input a string.
        The entered text can be retrieved after the dialog is closed.
    """
    def __init__(
        self, 
        parent
        ):
        self.value = None

        self.popup = tk.Toplevel(parent)
        self.popup.title("Enter Text")
        self.popup.geometry("300x150")
        self.popup.transient(parent)
        self.popup.grab_set()

        label = tk.Label(self.popup, text="Enter your text:")
        label.pack(pady=(10, 5))

        self.entry = tk.Entry(self.popup, width=40)
        self.entry.pack(pady=5)

        submit_btn = tk.Button(self.popup, text="Submit", command=self.on_submit)
        submit_btn.pack(pady=(10, 5))

        parent.wait_window(self.popup)

    def on_submit(self):
        self.value = self.entry.get()
        self.popup.destroy()
