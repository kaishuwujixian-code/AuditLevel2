import io
import os
import tkinter as tk
from contextlib import redirect_stderr, redirect_stdout
from tkinter import filedialog, messagebox
from typing import Optional

from core.paths import PROJECTS_DIR
from main import _validate_inputs


class AppBindings:
    def __init__(self, window) -> None:
        self.window = window

    def new_project(self) -> None:
        if not self._confirm_discard_changes():
            return
        self.window.new_project()

    def open_project(self) -> None:
        if not self._confirm_discard_changes():
            return
        path = filedialog.askopenfilename(
            title="Open project.json",
            initialdir=PROJECTS_DIR,
            filetypes=[("Project JSON", "project.json"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            self.window.load_project(path)
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))

    def save_project(self) -> None:
        try:
            if not self.window.project_path:
                self.save_project_as()
                return
            self.window.save_project()
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def save_project_as(self) -> None:
        info = self.window.project_data.get("project_info", {})
        building = str(info.get("building_name", "project"))
        slug = self.window._slugify(building)
        default_dir = os.path.join(PROJECTS_DIR, slug)
        os.makedirs(default_dir, exist_ok=True)
        path = filedialog.asksaveasfilename(
            title="Save project.json",
            initialdir=default_dir,
            initialfile="project.json",
            defaultextension=".json",
            filetypes=[("Project JSON", "project.json"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            self.window.save_project(path)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def validate_project(self) -> None:
        if not self.window.project_path:
            messagebox.showwarning("Validate", "Save the project before validating.")
            return
        try:
            output = io.StringIO()
            errors = io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                _validate_inputs(
                    self.window.project_path,
                    "templates/template.level1.json",
                    "templates/level1.docx",
                )
            message = output.getvalue().strip() or "Validation complete."
            warnings = errors.getvalue().strip()
            if warnings:
                message = f"{message}\n\nWarnings:\n{warnings}"
            messagebox.showinfo("Validation", message)
            self.window.log_message("Validation complete.")
        except Exception as exc:
            messagebox.showerror("Validation failed", str(exc))
            self.window.log_message(f"Validation failed: {exc}")

    def generate_report(self) -> None:
        try:
            self.window.generate_report()
        except Exception as exc:
            messagebox.showerror("Generate failed", str(exc))
            self.window.log_message(f"Generate failed: {exc}")

    def _confirm_discard_changes(self) -> bool:
        return messagebox.askyesno(
            "Discard changes?",
            "Any unsaved changes will be lost. Continue?",
        )
