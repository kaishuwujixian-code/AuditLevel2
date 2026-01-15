import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


DEFAULT_SCHEMA_PATH = Path("schemas/level1_questionnaire.schema.json")
DEFAULT_PROJECT_PATH = Path("project.json")


@dataclass
class QuestionWidget:
    question_id: str
    question_type: str
    widget: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


class QuestionnaireApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Questionnaire Builder")
        self.root.geometry("1024x768")
        self.schema_path_var = tk.StringVar(value=str(DEFAULT_SCHEMA_PATH))
        self.status_var = tk.StringVar(value="Ready")
        self._question_widgets: Dict[str, QuestionWidget] = {}
        self._schema_data: Optional[Dict[str, Any]] = None
        self._build_ui()
        self._load_schema(Path(self.schema_path_var.get()))

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(1, weight=1)

        select_button = ttk.Button(
            top_frame, text="Select schema…", command=self._select_schema
        )
        select_button.grid(row=0, column=0, sticky="w")

        schema_entry = ttk.Entry(
            top_frame, textvariable=self.schema_path_var, state="readonly"
        )
        schema_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        content_frame = ttk.Frame(self.root)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.rowconfigure(0, weight=1)
        content_frame.columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(content_frame, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(
            content_frame, orient="vertical", command=self._canvas.yview
        )
        self._scrollable_frame = ttk.Frame(self._canvas)

        self._scrollable_frame.bind(
            "<Configure>",
            lambda event: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            ),
        )
        self._canvas_frame = self._canvas.create_window(
            (0, 0), window=self._scrollable_frame, anchor="nw"
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.columnconfigure(1, weight=1)

        save_button = ttk.Button(
            bottom_frame, text="Save Project", command=self._save_project
        )
        save_button.grid(row=0, column=0, sticky="w")

        status_label = ttk.Label(bottom_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=1, sticky="e")

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfigure(self._canvas_frame, width=event.width)

    def _select_schema(self) -> None:
        path = filedialog.askopenfilename(
            title="Select schema JSON",
            initialfile=str(DEFAULT_SCHEMA_PATH),
            filetypes=[("Schema JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        self.schema_path_var.set(path)
        self._load_schema(Path(path))

    def _load_schema(self, path: Path) -> None:
        if not path.exists():
            messagebox.showerror("Schema not found", f"Missing schema: {path}")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            messagebox.showerror("Schema error", f"Invalid JSON: {exc}")
            return
        sections = data.get("sections")
        if not sections:
            messagebox.showerror("Schema error", "Schema has no sections.")
            return
        self._schema_data = data
        self._render_schema(sections)
        self.status_var.set(f"Loaded schema: {path}")

    def _render_schema(self, sections: List[Dict[str, Any]]) -> None:
        for child in self._scrollable_frame.winfo_children():
            child.destroy()
        self._question_widgets.clear()

        for section in sections:
            section_title = section.get("title", "Untitled Section")
            section_frame = ttk.LabelFrame(
                self._scrollable_frame, text=section_title, padding=10
            )
            section_frame.pack(fill="x", padx=10, pady=6)

            questions = section.get("questions", [])
            for question in questions:
                self._add_question(section_frame, question)

    def _add_question(self, parent: ttk.Frame, question: Dict[str, Any]) -> None:
        question_id = question.get("id", "")
        question_title = question.get("title", question_id)
        question_type = question.get("type", "text")

        question_frame = ttk.Frame(parent)
        question_frame.pack(fill="x", pady=6)

        label = ttk.Label(question_frame, text=question_title)
        label.pack(anchor="w")

        widget = self._create_question_widget(question_frame, question)
        if widget:
            self._question_widgets[question_id] = widget

    def _create_question_widget(
        self, parent: ttk.Frame, question: Dict[str, Any]
    ) -> Optional[QuestionWidget]:
        question_id = question.get("id", "")
        question_type = question.get("type", "text")

        if question_type == "text":
            var = tk.StringVar()
            entry = ttk.Entry(parent, textvariable=var)
            entry.pack(fill="x", pady=(4, 0))
            return QuestionWidget(question_id, question_type, var)

        if question_type == "notes":
            text = tk.Text(parent, height=4, wrap="word")
            text.pack(fill="x", pady=(4, 0))
            return QuestionWidget(question_id, question_type, text)

        if question_type == "single_select":
            options = question.get("options", [])
            labels = [opt.get("label", opt.get("value", "")) for opt in options]
            label_to_value = {
                opt.get("label", opt.get("value", "")): opt.get("value")
                for opt in options
            }
            var = tk.StringVar()
            combo = ttk.Combobox(parent, textvariable=var, values=labels, state="readonly")
            combo.pack(fill="x", pady=(4, 0))
            return QuestionWidget(
                question_id,
                question_type,
                var,
                metadata={"label_to_value": label_to_value},
            )

        if question_type == "measure_select":
            options = question.get("options", [])
            override_target = question.get("override_target", "measure_overrides")
            groups: Dict[str, List[Dict[str, str]]] = {}
            category_order: List[str] = []
            for opt in options:
                label = opt.get("label", opt.get("value", ""))
                value = opt.get("value")
                category = opt.get("category_label") or opt.get("category") or "Other / Misc"
                if category not in groups:
                    category_order.append(category)
                groups.setdefault(category, []).append({"label": label, "value": value})

            option_vars = []
            for category in category_order:
                frame = ttk.Labelframe(parent, text=category)
                frame.pack(fill="x", pady=(4, 0))
                frame.columnconfigure(1, weight=1)
                for idx, opt in enumerate(groups[category]):
                    var = tk.BooleanVar()
                    override_var = tk.StringVar()
                    check = ttk.Checkbutton(frame, text=opt["label"], variable=var)
                    check.grid(row=idx, column=0, sticky="w", padx=(4, 6), pady=2)
                    entry = ttk.Entry(frame, textvariable=override_var, state="disabled")
                    entry.grid(row=idx, column=1, sticky="ew", padx=(0, 4), pady=2)

                    def _toggle_entry(*_args, entry_widget=entry, value_var=var) -> None:
                        entry_widget.configure(
                            state="normal" if value_var.get() else "disabled"
                        )

                    var.trace_add("write", _toggle_entry)
                    option_vars.append((opt["value"], var, override_var))

            return QuestionWidget(
                question_id,
                question_type,
                option_vars,
                metadata={"override_target": override_target},
            )

        if question_type == "multi_select":
            options = question.get("options", [])
            option_vars = []
            options_frame = ttk.Frame(parent)
            options_frame.pack(fill="x", pady=(4, 0))
            for opt in options:
                label = opt.get("label", opt.get("value", ""))
                value = opt.get("value")
                var = tk.BooleanVar()
                check = ttk.Checkbutton(options_frame, text=label, variable=var)
                check.pack(anchor="w")
                option_vars.append((value, var))
            return QuestionWidget(
                question_id,
                question_type,
                option_vars,
            )

        if question_type == "image_list":
            container = ttk.Frame(parent)
            container.pack(fill="x", pady=(4, 0))
            listbox = tk.Listbox(container, height=4)
            listbox.pack(fill="x", pady=(0, 4))
            add_button = ttk.Button(
                container,
                text="Add photos…",
                command=lambda: self._add_photos(listbox),
            )
            add_button.pack(anchor="w")
            return QuestionWidget(
                question_id,
                question_type,
                listbox,
                metadata={"paths": []},
            )

        return None

    def _add_photos(self, listbox: tk.Listbox) -> None:
        paths = filedialog.askopenfilenames(
            title="Select photos",
            filetypes=[("Image files", "*.*"), ("All files", "*.*")],
        )
        if not paths:
            return
        question_id = self._find_question_id_by_widget(listbox)
        if not question_id:
            return
        widget = self._question_widgets[question_id]
        existing = widget.metadata.setdefault("paths", [])
        for path in paths:
            if path not in existing:
                existing.append(path)
                listbox.insert("end", path)

    def _find_question_id_by_widget(self, widget: Any) -> Optional[str]:
        for question_id, item in self._question_widgets.items():
            if item.widget is widget:
                return question_id
        return None

    def _extract_answer(self, widget: QuestionWidget) -> Any:
        if widget.question_type == "text":
            return widget.widget.get()
        if widget.question_type == "notes":
            return widget.widget.get("1.0", "end-1c")
        if widget.question_type == "single_select":
            label = widget.widget.get()
            mapping = widget.metadata.get("label_to_value", {})
            return mapping.get(label)
        if widget.question_type == "multi_select":
            selections = []
            for value, var in widget.widget:
                if var.get():
                    selections.append(value)
            return selections
        if widget.question_type == "measure_select":
            selections = []
            for value, var, _override in widget.widget:
                if var.get():
                    selections.append(value)
            return selections
        if widget.question_type == "image_list":
            return widget.metadata.get("paths", [])
        return None

    def _save_project(self) -> None:
        if not self._schema_data:
            messagebox.showerror("Save error", "No schema loaded.")
            return
        answers: Dict[str, Any] = {}
        photos: List[Dict[str, str]] = []
        for question_id, widget in self._question_widgets.items():
            value = self._extract_answer(widget)
            if widget.question_type == "image_list":
                for path in value:
                    photos.append({"path": path, "note": ""})
                continue
            answers[question_id] = value
            if widget.question_type == "measure_select":
                override_target = widget.metadata.get("override_target")
                if override_target:
                    overrides = {}
                    for measure_id, var, override_var in widget.widget:
                        if not var.get():
                            continue
                        text = override_var.get().strip()
                        if text:
                            overrides[measure_id] = text
                    if overrides:
                        answers[override_target] = overrides

        placeholders = self._build_placeholders(answers)

        payload = {
            "meta": {
                "schema_path": self.schema_path_var.get(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "answers": answers,
            "placeholders": placeholders,
            "photos": photos,
        }

        project_path = DEFAULT_PROJECT_PATH
        try:
            project_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save error", f"Failed to write project: {exc}")
            return

        self.status_var.set(f"Saved OK: {project_path.resolve()}")

    def _build_placeholders(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        if not self._schema_data:
            return {}
        sections = self._schema_data.get("sections", [])
        placeholder_values: Dict[str, Any] = {}
        for section in sections:
            for question in section.get("questions", []):
                question_id = question.get("id")
                if not question_id or question_id not in answers:
                    continue
                value = answers[question_id]
                for target in question.get("placeholder_targets", []):
                    placeholder_values[target] = value
        return placeholder_values
