import io
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

from core.paths import (
    DEFAULT_TEMPLATE_DOCX,
    DEFAULT_TEMPLATE_JSON,
    OUTPUT_DIR,
    PROJECTS_DIR,
)
from core.project_store import (
    default_output_path_for_project,
    load_project,
    save_project,
)
from core.questionnaire import load_questionnaire_schema
from core.template_store import TemplateData, load_template
from main import _validate_inputs
from reporting.word_renderer import render_word
from ui.checklist_panel import ChecklistPanel
from ui.diagnostics_panel import DiagnosticsPanel
from ui.measure_library_panel import MeasureLibraryPanel
from ui.measures_panel import MeasuresPanel
from ui.questionnaire_panel import QuestionnairePanel
from ui.report_panel import ReportPanel


class RetScreenApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Audit Studio")
        self.root.geometry("1280x720")
        self._template: Optional[TemplateData] = None
        self._schema: Optional[Dict] = None
        self._project_data: Optional[Dict] = None
        self._project_path: Optional[str] = None
        self._status_var = tk.StringVar(value="Ready")
        self._load_template()
        self._load_schema()
        self._build_ui()
        self.new_project()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, padding=(8, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)

        button_frame = ttk.Frame(toolbar)
        button_frame.grid(row=0, column=0, sticky="w")
        ttk.Button(button_frame, text="Open", command=self.open_project_dialog).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(button_frame, text="Save", command=self.save_project).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(button_frame, text="Validate", command=self.validate_project).grid(
            row=0, column=2, padx=(0, 6)
        )
        ttk.Button(button_frame, text="Generate Report", command=self.generate_report).grid(
            row=0, column=3, padx=(0, 6)
        )
        ttk.Button(
            button_frame, text="Open Output Folder", command=self.open_output_folder
        ).grid(row=0, column=4, padx=(0, 6))

        content = ttk.Frame(self.root)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self._notebook = ttk.Notebook(content)
        self._notebook.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self._inputs_tab = QuestionnairePanel(self._notebook, self._schema or {})
        self._measures_tab = MeasuresPanel(self._notebook)
        self._measure_library_tab = MeasureLibraryPanel(
            self._notebook, on_catalog_saved=self._on_catalog_saved
        )
        self._checklist_tab = ChecklistPanel(self._notebook, self._template or TemplateData({}, [], {}, [], {}, {}))
        self._report_tab = ReportPanel(self._notebook, self.generate_report)
        self._diagnostics_tab = DiagnosticsPanel(self._notebook)

        self._notebook.add(self._inputs_tab, text="Inputs")
        self._notebook.add(self._measures_tab, text="Measures")
        self._notebook.add(self._measure_library_tab, text="Measure Library")
        self._notebook.add(self._checklist_tab, text="Checklist")
        self._notebook.add(self._report_tab, text="Report")
        self._notebook.add(self._diagnostics_tab, text="Diagnostics")

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

    def _load_schema(self) -> None:
        try:
            self._schema = load_questionnaire_schema(
                os.path.join("schemas", "level1_questionnaire.schema.json")
            )
        except Exception as exc:
            self._set_status(f"Schema error: {exc}")

    def new_project(self) -> None:
        self._project_data = {
            "project_info": {
                "client_name": "",
                "site_address": "",
                "building_name": "",
                "report_date": "",
                "prepared_by": "",
            },
            "answers": {},
            "measures": [],
            "selected_measures": [],
            "measure_overrides": {},
            "checklist_selections": {},
            "notes": {"general_site_notes": ""},
        }
        self._project_path = None
        self._load_project_into_tabs()
        self._set_status("Started new project.")

    def load_project(self, project_path: str) -> None:
        if not self._template or not self._schema:
            self._set_status("Template or schema not loaded.")
            return
        try:
            self._project_data = load_project(project_path)
            self._project_path = project_path
            self._load_project_into_tabs()
            self._set_status(f"Loaded project: {project_path}")
        except Exception as exc:
            self._set_status(f"Error loading project: {exc}")

    def open_project_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Open project.json",
            initialdir=PROJECTS_DIR,
            filetypes=[("Project JSON", "project.json"), ("JSON files", "*.json")],
        )
        if path:
            self.load_project(path)

    def _load_project_into_tabs(self) -> None:
        if not self._project_data:
            return
        if self._schema:
            self._inputs_tab.load_project(self._project_data)
        if self._template:
            self._measures_tab.load_project(self._project_data)
            self._checklist_tab.load_project(self._project_data)

    def save_project(self) -> None:
        if not self._project_path or not self._project_data:
            path = filedialog.asksaveasfilename(
                title="Save project.json",
                initialdir=PROJECTS_DIR,
                defaultextension=".json",
                filetypes=[("Project JSON", "*.json")],
                initialfile="project.json",
            )
            if not path:
                self._set_status("Save cancelled.")
                return
            self._project_path = path
        try:
            self._sync_project_data()
            save_project(self._project_path, self._project_data)
            self._set_status(f"Saved project: {self._project_path}")
        except Exception as exc:
            self._set_status(f"Save failed: {exc}")

    def generate_report(self) -> None:
        if not self._project_path or not self._project_data:
            self._set_status("Select a project to generate.")
            return
        if not self._ensure_templates():
            return
        try:
            self._sync_project_data()
            save_project(self._project_path, self._project_data)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            out_path = default_output_path_for_project(
                self._project_data, self._project_path, OUTPUT_DIR
            )
            render_word(
                template_path=DEFAULT_TEMPLATE_DOCX,
                project_json_path=self._project_path,
                out_path=out_path,
            )
            self._report_tab.update_output(out_path)
            self._set_status(f"Generated: {out_path}")
        except Exception as exc:
            self._set_status(f"Generate failed: {exc}")

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
                self._sync_project_data()
                save_project(self._project_path, self._project_data)
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
            self._diagnostics_tab.set_output(message)
            messagebox.showinfo("Validation", message)
            self._set_status("Validation complete.")
        except Exception as exc:
            messagebox.showerror("Validation Failed", str(exc))
            self._set_status(f"Validation failed: {exc}")

    def open_projects_folder(self) -> None:
        self._open_folder(PROJECTS_DIR, "projects")

    def open_output_folder(self) -> None:
        self._open_folder(OUTPUT_DIR, "output")

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

    def _sync_project_data(self) -> None:
        if not self._project_data:
            return
        self._inputs_tab.update_project(self._project_data)
        self._measures_tab.update_project(self._project_data)
        self._checklist_tab.update_project(self._project_data)

    def _on_catalog_saved(self, catalog) -> None:
        self._measures_tab.reload_catalog(catalog)
