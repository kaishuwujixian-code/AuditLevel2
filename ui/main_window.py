import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional

from core.paths import DEFAULT_TEMPLATE_DOCX, DEFAULT_TEMPLATE_JSON, OUTPUT_DIR, PROJECTS_DIR
from core.project_store import load_project, save_project
from core.template_store import load_template
from reporting.level1_generator import generate_level1_report
from ui.widgets import LabeledCombo, LabeledEntry, LabeledText, MultiSelectList, SummaryBox
from ui.bindings import AppBindings


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Level 1 Project Editor")
        self.root.geometry("1200x720")

        self.project_data: Dict = {}
        self.project_path: Optional[str] = None
        self.schema: Dict = {}
        self.template = load_template(DEFAULT_TEMPLATE_JSON)

        self._fields: Dict[str, List] = {}
        self._multi_fields: Dict[str, MultiSelectList] = {}

        self.bindings = AppBindings(self)
        self._build_menu()
        self._build_layout()
        self._load_schema()
        self.new_project()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.bindings.new_project)
        file_menu.add_command(label="Open", command=self.bindings.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.bindings.save_project)
        file_menu.add_command(label="Save As", command=self.bindings.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Validate Project", command=self.bindings.validate_project)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        report_menu = tk.Menu(menubar, tearoff=0)
        report_menu.add_command(label="Generate Level 1", command=self.bindings.generate_report)
        menubar.add_cascade(label="Report", menu=report_menu)

        self.root.config(menu=menubar)

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        paned = ttk.PanedWindow(container, orient="horizontal")
        paned.pack(fill="both", expand=True)

        nav_frame = ttk.Frame(paned, padding=(8, 8))
        paned.add(nav_frame, weight=1)

        self.nav_tree = ttk.Treeview(nav_frame, show="tree")
        self.nav_tree.pack(fill="both", expand=True)
        self._build_nav_tree()
        self.nav_tree.bind("<<TreeviewSelect>>", self._on_nav_select)

        content_frame = ttk.Frame(paned, padding=(8, 8))
        paned.add(content_frame, weight=3)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)

        self.summary_box = SummaryBox(content_frame)
        self.summary_box.grid(row=0, column=0, sticky="ew")

        self.section_container = ttk.Frame(content_frame)
        self.section_container.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.section_container.columnconfigure(0, weight=1)
        self.section_container.rowconfigure(0, weight=1)

        self.log_text = tk.Text(content_frame, height=6, wrap="word")
        self.log_text.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.log_text.configure(state="disabled")

        self._sections: Dict[str, ttk.Frame] = {}

    def _build_nav_tree(self) -> None:
        self.nav_tree.delete(*self.nav_tree.get_children())
        root_id = self.nav_tree.insert("", "end", text="Project")
        self.nav_tree.insert(root_id, "end", text="Project Info", values=("project_info",))
        systems_id = self.nav_tree.insert(root_id, "end", text="Building Systems", open=True)
        self.nav_tree.insert(systems_id, "end", text="Heating", values=("heating",))
        self.nav_tree.insert(systems_id, "end", text="DHW", values=("dhw",))
        self.nav_tree.insert(systems_id, "end", text="Cooling", values=("cooling",))
        self.nav_tree.insert(systems_id, "end", text="Ventilation", values=("ventilation",))
        self.nav_tree.insert(root_id, "end", text="Measures", values=("measures",))
        self.nav_tree.insert(root_id, "end", text="Checklist / Findings", values=("findings",))
        self.nav_tree.insert(root_id, "end", text="Photos / Notes", values=("notes",))
        self.nav_tree.item(root_id, open=True)
        self.nav_tree.selection_set(self.nav_tree.get_children(root_id)[0])

    def _load_schema(self) -> None:
        schema_path = os.path.join("schemas", "level1_questionnaire.schema.json")
        if not os.path.isfile(schema_path):
            self.schema = {"sections": []}
            return
        with open(schema_path, "r", encoding="utf-8") as handle:
            self.schema = json.load(handle)

    def _schema_section(self, section_id: str) -> Optional[dict]:
        for section in self.schema.get("sections", []):
            if section.get("id") == section_id:
                return section
        return None

    def new_project(self) -> None:
        self.project_data = {
            "project_info": {
                "client_name": "",
                "site_address": "",
                "building_name": "",
                "report_date": "",
                "prepared_by": "",
            },
            "selected_measures": [],
            "notes": {"general_site_notes": ""},
        }
        self.project_path = None
        self._build_sections()
        self._refresh_summary()
        self.log_message("Started new project.")

    def load_project(self, path: str) -> None:
        data = load_project(path)
        if not isinstance(data, dict):
            raise ValueError("Project JSON must be an object.")
        self.project_data = data
        self.project_path = path
        self._build_sections()
        self._refresh_summary()
        self.log_message(f"Loaded project: {path}")

    def save_project(self, path: Optional[str] = None) -> None:
        target_path = path or self.project_path
        if not target_path:
            raise ValueError("No project path specified.")
        self._sync_fields_to_project()
        save_project(target_path, self.project_data)
        self.project_path = target_path
        self._refresh_summary()
        self.log_message(f"Saved project: {target_path}")

    def log_message(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

    def _build_sections(self) -> None:
        for child in self.section_container.winfo_children():
            child.destroy()
        self._sections.clear()
        self._fields.clear()
        self._multi_fields.clear()

        self._sections["project_info"] = self._build_project_info_section()
        self._sections["heating"] = self._build_system_section("heating", "Heating")
        self._sections["dhw"] = self._build_system_section("dhw", "Domestic Hot Water")
        self._sections["cooling"] = self._build_system_section("cooling", "Cooling")
        self._sections["ventilation"] = self._build_system_section("ventilation", "Ventilation")
        self._sections["measures"] = self._build_measures_section()
        self._sections["findings"] = self._build_findings_section()
        self._sections["notes"] = self._build_notes_section()

        self.show_section("project_info")

    def show_section(self, section_id: str) -> None:
        for frame in self._sections.values():
            frame.grid_forget()
        frame = self._sections.get(section_id)
        if frame:
            frame.grid(row=0, column=0, sticky="nsew")

    def _build_project_info_section(self) -> ttk.Frame:
        frame = ttk.Frame(self.section_container)
        frame.columnconfigure(0, weight=1)
        info = self.project_data.setdefault("project_info", {})

        fields = [
            ("client_name", "Client name"),
            ("site_address", "Site address"),
            ("building_name", "Building name"),
            ("report_date", "Report date"),
            ("prepared_by", "Prepared by"),
        ]
        self._fields["project_info"] = []
        for row, (key, label) in enumerate(fields):
            widget = LabeledEntry(frame, label)
            widget.grid(row=row, column=0, sticky="ew", pady=4)
            widget.set(str(info.get(key, "")))
            self._fields["project_info"].append((key, widget))
        return frame

    def _build_system_section(self, section_id: str, title: str) -> ttk.Frame:
        frame = ttk.Frame(self.section_container)
        frame.columnconfigure(0, weight=1)
        section = self._schema_section(section_id)
        system_data = self.project_data.setdefault("building_systems", {})
        section_values = system_data.setdefault(section_id, {})
        self._fields[section_id] = []
        ttk.Label(frame, text=title, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        if not section:
            ttk.Label(frame, text="No schema entries for this section.").grid(row=1, column=0, sticky="w")
            return frame
        for idx, question in enumerate(section.get("questions", []), start=1):
            options = [option["label"] for option in question.get("options", [])]
            widget = LabeledCombo(frame, question.get("title", question.get("id", "")), options)
            widget.grid(row=idx, column=0, sticky="ew", pady=4)
            widget.set(str(section_values.get(question.get("id"), "")))
            self._fields[section_id].append((question.get("id"), widget))
        return frame

    def _build_measures_section(self) -> ttk.Frame:
        frame = ttk.Frame(self.section_container)
        frame.columnconfigure(0, weight=1)
        measures = sorted(self.template.measures.keys())
        widget = MultiSelectList(frame, "Selected measures", measures, height=12)
        widget.grid(row=0, column=0, sticky="nsew")
        widget.set(self.project_data.get("selected_measures", []))
        self._multi_fields["selected_measures"] = widget
        return frame

    def _build_findings_section(self) -> ttk.Frame:
        frame = ttk.Frame(self.section_container)
        frame.columnconfigure(0, weight=1)
        section = self._schema_section("findings")
        findings = self.project_data.setdefault("findings", {})
        self._fields["findings"] = []
        if not section:
            ttk.Label(frame, text="No findings schema entries.").grid(row=0, column=0, sticky="w")
            return frame
        for idx, question in enumerate(section.get("questions", [])):
            if question.get("type") in {"multi_select"}:
                options = [option["label"] for option in question.get("options", [])]
                widget = MultiSelectList(frame, question.get("title", question.get("id", "")), options)
                widget.grid(row=idx, column=0, sticky="nsew", pady=4)
                widget.set(findings.get(question.get("id"), []))
                self._multi_fields[question.get("id")] = widget
            elif question.get("type") in {"notes", "text"}:
                widget = LabeledText(frame, question.get("title", question.get("id", "")), height=4)
                widget.grid(row=idx, column=0, sticky="nsew", pady=4)
                widget.set(str(findings.get(question.get("id"), "")))
                self._fields["findings"].append((question.get("id"), widget))
            else:
                options = [option["label"] for option in question.get("options", [])]
                widget = LabeledCombo(frame, question.get("title", question.get("id", "")), options)
                widget.grid(row=idx, column=0, sticky="ew", pady=4)
                widget.set(str(findings.get(question.get("id"), "")))
                self._fields["findings"].append((question.get("id"), widget))
        return frame

    def _build_notes_section(self) -> ttk.Frame:
        frame = ttk.Frame(self.section_container)
        frame.columnconfigure(0, weight=1)
        notes = self.project_data.setdefault("notes", {})
        widget = LabeledText(frame, "General site notes", height=8)
        widget.grid(row=0, column=0, sticky="nsew")
        widget.set(str(notes.get("general_site_notes", "")))
        self._fields["notes"] = [("general_site_notes", widget)]
        return frame

    def _sync_fields_to_project(self) -> None:
        info = self.project_data.setdefault("project_info", {})
        for key, widget in self._fields.get("project_info", []):
            info[key] = widget.get()

        systems = self.project_data.setdefault("building_systems", {})
        for section_id in ("heating", "dhw", "cooling", "ventilation"):
            section_values = systems.setdefault(section_id, {})
            for key, widget in self._fields.get(section_id, []):
                section_values[key] = widget.get()

        findings = self.project_data.setdefault("findings", {})
        for key, widget in self._fields.get("findings", []):
            findings[key] = widget.get()

        notes = self.project_data.setdefault("notes", {})
        for key, widget in self._fields.get("notes", []):
            notes[key] = widget.get()

        for question_id, widget in self._multi_fields.items():
            values = widget.get()
            if question_id == "selected_measures":
                self.project_data["selected_measures"] = values
            else:
                findings = self.project_data.setdefault("findings", {})
                findings[question_id] = values

    def _refresh_summary(self) -> None:
        info = self.project_data.get("project_info", {})
        selected = self.project_data.get("selected_measures", [])
        checklist = self.project_data.get("checklist_selections", {})
        checklist_count = 0
        if isinstance(checklist, dict):
            for group in checklist.values():
                if isinstance(group, dict):
                    for items in group.values():
                        if isinstance(items, list):
                            checklist_count += len(items)
        self.summary_box.update(
            building=str(info.get("building_name", "")),
            address=str(info.get("site_address", "")),
            measures_count=len(selected) if isinstance(selected, list) else 0,
            checklist_count=checklist_count,
        )

    def _on_nav_select(self, _event: tk.Event) -> None:
        selection = self.nav_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        values = self.nav_tree.item(item_id).get("values", [])
        if values:
            self.show_section(values[0])

    def generate_report(self) -> None:
        if not self.project_path:
            raise ValueError("Save the project before generating.")
        self._sync_fields_to_project()
        save_project(self.project_path, self.project_data)
        docx_path = self.project_data.get("docx_template_path") or DEFAULT_TEMPLATE_DOCX
        if not os.path.isfile(docx_path):
            raise FileNotFoundError(f"Docx template not found: {docx_path}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        slug = self._slugify(self.project_data.get("project_info", {}).get("building_name", "project"))
        out_path = os.path.join(OUTPUT_DIR, f"{slug}_level1_walkthrough.docx")
        generate_level1_report(self.project_path, DEFAULT_TEMPLATE_JSON, docx_path, out_path)
        self.log_message(f"Generated report: {out_path}")

    @staticmethod
    def _slugify(value: str) -> str:
        slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug or "project"
