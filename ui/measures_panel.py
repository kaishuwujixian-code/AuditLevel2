from __future__ import annotations

from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.measure_catalog import MeasureCatalog, load_measure_catalog
from core.project_store import normalize_measures_data
from ui.measure_editor import MeasuresEditor


class MeasuresPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._catalog: Optional[MeasureCatalog] = None
        self._catalog_tree: Optional[ttk.Treeview] = None
        self._editor: Optional[MeasuresEditor] = None
        self._catalog_items: Dict[str, str] = {}
        self._selected_tree_ids: set[str] = set()
        self._search_var = tk.StringVar(value="")
        self._build_ui()
        self._load_catalog()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        catalog_frame = ttk.Frame(paned, padding=(6, 6))
        catalog_frame.columnconfigure(0, weight=1)
        catalog_frame.rowconfigure(2, weight=1)
        ttk.Label(catalog_frame, text="Measure Library").grid(row=0, column=0, sticky="w")

        search_row = ttk.Frame(catalog_frame)
        search_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        search_row.columnconfigure(1, weight=1)
        ttk.Label(search_row, text="Search").grid(row=0, column=0, sticky="w", padx=(0, 6))
        search_entry = ttk.Entry(search_row, textvariable=self._search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(search_row, text="Clear", command=lambda: self._search_var.set("")).grid(
            row=0, column=2, padx=(6, 0)
        )
        ttk.Button(search_row, text="Sort A-Z", command=self._sort_catalog_alphabetically).grid(
            row=0, column=3, padx=(6, 0)
        )

        tree_wrap = ttk.Frame(catalog_frame)
        tree_wrap.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        tree_wrap.columnconfigure(0, weight=1)
        tree_wrap.rowconfigure(0, weight=1)

        self._catalog_tree = ttk.Treeview(tree_wrap, show="tree")
        self._catalog_tree.grid(row=0, column=0, sticky="nsew")
        catalog_scroll = ttk.Scrollbar(
            tree_wrap, orient="vertical", command=self._catalog_tree.yview
        )
        catalog_xscroll = ttk.Scrollbar(
            tree_wrap, orient="horizontal", command=self._catalog_tree.xview
        )
        self._catalog_tree.configure(
            yscrollcommand=catalog_scroll.set,
            xscrollcommand=catalog_xscroll.set,
        )
        catalog_scroll.grid(row=0, column=1, sticky="ns")
        catalog_xscroll.grid(row=1, column=0, sticky="ew")
        self._search_var.trace_add("write", lambda *_args: self._populate_catalog_tree())
        self._catalog_tree.bind("<<TreeviewSelect>>", self._on_catalog_select)
        paned.add(catalog_frame, weight=1)

        editor_frame = ttk.Frame(paned, padding=(6, 6))
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)
        self._editor = MeasuresEditor(editor_frame, on_items_changed=self._sync_selected_tree_items)
        self._editor.grid(row=0, column=0, sticky="nsew")
        paned.add(editor_frame, weight=3)

    def load_project(self, project_data: Dict[str, Any]) -> None:
        if not self._editor:
            return
        normalize_measures_data(project_data)
        measures = _extract_measures(project_data)
        self._editor.set_measures(measures)
        self._sync_selected_tree_items()

    def update_project(self, project_data: Dict[str, Any]) -> None:
        if not self._editor:
            return
        measures = self._editor.get_measures()
        project_data["measures"] = measures
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        answers["measures"] = measures
        project_data["answers"] = answers

    def _load_catalog(self) -> None:
        if not self._catalog_tree:
            return
        try:
            self._catalog = load_measure_catalog()
        except Exception:
            self._catalog = None
        if self._editor and self._catalog:
            self._editor.set_categories(self._catalog.categories)
        self._populate_catalog_tree()
        self._sync_selected_tree_items()

    def reload_catalog(self, catalog: Optional[MeasureCatalog] = None) -> None:
        if catalog is not None:
            self._catalog = catalog
            if self._editor:
                self._editor.set_categories(self._catalog.categories)
            self._populate_catalog_tree()
            self._sync_selected_tree_items()
            return
        self._load_catalog()

    def _sort_catalog_alphabetically(self) -> None:
        if not self._catalog:
            return
        self._catalog.categories = sorted(
            self._catalog.categories,
            key=lambda category: str(category.get("tab_title", "") or category.get("code", "")).strip().lower(),
        )
        self._catalog.order = sorted(
            self._catalog.order,
            key=lambda measure_id: str(
                self._catalog.measures.get(measure_id, {}).get("title")
                or self._catalog.measures.get(measure_id, {}).get("name")
                or measure_id
            ).strip().lower(),
        )
        self._populate_catalog_tree()

    def _populate_catalog_tree(self) -> None:
        if not self._catalog_tree:
            return
        self._catalog_tree.delete(*self._catalog_tree.get_children())
        self._catalog_items = {}
        self._selected_tree_ids = set()
        if not self._catalog:
            self._catalog_tree.insert("", "end", text="Measure catalog not available.")
            return

        category_nodes: Dict[str, str] = {}
        term = self._search_var.get().strip().lower()
        for category in self._catalog.categories:
            code = str(category.get("code", "")).strip()
            label = str(category.get("tab_title", "")).strip() or code or "Other"
            category_nodes[code] = self._catalog_tree.insert("", "end", text=label)

        visible_by_category: Dict[str, int] = {key: 0 for key in category_nodes}
        for measure_id in self._catalog.order:
            measure = self._catalog.measures.get(measure_id, {})
            category = str(measure.get("category") or "").strip()
            parent = category_nodes.get(category, "")
            title = str(measure.get("title") or measure.get("name") or measure_id)
            if term and term not in title.lower() and term not in category.lower():
                continue
            item_id = self._catalog_tree.insert(parent, "end", text=title)
            self._catalog_items[item_id] = measure_id
            if category in visible_by_category:
                visible_by_category[category] += 1

        for code, node_id in list(category_nodes.items()):
            if visible_by_category.get(code, 0) == 0:
                self._catalog_tree.delete(node_id)
                continue
            self._catalog_tree.item(node_id, open=True)
        self._sync_selected_tree_items()

    def _on_catalog_select(self, _event: tk.Event) -> None:
        if not self._catalog_tree or not self._catalog or not self._editor:
            return
        selection = self._catalog_tree.selection()
        if not selection:
            return
        measure_id = self._catalog_items.get(selection[0])
        if not measure_id:
            return
        measure = self._catalog.measures.get(measure_id, {})
        self._editor.apply_catalog_measure(measure)

    def _sync_selected_tree_items(self) -> None:
        if not self._catalog_tree or not self._editor:
            return
        selected_catalog_ids = self._editor.selected_catalog_measure_ids()
        for tree_id in self._selected_tree_ids:
            if self._catalog_tree.exists(tree_id):
                self._catalog_tree.item(tree_id, tags=())
        self._selected_tree_ids = set()
        for tree_id, catalog_id in self._catalog_items.items():
            if catalog_id in selected_catalog_ids and self._catalog_tree.exists(tree_id):
                self._catalog_tree.item(tree_id, tags=("chosen",))
                self._selected_tree_ids.add(tree_id)
        self._catalog_tree.tag_configure("chosen", foreground="#1d4ed8")


def _extract_measures(project_data: Dict[str, Any]) -> list[Dict[str, Any]]:
    measures = project_data.get("measures")
    if isinstance(measures, list):
        return [item for item in measures if isinstance(item, dict)]
    answers = project_data.get("answers", {})
    if isinstance(answers, dict):
        measures = answers.get("measures")
        if isinstance(measures, list):
            return [item for item in measures if isinstance(item, dict)]
    return []
