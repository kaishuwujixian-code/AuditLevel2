from __future__ import annotations

from typing import Dict, List

import tkinter as tk
from tkinter import ttk

from core.template_store import TemplateData


class ChecklistPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, template: TemplateData) -> None:
        super().__init__(master)
        self._template = template
        self._vars: Dict[str, Dict[str, Dict[str, tk.BooleanVar]]] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._scroll = _ScrollableFrame(self)
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._render_checklists()

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
                if not isinstance(items, list):
                    continue
                for item in items:
                    var = tk.BooleanVar(value=False)
                    label = ttk.Checkbutton(category_frame, text=str(item), variable=var)
                    label.pack(anchor="w")
                    self._vars[group_name][category_name][str(item)] = var

    def load_project(self, project_data: Dict[str, Any]) -> None:
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
