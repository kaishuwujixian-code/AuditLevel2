import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from core.paths import (
    DEFAULT_TEMPLATE_DOCX,
    DEFAULT_TEMPLATE_JSON,
    OUTPUT_DIR,
    PROJECTS_DIR,
)
from core.project_store import ProjectRecord, default_output_path, scan_projects
from reporting.level1_generator import generate_level1_report
from tools.site_wizard import (
    clone_project_interactive,
    create_new_project_interactive,
    reuse_project_interactive,
)


class ProjectBrowserApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Level 1 Project Browser")
        self._records: list[ProjectRecord] = []
        self._record_by_id: dict[str, ProjectRecord] = {}
        self._status_var = tk.StringVar(value="Ready")
        self._build_ui()
        self.refresh_projects()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, padding=(8, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)

        button_frame = ttk.Frame(toolbar)
        button_frame.grid(row=0, column=0, sticky="w")

        ttk.Button(button_frame, text="Refresh", command=self.refresh_projects).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(button_frame, text="New", command=self.create_new_project).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(button_frame, text="Clone", command=self.clone_project).grid(
            row=0, column=2, padx=(0, 6)
        )
        ttk.Button(button_frame, text="Reuse", command=self.reuse_project).grid(
            row=0, column=3, padx=(0, 6)
        )
        ttk.Button(button_frame, text="Generate", command=self.generate_selected).grid(
            row=0, column=4, padx=(0, 6)
        )
        ttk.Button(
            button_frame,
            text="Open Output Folder",
            command=self.open_output_folder,
        ).grid(row=0, column=5)

        tree_frame = ttk.Frame(self.root, padding=(8, 0, 8, 0))
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ("building", "address", "report_date", "measures", "path")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("building", text="Building Name")
        self.tree.heading("address", text="Address")
        self.tree.heading("report_date", text="Report Date")
        self.tree.heading("measures", text="Measures (#)")
        self.tree.heading("path", text="Path")

        self.tree.column("building", width=180, anchor="w")
        self.tree.column("address", width=240, anchor="w")
        self.tree.column("report_date", width=120, anchor="w")
        self.tree.column("measures", width=90, anchor="center")
        self.tree.column("path", width=320, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_double_click)

        status_bar = ttk.Label(
            self.root,
            textvariable=self._status_var,
            anchor="w",
            relief="sunken",
            padding=(8, 4),
        )
        status_bar.grid(row=2, column=0, sticky="ew")

    def set_status(self, message: str, error: bool = False) -> None:
        self._status_var.set(message)
        if error:
            self._status_var.set(f"Error: {message}")

    def refresh_projects(self, update_status: bool = True) -> None:
        try:
            records, errors = scan_projects(PROJECTS_DIR)
            self._records = records
            self._populate_tree()
            if update_status:
                message = f"Loaded {len(records)} project(s)."
                if errors:
                    message += f" {len(errors)} file(s) skipped."
                    for error in errors:
                        print(error)
                self.set_status(message)
            else:
                for error in errors:
                    print(error)
        except Exception as exc:
            self.set_status(str(exc), error=True)

    def _populate_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._record_by_id.clear()
        for record in self._records:
            item_id = self.tree.insert(
                "",
                "end",
                values=(
                    record.building_name,
                    record.address,
                    record.report_date,
                    record.measures_count,
                    record.path,
                ),
            )
            self._record_by_id[item_id] = record

    def _get_selected_record(self) -> ProjectRecord | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self._record_by_id.get(selection[0])

    def _ensure_templates(self) -> bool:
        if not os.path.isfile(DEFAULT_TEMPLATE_JSON):
            self.set_status(
                f"Template JSON missing: {DEFAULT_TEMPLATE_JSON}", error=True
            )
            return False
        if not os.path.isfile(DEFAULT_TEMPLATE_DOCX):
            self.set_status(
                f"Template DOCX missing: {DEFAULT_TEMPLATE_DOCX}", error=True
            )
            return False
        return True

    def _generate_report_for_record(self, record: ProjectRecord) -> None:
        if not self._ensure_templates():
            return
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = default_output_path(record, OUTPUT_DIR)
        generate_level1_report(
            record.path,
            DEFAULT_TEMPLATE_JSON,
            DEFAULT_TEMPLATE_DOCX,
            out_path,
        )
        self.set_status(f"Generated report: {out_path}")

    def generate_selected(self) -> None:
        try:
            record = self._get_selected_record()
            if not record:
                self.set_status("Select a project to generate.")
                return
            self._generate_report_for_record(record)
        except Exception as exc:
            self.set_status(str(exc), error=True)

    def _on_double_click(self, _event: tk.Event) -> None:
        self.generate_selected()

    def create_new_project(self) -> None:
        try:
            if not self._ensure_templates():
                return
            output_path = create_new_project_interactive(DEFAULT_TEMPLATE_JSON, "")
            self.refresh_projects(update_status=False)
            self.set_status(f"Created project: {output_path}")
        except Exception as exc:
            self.set_status(str(exc), error=True)

    def clone_project(self) -> None:
        try:
            record = self._get_selected_record()
            if not record:
                self.set_status("Select a project to clone.")
                return
            if not self._ensure_templates():
                return
            output_path = clone_project_interactive(
                record.path, DEFAULT_TEMPLATE_JSON, ""
            )
            self.refresh_projects(update_status=False)
            self.set_status(f"Cloned project: {output_path}")
        except Exception as exc:
            self.set_status(str(exc), error=True)

    def reuse_project(self) -> None:
        try:
            record = self._get_selected_record()
            if not record:
                self.set_status("Select a project to reuse.")
                return
            if not self._ensure_templates():
                return
            output_path = reuse_project_interactive(
                record.path, DEFAULT_TEMPLATE_JSON, ""
            )
            self.refresh_projects(update_status=False)
            self.set_status(f"Reused project: {output_path}")
        except Exception as exc:
            self.set_status(str(exc), error=True)

    def open_output_folder(self) -> None:
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(OUTPUT_DIR)
            elif sys.platform == "darwin":
                subprocess.run(["open", OUTPUT_DIR], check=False)
            else:
                subprocess.run(["xdg-open", OUTPUT_DIR], check=False)
            self.set_status(f"Opened output folder: {OUTPUT_DIR}")
        except Exception as exc:
            self.set_status(str(exc), error=True)
