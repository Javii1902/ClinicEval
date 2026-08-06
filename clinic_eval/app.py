import tkinter as tk
from tkinter import ttk

from .db import backup_database
from .ui.home import Home
from .ui.new_assessment import NewAssessment
from .ui.clinic import Clinic
from .ui.dashboard import Dashboard


class ClinicEvalApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ClinicEval")
        self.geometry("1500x950")
        self.minsize(1200, 750)

        self.notebook = None
        self.tabs = {}

        self.build_ui()
        self.run_startup_backup()

    def run_startup_backup(self):
        # A quiet safety net, not a required user action: at most one
        # automatic backup per calendar day, so restarting the app several
        # times in a day doesn't pile up near-duplicate copies. Never allowed
        # to block startup or crash the app if it fails for any reason.
        try:
            backup_database(force=False)
        except OSError:
            pass

    def build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tabs["home"] = Home(self.notebook, self)
        self.tabs["new_assessment"] = NewAssessment(self.notebook, self)
        self.tabs["clinic"] = Clinic(self.notebook, self)
        self.tabs["dashboard"] = Dashboard(self.notebook, self)

        self.notebook.add(self.tabs["home"], text="Home")
        self.notebook.add(self.tabs["new_assessment"], text="New Assessment")
        self.notebook.add(self.tabs["clinic"], text="Clinic")
        self.notebook.add(self.tabs["dashboard"], text="Dashboard")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.after(100, lambda: self.open_tab("home"))

    def open_tab(self, tab_name):
        tab = self.tabs.get(tab_name)
        if tab is not None:
            self.notebook.select(tab)
            self.after_idle(lambda: self.refresh_tab(tab))

    def on_tab_changed(self, event):
        selected_tab_id = self.notebook.select()
        if not selected_tab_id:
            return

        selected_widget = self.nametowidget(selected_tab_id)
        self.after_idle(lambda: self.refresh_tab(selected_widget))

    def refresh_tab(self, tab_widget):
        refresh_method = getattr(tab_widget, "refresh_data", None)
        if callable(refresh_method):
            refresh_method()
