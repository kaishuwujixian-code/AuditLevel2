import io
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional

from core.paths import (
    DEFAULT_TEMPLATE_DOCX,
    DEFAULT_TEMPLATE_JSON,
    OUTPUT_DIR,
    PROJECTS_DIR,
)
from core.project_store import (
    ProjectSummary,
    default_output_path_for_project,
    default_output_path_for_summary,
    load_project,
    save_project,
    scan_project_summaries,
)
from core.template_store import TemplateData, load_template
from reporting.level1_generator import generate_level1_report
from ui.detail_panel import DetailPanel
from ui.navigation_tree import NavigationTree
from ui.ribbon import Ribbon
from ui.workspace_table import WorkspaceTable
from main import _validate_inputs


class RetScreenApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("RETScreen-style Audit Studio")
        self.root.geometry("1280x720")
        self._template: Optional[TemplateData] = None
        self._project_data: Optional[Dict] = None
        self._project_path: Optional[str] = None
        self._project_summaries: list[ProjectSummary] = []
        self._status_var = tk.StringVar(value="Ready")
        self._build_ui()
        self._load_template()
        self.refresh_projects()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        ribbon_actions = {
            "open_projects": self.open_projects_folder,
            "open_output": self.open_output_folder,
            "settings": self.show_settings,
            "exit": self.root.destroy,
            "generate_selected": self.generate_selected,
            "generate_all": self.generate_all,
            "validate": self.validate_project,
            "save": self.save_project,
            "export": self.placeholder_export,
        }

        ribbon = Ribbon(self.root, ribbon_actions)
        ribbon.grid(row=0, column=0, sticky="ew")

        content = ttk.Frame(self.root)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        nav_frame = ttk.Frame(content)
        nav_frame.grid(row=0, column=0, sticky="nsew")
        nav_frame.rowconfigure(0, weight=1)
        nav_frame.columnconfigure(0, weight=1)

        self.navigation = NavigationTree(nav_frame, self.load_project)
        self.navigation.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)

        workspace_frame = ttk.Frame(content)
        workspace_frame.grid(row=0, column=1, sticky="nsew")
        workspace_frame.columnconfigure(0, weight=3)
        workspace_frame.columnconfigure(1, weight=2)
        workspace_frame.rowconfigure(0, weight=1)

        self.workspace = WorkspaceTable(workspace_frame, self.on_measure_selected)
        self.workspace.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.details = DetailPanel(workspace_frame)
        self.details.grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=6)

        status_bar = ttk.Label(
            self.root,
            textvariable=self._status_var,
            anchor="w",
            relief="sunken",
            padding=(8, 4),
        )
        status_bar.grid(row=2, column=0, sticky="ew")

    def _set_status(self, message: str) -> None:
        self._status_var.set(message)

    def _load_template(self) -> None:
        if not os.path.isfile(DEFAULT_TEMPLATE_JSON):
            self._set_status(f"Template JSON missing: {DEFAULT_TEMPLATE_JSON}")
            return
        try:
            self._template = load_template(DEFAULT_TEMPLATE_JSON)
        except Exception as exc:
            self._set_status(f"Template error: {exc}")

    def refresh_projects(self) -> None:
        summaries, errors = scan_project_summaries(PROJECTS_DIR)
        self._project_summaries = summaries
        self.navigation.populate(summaries)
        message = f"Loaded {len(summaries)} project(s)."
        if errors:
            message += f" {len(errors)} file(s) skipped."
            for error in errors:
                print(error)
        self._set_status(message)

    def load_project(self, project_path: str) -> None:
        if not self._template:
            self._set_status("Template not loaded.")
            return
        try:
            self._project_data = load_project(project_path)
            self._project_path = project_path
            self.workspace.load_project(self._template, self._project_data)
            self.details.load_project(self._template, self._project_data)
            self._set_status(f"Loaded project: {project_path}")
        except Exception as exc:
            self._set_status(f"Error loading project: {exc}")

    def on_measure_selected(self, measure_key: str) -> None:
        self.details.set_measure_preview(measure_key)

    def save_project(self) -> None:
        if not self._project_path or not self._project_data:
            self._set_status("No project loaded.")
            return
        try:
            self.details.update_project_notes()
            save_project(self._project_path, self._project_data)
            self._set_status(f"Saved project: {self._project_path}")
        except Exception as exc:
            self._set_status(f"Save failed: {exc}")

    def generate_selected(self) -> None:
        if not self._project_path or not self._project_data:
            self._set_status("Select a project to generate.")
            return
        if not self._ensure_templates():
            return
        try:
            self.details.update_project_notes()
            save_project(self._project_path, self._project_data)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            out_path = default_output_path_for_project(
                self._project_data, self._project_path, OUTPUT_DIR
            )
            generate_level1_report(
                self._project_path,
                DEFAULT_TEMPLATE_JSON,
                DEFAULT_TEMPLATE_DOCX,
                out_path,
            )
            self._set_status(f"Generated: {out_path}")
        except Exception as exc:
            self._set_status(f"Generate failed: {exc}")

    def generate_all(self) -> None:
        if not self._ensure_templates():
            return
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        completed = 0
        for summary in self._project_summaries:
            try:
                out_path = default_output_path_for_summary(summary, OUTPUT_DIR)
                generate_level1_report(
                    summary.path,
                    DEFAULT_TEMPLATE_JSON,
                    DEFAULT_TEMPLATE_DOCX,
                    out_path,
                )
                completed += 1
            except Exception as exc:
                self._set_status(f"Generate failed for {summary.name}: {exc}")
                return
        self._set_status(f"Generated {completed} report(s) in {OUTPUT_DIR}.")

    def validate_project(self) -> None:
        if not self._project_path:
            self._set_status("No project loaded.")
            return
        try:
            output = io.StringIO()
            error_output = io.StringIO()
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = output
            sys.stderr = error_output
            try:
                _validate_inputs(
                    self._project_path, DEFAULT_TEMPLATE_JSON, DEFAULT_TEMPLATE_DOCX
                )
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
            message = output.getvalue().strip() or "Validation completed."
            warnings = error_output.getvalue().strip()
            if warnings:
                message = f"{message}\n\nWarnings:\n{warnings}"
            messagebox.showinfo("Validation", message)
            self._set_status("Validation complete.")
        except Exception as exc:
            messagebox.showerror("Validation Failed", str(exc))
            self._set_status(f"Validation failed: {exc}")

    def open_projects_folder(self) -> None:
        self._open_folder(PROJECTS_DIR, "projects")

    def open_output_folder(self) -> None:
        self._open_folder(OUTPUT_DIR, "output")

    def show_settings(self) -> None:
        messagebox.showinfo("Settings", "Settings will be available in a future update.")

    def placeholder_export(self) -> None:
        messagebox.showinfo("Export", "Export is not available yet.")

    def _open_folder(self, path: str, label: str) -> None:
        try:
            os.makedirs(path, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
            self._set_status(f"Opened {label} folder: {path}")
        except Exception as exc:
            self._set_status(f"Open folder failed: {exc}")

    def _ensure_templates(self) -> bool:
        if not os.path.isfile(DEFAULT_TEMPLATE_JSON):
            self._set_status(f"Template JSON missing: {DEFAULT_TEMPLATE_JSON}")
            return False
        if not os.path.isfile(DEFAULT_TEMPLATE_DOCX):
            self._set_status(f"Template DOCX missing: {DEFAULT_TEMPLATE_DOCX}")
            return False
        return True
