import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.utils.git_handler import GitHandler
from src.core.code_parsing.project import ProjectParser
from interfaces.html.html import HtmlGraphBuilder


class ParserApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Parser App")
        self.root.geometry("600x400")

        self.mode_var = tk.StringVar(value="full")
        self.mode_combobox = ttk.Combobox(
            self.root,
            textvariable=self.mode_var,
            values=["full", "object_links", "struct", "file_links"],
            state="readonly",
            width=15
        )
        self.mode_combobox.pack(pady=10)

        self.url_label = tk.Label(self.root, text="Enter Git Repo URL:")
        self.url_label.pack(pady=10)

        self.url_entry = tk.Entry(self.root, width=40)
        self.url_entry.pack(pady=10)

        self.process_url_button = tk.Button(
            self.root, text="Process URL",
            command=lambda: self.process_url(self.mode_var.get()))
        self.process_url_button.pack(pady=10)

        self.directory_button = tk.Button(
            self.root,
            text="Select Local Directory",
            command=lambda: self.process_directory(self.mode_var.get()))
        self.directory_button.pack(pady=10)

        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack(pady=20)

    def process_url(self, mode):
        url = self.url_entry.get()
        if url:
            self.show_status("URL processed successfully!")

            gh = GitHandler()
            path = gh.clone_repo(url)

            parser = ProjectParser(path)
            graph = parser.parse_project()
            parser.save_graph("tmp/results/output.json")
            HtmlGraphBuilder().apply_filter_and_save(graph, mode)
            self.show_status("Result saved!")
        else:
            messagebox.showwarning(
                "Input Error", "Please enter a valid Git Repo URL.")

    def process_directory(self, mode):
        directory = filedialog.askdirectory()
        if directory:
            self.show_status("Directory processed successfully!")
            parser = ProjectParser(directory)
            graph = parser.parse_project()
            parser.save_graph("tmp/results/output.json")
            HtmlGraphBuilder().apply_filter_and_save(graph, mode)
            self.show_status("Result saved!")
        else:
            messagebox.showwarning(
                "Input Error", "Please select a valid directory.")

    def show_status(self, message):
        self.status_label.config(text=message)

    def start(self):
        self.root.mainloop()
