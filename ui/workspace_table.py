import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional

from core.template_store import TemplateData


MeasureSelectHandler = Callable[[str], None]


class WorkspaceTable(ttk.Frame):
    def __init__(self, master: tk.Misc, on_measure_select: MeasureSelectHandler) -> None:
        super().__init__(master)
        self._on_measure_select = on_measure_select
        self._template: Optional[TemplateData] = None
        self._project_data: Optional[Dict] = None
        self._measure_by_row: Dict[str, str] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        columns = (
            "include",
            "category",
            "item",
            "notes",
            "savings",
            "cost",
            "payback",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("include", text="Include?")
        self.tree.heading("category", text="Category")
        self.tree.heading("item", text="Item / Measure")
        self.tree.heading("notes", text="Notes")
        self.tree.heading("savings", text="Savings")
        self.tree.heading("cost", text="Cost")
        self.tree.heading("payback", text="Payback")

        self.tree.column("include", width=70, anchor="center")
        self.tree.column("category", width=140, anchor="w")
        self.tree.column("item", width=240, anchor="w")
        self.tree.column("notes", width=180, anchor="w")
        self.tree.column("savings", width=90, anchor="center")
        self.tree.column("cost", width=90, anchor="center")
        self.tree.column("payback", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Button-1>", self._handle_click, add=True)
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)

    def load_project(self, template: TemplateData, project_data: Dict) -> None:
        self._template = template
        self._project_data = project_data
        self._measure_by_row.clear()

        for item in self.tree.get_children():
            self.tree.delete(item)

        selected = project_data.get("selected_measures", [])
        if not isinstance(selected, list):
            selected = []
        selected = self._normalize_selected(selected)
        project_data["selected_measures"] = selected

        category_titles = template.category_titles
        category_order = [item.get("code", "") for item in template.ui_categories]
        measure_order = template.measure_order or sorted(template.measures.keys())
        order_index = {key: idx for idx, key in enumerate(measure_order)}

        def sort_key(measure_key: str) -> tuple:
            measure = template.measures.get(measure_key, {})
            category_code = measure.get("category") or template.category_overrides.get(measure_key, "")
            index = order_index.get(measure_key, len(order_index))
            try:
                category_index = category_order.index(category_code)
            except ValueError:
                category_index = len(category_order)
            return (category_index, index, category_code, measure_key.lower())

        for measure_key in sorted(template.measures.keys(), key=sort_key):
            measure = template.measures.get(measure_key, {})
            category_code = measure.get("category") or template.category_overrides.get(measure_key, "")
            category_label = category_titles.get(category_code, category_code)
            include = "✓" if measure_key in selected else ""
            notes = ""
            display_name = measure.get("name") or measure.get("title") or measure_key
            row_id = self.tree.insert(
                "",
                "end",
                values=(
                    include,
                    category_label,
                    display_name,
                    notes,
                    "—",
                    "—",
                    "—",
                ),
            )
            self._measure_by_row[row_id] = measure_key

    def _handle_click(self, event: tk.Event) -> None:
        if not self._project_data or not self._template:
            return
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        if column != "#1":
            return
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        measure_key = self._measure_by_row.get(row_id)
        if not measure_key:
            return
        self.toggle_measure(measure_key)

    def _handle_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        measure_key = self._measure_by_row.get(selection[0])
        if measure_key:
            self._on_measure_select(measure_key)

    def toggle_measure(self, measure_key: str) -> None:
        if not self._project_data:
            return
        selected = self._project_data.get("selected_measures", [])
        if not isinstance(selected, list):
            selected = []
        if measure_key in selected:
            selected = [item for item in selected if item != measure_key]
        else:
            selected = selected + [measure_key]
        self._project_data["selected_measures"] = selected
        for row_id, key in self._measure_by_row.items():
            if key == measure_key:
                current = self.tree.set(row_id, "include")
                self.tree.set(row_id, "include", "" if current else "✓")
                break

    def _normalize_selected(self, selected: List[str]) -> List[str]:
        if not self._template:
            return selected
        mapped = []
        for item in selected:
            if item in self._template.measures:
                mapped.append(item)
                continue
            mapped.append(self._template.legacy_key_map.get(item, item))
        return mapped
