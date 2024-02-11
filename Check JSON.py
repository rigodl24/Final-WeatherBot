from tkinter import filedialog
import tkinter as tk

root = tk.Tk()
root.withdraw()  # Hide the main window

file_path = filedialog.askopenfilename(initialdir="/", title="Select File",
                                       filetypes=(("JSON files", "*.json"), ("all files", "*.*")))

print("Selected file:", file_path)
