from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.questionnaire import apply_answers_to_project, collect_template_placeholders
from reporting.narratives import load_option_sets
from ui.library_items_panel import LibraryItemsPanel
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
        self._question_definitions: Dict[str, Dict[str, Any]] = {}
        self._section_questions: Dict[ttk.LabelFrame, list[str]] = {}
        self._section_order: Dict[ttk.Frame, list[ttk.LabelFrame]] = {}
        self._question_visibility: Dict[str, bool] = {}
        self._tab_frames: Dict[str, ttk.Frame] = {}
        self._option_sets = load_option_sets()
        self._template_fields = collect_template_placeholders(schema)
        self._misc_panel: Optional[MiscPanel] = None
        self._system_library_panels: Dict[str, LibraryItemsPanel] = {}
        self._catalog_panel_by_filename: Dict[str, LibraryItemsPanel] = {}
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        ttk.Button(toolbar, text="Clear Current Tab", command=self._clear_current_tab).pack(
            side="right"
        )
        self._notebook = ttk.Notebook(self)
        self._notebook.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_sections()

    def _build_sections(self) -> None:
        for child in self._notebook.winfo_children():
            child.destroy()
        self._question_widgets.clear()
        self._template_widgets.clear()
        self._question_definitions.clear()
        self._section_questions.clear()
        self._section_order.clear()
        self._question_visibility.clear()

        general_tab = _ScrollableFrame(self._notebook)
        self._notebook.add(general_tab, text="General")
        self._tab_frames["general"] = general_tab.content

        self._system_library_panels = {
            "heating": LibraryItemsPanel(
                self._notebook,
                storage_key="heating_items",
                catalog_filename="heating_catalog.json",
                title="Heating Library",
                item_label="Heating",
            ),
            "cooling": LibraryItemsPanel(
                self._notebook,
                storage_key="cooling_items",
                catalog_filename="cooling_catalog.json",
                title="Cooling Library",
                item_label="Cooling",
            ),
            "dhw": LibraryItemsPanel(
                self._notebook,
                storage_key="dhw_items",
                catalog_filename="dhw_catalog.json",
                title="DHW Library",
                item_label="DHW",
            ),
            "ventilation": LibraryItemsPanel(
                self._notebook,
                storage_key="ventilation_items",
                catalog_filename="ventilation_catalog.json",
                title="Ventilation Library",
                item_label="Ventilation",
            ),
        }
        self._catalog_panel_by_filename = {
            "heating_catalog.json": self._system_library_panels["heating"],
            "cooling_catalog.json": self._system_library_panels["cooling"],
            "dhw_catalog.json": self._system_library_panels["dhw"],
            "ventilation_catalog.json": self._system_library_panels["ventilation"],
        }

        self._notebook.add(self._system_library_panels["heating"], text="Heating")
        self._notebook.add(self._system_library_panels["cooling"], text="Cooling")
        self._notebook.add(self._system_library_panels["dhw"], text="DHW")
        self._notebook.add(self._system_library_panels["ventilation"], text="Ventilation")
        self._misc_panel = MiscPanel(self._notebook)
        self._notebook.add(self._misc_panel, text="Misc")

        general_container = general_tab.content
        section_frames: Dict[tuple[str, str], ttk.LabelFrame] = {}

        for section in self._schema.get("sections", []):
            if not isinstance(section, dict):
                continue
            section_id = str(section.get("id", "")).strip().lower()
            section_title = section.get("title", "Section")
            default_tab = section_id if section_id in self._system_library_panels else "general"
            for question in section.get("questions", []):
                if question.get("type") in {"measure_select", "measure_list", "misc_list"}:
                    continue
                question_section = self._resolve_system_section(question)
                tab_key = question_section or default_tab
                if tab_key in self._system_library_panels:
                    continue
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
        self._setup_visibility_handlers()
        self._apply_visibility()
        self._notebook.select(general_tab)

    def _clear_current_tab(self) -> None:
        selected = self._notebook.select()
        if not selected:
            return
        tab = self._notebook.nametowidget(selected)
        if self._misc_panel and tab is self._misc_panel:
            self._misc_panel.clear_items()
            return
        for panel in self._system_library_panels.values():
            if tab is panel:
                panel.clear_items()
                return
        if isinstance(tab, _ScrollableFrame):
            self._clear_tab_widgets(tab.content)
            return

    def _clear_tab_widgets(self, container: ttk.Frame) -> None:
        for widget in list(self._question_widgets.values()) + list(self._template_widgets.values()):
            row_frame = widget.metadata.get("row_frame")
            if not row_frame or not _is_descendant(row_frame, container):
                continue
            self._clear_widget_value(widget)
        self._apply_visibility()

    def _clear_widget_value(self, widget: QuestionWidget) -> None:
        if widget.question_type in {"text", "number", "date"}:
            widget.widget.set("")
        elif widget.question_type == "notes":
            widget.widget.delete("1.0", tk.END)
        elif widget.question_type == "single_select":
            widget.widget.set("")
        elif widget.question_type == "multi_select":
            for _value, var in widget.widget:
                var.set(False)
        elif widget.question_type == "boiler_groups":
            self._set_boiler_group_rows(widget, [])

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
        self._question_definitions[question_id] = question
        title = question.get("title") or question_id
        question_type = question.get("type", "text")

        row = getattr(parent, "next_row", 0)
        parent.next_row = row + 1
        row_frame = ttk.Frame(parent)
        row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row_frame.columnconfigure(1, weight=1)
        ttk.Label(row_frame, text=title).grid(row=0, column=0, sticky="nw", padx=(0, 12))

        widget = self._create_question_widget(row_frame, question, row=0)
        if widget:
            widget.metadata["row_frame"] = row_frame
            widget.metadata["section_frame"] = parent
            self._section_questions.setdefault(parent, []).append(question_id)
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
        value_aliases = question.get("value_aliases") or {}
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
                metadata={
                    "label_to_value": label_to_value,
                    "value_to_label": value_to_label,
                    "value_aliases": value_aliases,
                    "inverse_value_aliases": {v: k for k, v in value_aliases.items()},
                },
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
                metadata={
                    "value_aliases": value_aliases,
                    "inverse_value_aliases": {v: k for k, v in value_aliases.items()},
                },
            )


        if question_type == "boiler_groups":
            container = ttk.Frame(parent)
            container.grid(row=row, column=1, sticky="ew", pady=6)
            container.columnconfigure(0, weight=1)

            rows_container = ttk.Frame(container)
            rows_container.grid(row=0, column=0, sticky="ew")
            rows_container.columnconfigure(0, weight=1)

            row_defs: list[dict[str, Any]] = []

            controls = ttk.Frame(container)
            controls.grid(row=1, column=0, sticky="w", pady=(6, 0))

            group_type_options = self._option_sets.get("heating.boiler_type", {})
            condition_options = self._option_sets.get("boiler.condition", {})

            def _add_row(values: Dict[str, Any] | None = None) -> None:
                values = values if isinstance(values, dict) else {}
                row_idx = len(row_defs)
                row_frame = ttk.LabelFrame(rows_container, text=f"Boiler Group {row_idx + 1}", padding=8)
                row_frame.grid(row=row_idx, column=0, sticky="ew", pady=(0, 6))
                for col in range(0, 8, 2):
                    row_frame.columnconfigure(col + 1, weight=1)

                quantity_var = tk.StringVar(value="" if values.get("quantity") is None else str(values.get("quantity")))
                capacity_var = tk.StringVar(value="" if values.get("capacity_mbh") is None else str(values.get("capacity_mbh")))
                install_year_var = tk.StringVar(value="" if values.get("install_year") is None else str(values.get("install_year")))

                boiler_type_values = list(group_type_options.keys())
                boiler_type_labels = [group_type_options[v] for v in boiler_type_values]
                boiler_type_label_to_value = {group_type_options[value]: value for value in boiler_type_values}
                boiler_type_value_to_label = {value: group_type_options[value] for value in boiler_type_values}
                boiler_type_var = tk.StringVar(value=boiler_type_value_to_label.get(values.get("boiler_type"), ""))

                condition_values = list(condition_options.keys())
                condition_labels = [condition_options[v] for v in condition_values]
                condition_label_to_value = {condition_options[value]: value for value in condition_values}
                condition_value_to_label = {value: condition_options[value] for value in condition_values}
                condition_var = tk.StringVar(value=condition_value_to_label.get(values.get("condition"), ""))

                ttk.Label(row_frame, text="Quantity").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
                ttk.Entry(row_frame, textvariable=quantity_var, width=10).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=2)
                ttk.Label(row_frame, text="Type").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=2)
                ttk.Combobox(row_frame, textvariable=boiler_type_var, values=boiler_type_labels, state="readonly").grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=2)

                ttk.Label(row_frame, text="Capacity (MBH each)").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
                ttk.Entry(row_frame, textvariable=capacity_var, width=14).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=2)
                ttk.Label(row_frame, text="Install year").grid(row=1, column=2, sticky="w", padx=(0, 6), pady=2)
                ttk.Entry(row_frame, textvariable=install_year_var, width=10).grid(row=1, column=3, sticky="ew", padx=(0, 12), pady=2)

                ttk.Label(row_frame, text="Condition").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=2)
                ttk.Combobox(row_frame, textvariable=condition_var, values=condition_labels, state="readonly").grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=2)

                row_defs.append(
                    {
                        "frame": row_frame,
                        "quantity": quantity_var,
                        "boiler_type": boiler_type_var,
                        "capacity_mbh": capacity_var,
                        "install_year": install_year_var,
                        "condition": condition_var,
                        "boiler_type_label_to_value": boiler_type_label_to_value,
                        "condition_label_to_value": condition_label_to_value,
                    }
                )

            def _remove_last_row() -> None:
                if not row_defs:
                    return
                row_def = row_defs.pop()
                frame = row_def.get("frame")
                if frame:
                    frame.destroy()

            ttk.Button(controls, text="Add boiler group", command=lambda: _add_row()).pack(side="left")
            ttk.Button(controls, text="Remove last", command=_remove_last_row).pack(side="left", padx=(6, 0))

            return QuestionWidget(
                question_id,
                question_type,
                row_defs,
                metadata={
                    "add_row": _add_row,
                },
            )

        return None

    def reload_system_catalog(self, catalog_filename: str) -> None:
        panel = self._catalog_panel_by_filename.get(catalog_filename)
        if panel:
            panel.reload_catalog()

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
        for panel in self._system_library_panels.values():
            panel.load_project(project_data)
        self._apply_visibility()

    def update_project(self, project_data: Dict[str, Any]) -> None:
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        answers = dict(answers)
        for question_id, widget in self._question_widgets.items():
            answers[question_id] = self._extract_answer(widget)

        boiler_groups = answers.get("boilers")
        if isinstance(boiler_groups, list) and boiler_groups:
            quantities: list[int] = []
            for group in boiler_groups:
                if not isinstance(group, dict):
                    continue
                try:
                    quantities.append(int(float(str(group.get("quantity", "")).strip())))
                except (TypeError, ValueError):
                    continue
            if quantities:
                answers["number_of_boilers"] = sum(quantities)
            first_group = next((group for group in boiler_groups if isinstance(group, dict)), None)
            if first_group:
                if first_group.get("capacity_mbh"):
                    answers["boiler_capacity_mbh"] = first_group.get("capacity_mbh")
                if first_group.get("boiler_type"):
                    answers["boiler_type"] = first_group.get("boiler_type")
                if first_group.get("install_year"):
                    answers["boiler_install_year"] = first_group.get("install_year")
                if first_group.get("condition"):
                    answers["boiler_condition"] = first_group.get("condition")

        template_fields: Dict[str, Any] = {}
        for placeholder, widget in self._template_widgets.items():
            template_fields[placeholder] = self._extract_answer(widget)

        apply_answers_to_project(project_data, answers, self._schema, template_fields)
        if self._misc_panel:
            self._misc_panel.update_project(project_data)
        for panel in self._system_library_panels.values():
            panel.update_project(project_data)

    def _extract_answer(self, widget: QuestionWidget) -> Any:
        if widget.question_type in {"text", "number", "date"}:
            return widget.widget.get()
        if widget.question_type == "notes":
            return widget.widget.get("1.0", "end-1c")
        if widget.question_type == "single_select":
            label = widget.widget.get()
            mapping = widget.metadata.get("label_to_value", {})
            value = mapping.get(label)
            inverse_aliases = widget.metadata.get("inverse_value_aliases", {})
            if value in inverse_aliases:
                return inverse_aliases[value]
            return value
        if widget.question_type == "multi_select":
            selections = []
            inverse_aliases = widget.metadata.get("inverse_value_aliases", {})
            for value, var in widget.widget:
                if var.get():
                    selections.append(inverse_aliases.get(value, value))
            return selections
        if widget.question_type == "boiler_groups":
            groups = []
            for row in widget.widget:
                quantity = row["quantity"].get().strip()
                boiler_type_label = row["boiler_type"].get().strip()
                capacity_mbh = row["capacity_mbh"].get().strip()
                install_year = row["install_year"].get().strip()
                condition_label = row["condition"].get().strip()
                boiler_type = row["boiler_type_label_to_value"].get(boiler_type_label, "")
                condition = row["condition_label_to_value"].get(condition_label, "")
                group = {
                    "quantity": quantity,
                    "boiler_type": boiler_type,
                    "capacity_mbh": capacity_mbh,
                    "install_year": install_year,
                    "condition": condition,
                }
                if any(str(value).strip() for value in group.values()):
                    groups.append(group)
            return groups
        return None

    def _set_widget_value(self, widget: QuestionWidget, value: Any) -> None:
        if widget.question_type in {"text", "number", "date"}:
            widget.widget.set("" if value is None else str(value))
        elif widget.question_type == "notes":
            widget.widget.delete("1.0", tk.END)
            if value:
                widget.widget.insert("1.0", str(value))
        elif widget.question_type == "single_select":
            aliases = widget.metadata.get("value_aliases", {})
            value_to_label = widget.metadata.get("value_to_label", {})
            if isinstance(value, (list, tuple)):
                if not value:
                    value = None
                elif len(value) == 1:
                    value = value[0]
                else:
                    value = "mixed_unknown" if "mixed_unknown" in value else value[0]
            if value in aliases:
                value = aliases[value]
            label = value_to_label.get(value, "" if value is None else str(value))
            widget.widget.set(label)
        elif widget.question_type == "multi_select":
            aliases = widget.metadata.get("value_aliases", {})
            values = set(aliases.get(item, item) for item in (value or []))
            for option_value, var in widget.widget:
                var.set(option_value in values)
        elif widget.question_type == "boiler_groups":
            groups = value if isinstance(value, list) else []
            self._set_boiler_group_rows(widget, groups)

    def _set_boiler_group_rows(self, widget: QuestionWidget, groups: list[dict[str, Any]]) -> None:
        if widget.question_type != "boiler_groups":
            return
        while widget.widget:
            row_def = widget.widget.pop()
            frame = row_def.get("frame")
            if frame:
                frame.destroy()
        add_row = widget.metadata.get("add_row")
        if callable(add_row):
            for group in groups:
                add_row(group)

    def _build_form_section(self, parent: ttk.Frame, title: str) -> ttk.LabelFrame:
        section_frame = ttk.LabelFrame(parent, text=title, padding=10)
        section_frame.pack(fill="x", padx=10, pady=6)
        self._section_order.setdefault(parent, []).append(section_frame)
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

    def _setup_visibility_handlers(self) -> None:
        dependency_map: Dict[str, list[str]] = {}
        for question_id, question in self._question_definitions.items():
            show_if = question.get("show_if")
            if not show_if:
                continue
            field = show_if.get("field")
            if not field:
                continue
            dependency_map.setdefault(field, []).append(question_id)

        for controller_id in dependency_map:
            widget = self._question_widgets.get(controller_id)
            if not widget:
                continue
            if widget.question_type in {"text", "number", "date", "single_select"}:
                widget.widget.trace_add("write", lambda *_args: self._apply_visibility())
            elif widget.question_type == "multi_select":
                for _value, var in widget.widget:
                    var.trace_add("write", lambda *_args: self._apply_visibility())

    def _apply_visibility(self) -> None:
        for question_id, question in self._question_definitions.items():
            show_if = question.get("show_if")
            widget = self._question_widgets.get(question_id)
            visible = self._evaluate_show_if(show_if) if show_if else True
            self._question_visibility[question_id] = visible
            if widget:
                self._set_question_visibility(widget, visible)
        self._refresh_section_visibility()

    def _set_question_visibility(self, widget: QuestionWidget, visible: bool) -> None:
        row_frame = widget.metadata.get("row_frame")
        if not row_frame:
            return
        if visible:
            row_frame.grid()
        else:
            row_frame.grid_remove()

    def _refresh_section_visibility(self) -> None:
        for container, frames in self._section_order.items():
            for frame in frames:
                frame.pack_forget()
            for frame in frames:
                question_ids = self._section_questions.get(frame, [])
                if not question_ids:
                    frame.pack(fill="x", padx=10, pady=6)
                    continue
                if any(self._question_visibility.get(question_id, True) for question_id in question_ids):
                    frame.pack(fill="x", padx=10, pady=6)

    def _evaluate_show_if(self, show_if: Optional[Dict[str, Any]]) -> bool:
        if not show_if:
            return True
        field = show_if.get("field")
        op = show_if.get("op")
        expected = show_if.get("value")
        if not field or not op:
            return True
        widget = self._question_widgets.get(field)
        if not widget:
            return True
        current = self._extract_answer(widget)

        if op == "eq":
            return current == expected
        if op == "ne":
            return current != expected
        if op == "in":
            if isinstance(current, (list, tuple)):
                return any(item in expected for item in current or [])
            return current in (expected or [])
        if op == "not_in":
            if isinstance(current, (list, tuple)):
                return all(item not in expected for item in current or [])
            return current not in (expected or [])
        if op == "contains":
            if isinstance(current, (list, tuple)):
                return expected in current
            return False
        if op == "not_contains":
            if isinstance(current, (list, tuple)):
                return expected not in current
            return True
        return True


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


def _is_descendant(widget: tk.Misc, ancestor: tk.Misc) -> bool:
    current = widget
    while current is not None:
        if current is ancestor:
            return True
        current = current.master
    return False
