from __future__ import annotations

from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import ttk

from core.paths import DEFAULT_TEMPLATE_JSON
from core.template_store import TemplateData
from core.template_store import load_template
from ui.checklist_library_panel import ChecklistLibraryPanel
from ui.measure_library_panel import MeasureLibraryPanel
from ui.misc_library_panel import MiscLibraryPanel


class ChecklistPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        template: TemplateData,
        *,
        on_measure_catalog_saved=None,
    ) -> None:
        super().__init__(master)
        self._template = template
        self._vars: Dict[str, Dict[str, Dict[str, tk.BooleanVar]]] = {}
        self._project_data: Optional[Dict[str, Any]] = None
        self._on_measure_catalog_saved = on_measure_catalog_saved
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew")

        self._selection_tab = ttk.Frame(notebook)
        self._selection_tab.columnconfigure(0, weight=1)
        self._selection_tab.rowconfigure(0, weight=1)
        self._scroll = _ScrollableFrame(self._selection_tab)
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._render_checklists()
        notebook.add(self._selection_tab, text="Selections")

        self._library_tab = ttk.Frame(notebook)
        self._library_tab.columnconfigure(0, weight=1)
        self._library_tab.rowconfigure(0, weight=1)
        library_notebook = ttk.Notebook(self._library_tab)
        library_notebook.grid(row=0, column=0, sticky="nsew")

        self._checklist_library_panel = ChecklistLibraryPanel(
            library_notebook, on_saved=self._on_library_saved
        )
        library_notebook.add(self._checklist_library_panel, text="Checklist Library")

        self._measure_library_panel = MeasureLibraryPanel(
            library_notebook, on_catalog_saved=self._on_measure_catalog_saved
        )
        library_notebook.add(self._measure_library_panel, text="Measure Library")

        self._misc_library_panel = MiscLibraryPanel(library_notebook)
        library_notebook.add(self._misc_library_panel, text="Misc Library")

        notebook.add(self._library_tab, text="Library")

    def _render_checklists(self) -> None:
        container = self._scroll.content
        for child in container.winfo_children():
            child.destroy()
        self._vars.clear()

        if not self._template.checklists:
            ttk.Label(container, text="No checklist categories found in the template.").pack(anchor="w")
            return

        for group_name, categories in self._template.checklists.items():
            group_frame = ttk.LabelFrame(container, text=group_name, padding=10)
            group_frame.pack(fill="x", padx=10, pady=6)
            self._vars[group_name] = {}
            if not isinstance(categories, dict):
                continue
            for category_name, items in categories.items():
                category_frame = ttk.LabelFrame(group_frame, text=category_name, padding=8)
                category_frame.pack(fill="x", padx=10, pady=6)
                self._vars[group_name][category_name] = {}
                item_list = _extract_items(items)
                if not item_list:
                    continue
                for item in item_list:
                    var = tk.BooleanVar(value=False)
                    label = ttk.Checkbutton(category_frame, text=str(item), variable=var)
                    label.pack(anchor="w")
                    self._vars[group_name][category_name][str(item)] = var

    def load_project(self, project_data: Dict[str, Any]) -> None:
        self._project_data = project_data
        selections = project_data.get("checklist_selections", {})
        if not isinstance(selections, dict):
            selections = {}
        for group_name, categories in self._vars.items():
            selected_categories = selections.get(group_name, {}) if isinstance(selections.get(group_name), dict) else {}
            for category_name, items in categories.items():
                selected_items = selected_categories.get(category_name, [])
                if not isinstance(selected_items, list):
                    selected_items = []
                selected_set = set(selected_items)
                for item_label, var in items.items():
                    var.set(item_label in selected_set)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        selections: Dict[str, Dict[str, List[str]]] = {}
        for group_name, categories in self._vars.items():
            group_payload: Dict[str, List[str]] = {}
            for category_name, items in categories.items():
                selected_items = [label for label, var in items.items() if var.get()]
                if selected_items:
                    group_payload[category_name] = selected_items
            if group_payload:
                selections[group_name] = group_payload
        project_data["checklist_selections"] = selections

    def _on_library_saved(self, checklists: Dict[str, dict]) -> None:
        try:
            self._template = load_template(DEFAULT_TEMPLATE_JSON)
        except Exception:
            self._template = TemplateData({}, [], checklists, [], {}, {})
        self._render_checklists()
        if self._project_data:
            self.load_project(self._project_data)


class _ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.content = ttk.Frame(self._canvas)

        self._canvas_frame = self._canvas.create_window((0, 0), window=self.content, anchor="nw")
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


def _extract_items(value: object) -> list:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        items = value.get("items")
        if isinstance(items, list):
            labels: list[str] = []
            for item in items:
                if isinstance(item, dict):
                    label = item.get("label")
                    if isinstance(label, str) and label.strip():
                        labels.append(label)
                    else:
                        text = item.get("text")
                        if isinstance(text, str) and text.strip():
                            labels.append(text)
                elif item is not None:
                    labels.append(str(item))
            return labels
    return []
