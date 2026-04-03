import tkinter as tk

class PopUp_TextInput:
    """
    A simple popup dialog for entering text.
    
    This class creates a modal dialog that allows the user to input a string.
    The entered text can be retrieved after the dialog is closed.
    """
    
    def __init__(self, parent, text : str = "") -> None:
        """
        Initialize the PopUp_TextInput dialog.
        
        Args:
            parent: The parent tkinter element
            text (str): The initial text to display in the entry field
        Returns:
            None
        """
        self.value = None
        
        # Create the popup window
        self.popup = tk.Toplevel(parent)
        self.popup.title("Enter Text")
        self.popup.geometry("300x150")
        self.popup.transient(parent)
        self.popup.grab_set()
        
        # Create and place a label
        label = tk.Label(self.popup, text="Enter your text:")
        label.pack(pady=(10, 5))
        
        # Create and place a text entry field
        self.entry = tk.Entry(self.popup, width=40)
        self.entry.insert(0, text)
        self.entry.pack(pady=5)
        
        # Create and place a submit button
        submit_btn = tk.Button(self.popup, text="Submit", command=self.on_submit)
        submit_btn.pack(pady=(10, 5))

        parent.wait_window(self.popup)

    def on_submit(self) -> None:
        """
        Handle the submit button click event
        
        Returns:
            None
        """
        # Retrieve the entered text, save it and close the popup
        self.value = self.entry.get()
        self.popup.destroy()
