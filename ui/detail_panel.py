import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional

from core.template_store import TemplateData


class DetailPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(8, 6))
        self._project_data: Optional[Dict] = None
        self._template: Optional[TemplateData] = None
        self._current_measure_key: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)

        info_frame = ttk.LabelFrame(self, text="Project Info", padding=(6, 4))
        info_frame.grid(row=0, column=0, sticky="ew")
        info_frame.columnconfigure(1, weight=1)

        labels = [
            "Client",
            "Address",
            "Report Date",
            "Prepared By",
        ]
        self._info_vars = {label: tk.StringVar(value="-") for label in labels}
        for idx, label in enumerate(labels):
            ttk.Label(info_frame, text=f"{label}:").grid(row=idx, column=0, sticky="w")
            ttk.Label(info_frame, textvariable=self._info_vars[label]).grid(
                row=idx, column=1, sticky="w"
            )

        checklist_frame = ttk.LabelFrame(self, text="Checklist Summary", padding=(6, 4))
        checklist_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        checklist_frame.columnconfigure(0, weight=1)
        self._checklist_text = tk.Text(checklist_frame, height=6, wrap="word")
        self._checklist_text.grid(row=0, column=0, sticky="nsew")
        self._checklist_text.configure(state="disabled")

        measure_frame = ttk.LabelFrame(self, text="Measure Preview", padding=(6, 4))
        measure_frame.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        measure_frame.columnconfigure(0, weight=1)
        self._measure_text = tk.Text(measure_frame, height=10, wrap="word")
        self._measure_text.grid(row=0, column=0, sticky="nsew")
        self._measure_text.configure(state="disabled")

        notes_frame = ttk.LabelFrame(self, text="General Site Notes", padding=(6, 4))
        notes_frame.grid(row=3, column=0, sticky="nsew", pady=(6, 0))
        notes_frame.columnconfigure(0, weight=1)
        self._notes_text = tk.Text(notes_frame, height=6, wrap="word")
        self._notes_text.grid(row=0, column=0, sticky="nsew")

        self.rowconfigure(2, weight=1)

    def load_project(self, template: TemplateData, project_data: Dict) -> None:
        self._template = template
        self._project_data = project_data
        project_info = project_data.get("project_info", {})
        if not isinstance(project_info, dict):
            project_info = {}
        self._info_vars["Client"].set(str(project_info.get("client_name", "-")))
        self._info_vars["Address"].set(str(project_info.get("site_address", "-")))
        self._info_vars["Report Date"].set(str(project_info.get("report_date", "-")))
        self._info_vars["Prepared By"].set(str(project_info.get("prepared_by", "-")))

        checklist_summary = self._build_checklist_summary(project_data)
        self._update_text(self._checklist_text, checklist_summary)

        notes = project_data.get("notes", {})
        if not isinstance(notes, dict):
            notes = {}
        self._notes_text.delete("1.0", tk.END)
        self._notes_text.insert("1.0", str(notes.get("general_site_notes", "")))

        self.set_measure_preview(None)

    def set_measure_preview(self, measure_key: Optional[str]) -> None:
        self._current_measure_key = measure_key
        if not measure_key or not self._template:
            self._update_text(self._measure_text, "Select a measure to preview details.")
            return
        measure = self._template.measures.get(measure_key, {})
        name = measure.get("name", measure_key)
        existing = measure.get("existing", "")
        retrofit = measure.get("retrofit", "")
        summary = measure.get("summary", "")
        parts = [f"{name}\n", f"Key: {measure_key}\n"]
        if summary:
            parts.append(f"Summary:\n{summary}\n")
        if existing:
            parts.append(f"Existing:\n{existing}\n")
        if retrofit:
            parts.append(f"Retrofit:\n{retrofit}\n")
        self._update_text(self._measure_text, "\n".join(parts).strip())

    def update_project_notes(self) -> None:
        if not self._project_data:
            return
        notes = self._project_data.get("notes", {})
        if not isinstance(notes, dict):
            notes = {}
        notes["general_site_notes"] = self._notes_text.get("1.0", tk.END).strip()
        self._project_data["notes"] = notes

    def _build_checklist_summary(self, project_data: Dict) -> str:
        selections = project_data.get("checklist_selections", {})
        if not selections:
            return "No checklist selections."
        if not isinstance(selections, dict):
            return "Invalid checklist data."
        lines = []
        for group_name in sorted(selections.keys()):
            lines.append(group_name)
            categories = selections[group_name]
            if not isinstance(categories, dict):
                continue
            for category_name in sorted(categories.keys()):
                items = categories[category_name]
                if not isinstance(items, list):
                    continue
                joined = ", ".join(items) if items else "(none)"
                lines.append(f"  - {category_name}: {joined}")
        return "\n".join(lines)

    def _update_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state="disabled")
