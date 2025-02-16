import tkinter as tk
from tkinter import filedialog, messagebox

from src.parser.parser import ProjectAnalyzer
from src.utils.repo_manager.git_manager import GitManager

class ParserApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Parser App")
        self.root.geometry("600x400")

        self.url_label = tk.Label(self.root, text="Enter Git Repo URL:")
        self.url_label.pack(pady=10)

        self.url_entry = tk.Entry(self.root, width=40)
        self.url_entry.pack(pady=10)

        self.process_url_button = tk.Button(self.root, text="Process URL", command=self.process_url)
        self.process_url_button.pack(pady=10)

        self.directory_button = tk.Button(self.root, text="Select Local Directory", command=self.process_directory)
        self.directory_button.pack(pady=10)

        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack(pady=20)

    def process_url(self):
        url = self.url_entry.get()
        if url:
            self.show_status("URL processed successfully!")
            project = GitManager(url)
            analyzer = ProjectAnalyzer(project.path)
            analyzer.analyze()
            analyzer.graph.save_to_json()
            self.show_status("Result saved!")
        else:
            messagebox.showwarning("Input Error", "Please enter a valid Git Repo URL.")

    def process_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.show_status("Directory processed successfully!")
            analyzer = ProjectAnalyzer(directory)
            analyzer.analyze()
            analyzer.graph.save_to_json()
            self.show_status("Result saved!")
        else:
            messagebox.showwarning("Input Error", "Please select a valid directory.")

    def show_status(self, message):
        self.status_label.config(text=message)

    def start(self):
        self.root.mainloop()

