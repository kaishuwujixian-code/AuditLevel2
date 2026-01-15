from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.questionnaire import apply_answers_to_project, collect_template_placeholders


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
        self._template_fields = collect_template_placeholders(schema)
        self._scrollable = _ScrollableFrame(self)
        self._scrollable.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_sections()

    def _build_sections(self) -> None:
        container = self._scrollable.content
        for child in container.winfo_children():
            child.destroy()
        self._question_widgets.clear()
        self._template_widgets.clear()

        for section in self._schema.get("sections", []):
            section_frame = ttk.LabelFrame(
                container, text=section.get("title", "Section"), padding=10
            )
            section_frame.pack(fill="x", padx=10, pady=6)
            for question in section.get("questions", []):
                if question.get("type") == "measure_select":
                    continue
                self._add_question(section_frame, question)

        template_frame = ttk.LabelFrame(container, text="Template Fields", padding=10)
        template_frame.pack(fill="x", padx=10, pady=6)
        if not self._template_fields:
            ttk.Label(template_frame, text="No additional template placeholders found.").pack(anchor="w")
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

        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=6)
        ttk.Label(frame, text=title).pack(anchor="w")

        widget = self._create_question_widget(frame, question)
        if widget:
            if template_field:
                self._template_widgets[question_id] = widget
            else:
                self._question_widgets[question_id] = widget

    def _create_question_widget(
        self, parent: ttk.Frame, question: Dict[str, Any]
    ) -> Optional[QuestionWidget]:
        question_id = question.get("id", "")
        question_type = question.get("type", "text")

        if question_type in {"text", "number", "date"}:
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
            value_to_label = {
                opt.get("value"): opt.get("label", opt.get("value", ""))
                for opt in options
            }
            var = tk.StringVar()
            combo = ttk.Combobox(parent, textvariable=var, values=labels, state="readonly")
            combo.pack(fill="x", pady=(4, 0))
            return QuestionWidget(
                question_id,
                question_type,
                var,
                metadata={"label_to_value": label_to_value, "value_to_label": value_to_label},
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
