from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.questionnaire import apply_answers_to_project, collect_template_placeholders
from reporting.narratives import load_option_sets
from ui.misc_panel import MiscPanel


@dataclass
class QuestionWidget:
    question_id: str
    question_type: str
    widget: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


class QuestionnairePanel(ttk.Frame):
    def __init__(self, master: tk.Misc, schema: Dict[str, Any]) -> None:
        super().__init__(master)
        self._schema = schema
        self._question_widgets: Dict[str, QuestionWidget] = {}
        self._template_widgets: Dict[str, QuestionWidget] = {}
        self._option_sets = load_option_sets()
        self._template_fields = collect_template_placeholders(schema)
        self._misc_panel: Optional[MiscPanel] = None
        self._notebook = ttk.Notebook(self)
        self._notebook.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_sections()

    def _build_sections(self) -> None:
        for child in self._notebook.winfo_children():
            child.destroy()
        self._question_widgets.clear()
        self._template_widgets.clear()

        general_tab = _ScrollableFrame(self._notebook)
        self._notebook.add(general_tab, text="General")

        system_tabs = {
            "heating": _ScrollableFrame(self._notebook),
            "cooling": _ScrollableFrame(self._notebook),
            "dhw": _ScrollableFrame(self._notebook),
            "ventilation": _ScrollableFrame(self._notebook),
        }
        self._notebook.add(system_tabs["heating"], text="Heating")
        self._notebook.add(system_tabs["cooling"], text="Cooling")
        self._notebook.add(system_tabs["dhw"], text="DHW")
        self._notebook.add(system_tabs["ventilation"], text="Ventilation")
        self._misc_panel = MiscPanel(self._notebook)
        self._notebook.add(self._misc_panel, text="Misc")

        general_container = general_tab.content
        section_frames: Dict[tuple[str, str], ttk.LabelFrame] = {}

        for section in self._schema.get("sections", []):
            if not isinstance(section, dict):
                continue
            section_id = str(section.get("id", "")).strip().lower()
            section_title = section.get("title", "Section")
            default_tab = section_id if section_id in system_tabs else "general"
            for question in section.get("questions", []):
                if question.get("type") in {"measure_select", "measure_list", "misc_list"}:
                    continue
                question_section = self._resolve_system_section(question)
                tab_key = question_section or default_tab
                if tab_key in system_tabs:
                    container = system_tabs[tab_key].content
                else:
                    container = general_container
                frame_key = (tab_key, section_title)
                if frame_key not in section_frames:
                    section_frames[frame_key] = self._build_form_section(
                        container, section_title
                    )
                self._add_question(section_frames[frame_key], question)

        template_frame = self._build_form_section(general_container, "Template Fields")
        if not self._template_fields:
            ttk.Label(
                template_frame, text="No additional template placeholders found."
            ).grid(row=0, column=0, sticky="w")
        else:
            for placeholder in self._template_fields:
                question = {
                    "id": placeholder,
                    "title": placeholder,
                    "type": "text",
                }
                self._add_question(template_frame, question, template_field=True)

    def _add_question(
        self,
        parent: ttk.Frame,
        question: Dict[str, Any],
        *,
        template_field: bool = False,
    ) -> None:
        question_id = str(question.get("id", "")).strip()
        if not question_id:
            return
        title = question.get("title") or question_id
        question_type = question.get("type", "text")

        row = getattr(parent, "next_row", 0)
        parent.next_row = row + 1
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=6)

        widget = self._create_question_widget(parent, question, row=row)
        if widget:
            if template_field:
                self._template_widgets[question_id] = widget
            else:
                self._question_widgets[question_id] = widget

    def _create_question_widget(
        self, parent: ttk.Frame, question: Dict[str, Any], *, row: int
    ) -> Optional[QuestionWidget]:
        question_id = question.get("id", "")
        question_type = question.get("type", "text")
        options = question.get("options", [])
        options_ref = question.get("options_ref")
        if not options and options_ref:
            option_set = self._option_sets.get(options_ref, {})
            options = [
                {"label": label, "value": value} for value, label in option_set.items()
            ]

        if question_type in {"text", "number", "date"}:
            var = tk.StringVar()
            entry = ttk.Entry(parent, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", pady=6)
            return QuestionWidget(question_id, question_type, var)

        if question_type == "notes":
            text = tk.Text(parent, height=4, wrap="word")
            text.grid(row=row, column=1, sticky="ew", pady=6)
            return QuestionWidget(question_id, question_type, text)

        if question_type == "single_select":
            labels = [opt.get("label", opt.get("value", "")) for opt in options]
            label_to_value = {
                opt.get("label", opt.get("value", "")): opt.get("value")
                for opt in options
            }
            value_to_label = {
                opt.get("value"): opt.get("label", opt.get("value", ""))
                for opt in options
            }
            var = tk.StringVar()
            container = ttk.Frame(parent)
            container.grid(row=row, column=1, sticky="ew", pady=6)
            container.columnconfigure(0, weight=1)
            combo = ttk.Combobox(
                container, textvariable=var, values=labels, state="readonly"
            )
            combo.grid(row=0, column=0, sticky="ew")

            writeup = question.get("writeup")
            if _has_writeup(writeup):
                writeup_var = tk.StringVar()
                writeup_label = ttk.Label(
                    container, textvariable=writeup_var, wraplength=640
                )
                writeup_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

                def _update_writeup(*_args) -> None:
                    selected_label = var.get()
                    value = label_to_value.get(selected_label)
                    writeup_var.set(_resolve_writeup_text(writeup, value, selected_label))

                var.trace_add("write", _update_writeup)
                _update_writeup()
            return QuestionWidget(
                question_id,
                question_type,
                var,
                metadata={"label_to_value": label_to_value, "value_to_label": value_to_label},
            )

        if question_type == "multi_select":
            option_vars = []
            options_frame = ttk.Frame(parent)
            options_frame.grid(row=row, column=1, sticky="ew", pady=6)
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

        return None

    def load_project(self, project_data: Dict[str, Any]) -> None:
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        project_info = project_data.get("project_info", {})
        if not isinstance(project_info, dict):
            project_info = {}
        placeholders = project_data.get("placeholders", {})
        if not isinstance(placeholders, dict):
            placeholders = {}

        for question_id, widget in self._question_widgets.items():
            value = answers.get(question_id, project_info.get(question_id, ""))
            self._set_widget_value(widget, value)

        for placeholder, widget in self._template_widgets.items():
            value = placeholders.get(placeholder, "")
            self._set_widget_value(widget, value)
        if self._misc_panel:
            self._misc_panel.load_project(project_data)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        for question_id, widget in self._question_widgets.items():
            answers[question_id] = self._extract_answer(widget)

        template_fields: Dict[str, Any] = {}
        for placeholder, widget in self._template_widgets.items():
            template_fields[placeholder] = self._extract_answer(widget)

        apply_answers_to_project(project_data, answers, self._schema, template_fields)
        if self._misc_panel:
            self._misc_panel.update_project(project_data)

    def _extract_answer(self, widget: QuestionWidget) -> Any:
        if widget.question_type in {"text", "number", "date"}:
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
        return None

    def _set_widget_value(self, widget: QuestionWidget, value: Any) -> None:
        if widget.question_type in {"text", "number", "date"}:
            widget.widget.set("" if value is None else str(value))
        elif widget.question_type == "notes":
            widget.widget.delete("1.0", tk.END)
            if value:
                widget.widget.insert("1.0", str(value))
        elif widget.question_type == "single_select":
            value_to_label = widget.metadata.get("value_to_label", {})
            label = value_to_label.get(value, "" if value is None else str(value))
            widget.widget.set(label)
        elif widget.question_type == "multi_select":
            values = set(value or [])
            for option_value, var in widget.widget:
                var.set(option_value in values)

    def _build_form_section(self, parent: ttk.Frame, title: str) -> ttk.LabelFrame:
        section_frame = ttk.LabelFrame(parent, text=title, padding=10)
        section_frame.pack(fill="x", padx=10, pady=6)
        section_frame.columnconfigure(1, weight=1)
        section_frame.next_row = 0
        return section_frame

    def _resolve_system_section(self, question: Dict[str, Any]) -> str:
        question_id = str(question.get("id", "")).strip().lower()
        section_id = str(question.get("section_id", "")).strip().lower()
        for system in ("heating", "cooling", "dhw", "ventilation"):
            if question_id.startswith(f"{system}_") or section_id == system:
                return system
        return ""


class _ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.content = ttk.Frame(self._canvas)

        self._canvas_frame = self._canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        self.content.bind(
            "<Configure>",
            lambda event: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfigure(self._canvas_frame, width=event.width)


def _has_writeup(writeup: object) -> bool:
    if isinstance(writeup, dict):
        return any(str(value).strip() for value in writeup.values())
    if isinstance(writeup, str):
        return bool(writeup.strip())
    return False


def _resolve_writeup_text(writeup: object, value: object, label: str) -> str:
    if isinstance(writeup, dict):
        if value is not None and value in writeup:
            return str(writeup[value]).strip()
        if label and label in writeup:
            return str(writeup[label]).strip()
        return ""
    if isinstance(writeup, str):
        return writeup.strip()
    return ""
