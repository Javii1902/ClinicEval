from tkinter import ttk, messagebox

from ..db import backup_database


class Home(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_ui()

    def build_ui(self):
        container = ttk.Frame(self, padding=30)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Welcome to ClinicEval",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(20, 10))

        ttk.Label(
            container,
            text="Use the buttons below to open the section you want.",
            font=("Segoe UI", 11)
        ).pack(pady=(0, 30))

        ttk.Button(
            container,
            text="Open New Assessment",
            command=lambda: self.app.open_tab("new_assessment")
        ).pack(pady=10, ipadx=10, ipady=8)

        ttk.Button(
            container,
            text="Open Clinic",
            command=lambda: self.app.open_tab("clinic")
        ).pack(pady=10, ipadx=10, ipady=8)

        ttk.Button(
            container,
            text="Open Dashboard",
            command=lambda: self.app.open_tab("dashboard")
        ).pack(pady=10, ipadx=10, ipady=8)

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=(30, 20))

        ttk.Button(
            container,
            text="Backup Database Now",
            command=self.backup_now
        ).pack(pady=10, ipadx=10, ipady=8)

    def backup_now(self):
        try:
            backup_path = backup_database(force=True)
        except OSError as e:
            messagebox.showerror("Backup Failed", f"Could not back up the database.\n\n{e}")
            return

        if backup_path is None:
            messagebox.showwarning("Backup Skipped", "No database file was found to back up.")
            return

        messagebox.showinfo("Backup Complete", f"Database backed up successfully.\n\n{backup_path}")