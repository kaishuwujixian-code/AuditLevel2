from __future__ import annotations

from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.misc_catalog import MiscCatalog, load_misc_catalog
from ui.misc_editor import MiscEditor


class MiscPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._catalog: Optional[MiscCatalog] = None
        self._catalog_tree: Optional[ttk.Treeview] = None
        self._editor: Optional[MiscEditor] = None
        self._catalog_items: Dict[str, str] = {}
        self._build_ui()
        self._load_catalog()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        catalog_frame = ttk.Frame(paned, padding=(6, 6))
        catalog_frame.columnconfigure(0, weight=1)
        catalog_frame.rowconfigure(1, weight=1)
        ttk.Label(catalog_frame, text="Miscellaneous Library").grid(row=0, column=0, sticky="w")
        self._catalog_tree = ttk.Treeview(catalog_frame, show="tree")
        self._catalog_tree.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        catalog_scroll = ttk.Scrollbar(
            catalog_frame, orient="vertical", command=self._catalog_tree.yview
        )
        self._catalog_tree.configure(yscrollcommand=catalog_scroll.set)
        catalog_scroll.grid(row=1, column=1, sticky="ns", pady=(6, 0))
        self._catalog_tree.bind("<<TreeviewSelect>>", self._on_catalog_select)
        paned.add(catalog_frame, weight=1)

        editor_frame = ttk.Frame(paned, padding=(6, 6))
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)
        self._editor = MiscEditor(editor_frame)
        self._editor.grid(row=0, column=0, sticky="nsew")
        paned.add(editor_frame, weight=3)

    def load_project(self, project_data: Dict[str, Any]) -> None:
        if not self._editor:
            return
        items = _extract_items(project_data)
        self._editor.set_items(items)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        if not self._editor:
            return
        items = self._editor.get_items()
        project_data["misc_items"] = items
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        answers["misc_items"] = items
        project_data["answers"] = answers

    def _load_catalog(self) -> None:
        if not self._catalog_tree or not self._editor:
            return
        try:
            self._catalog = load_misc_catalog()
        except Exception:
            self._catalog = None
        if self._catalog:
            self._editor.set_categories(self._catalog.categories)
        self._populate_catalog_tree()

    def _populate_catalog_tree(self) -> None:
        if not self._catalog_tree:
            return
        self._catalog_tree.delete(*self._catalog_tree.get_children())
        self._catalog_items = {}
        if not self._catalog:
            self._catalog_tree.insert("", "end", text="Misc catalog not available.")
            return

        category_nodes: Dict[str, str] = {}
        for category in self._catalog.categories:
            code = str(category.get("code", "")).strip()
            label = str(category.get("title", "")).strip() or code or "Other"
            category_nodes[code] = self._catalog_tree.insert("", "end", text=label)

        for item_id in self._catalog.order:
            item = self._catalog.items.get(item_id, {})
            category = str(item.get("category") or "").strip()
            parent = category_nodes.get(category, "")
            title = item.get("title") or item_id
            row_id = self._catalog_tree.insert(parent, "end", text=title)
            self._catalog_items[row_id] = item_id

        for node_id in category_nodes.values():
            self._catalog_tree.item(node_id, open=True)

    def _on_catalog_select(self, _event: tk.Event) -> None:
        if not self._catalog_tree or not self._catalog or not self._editor:
            return
        selection = self._catalog_tree.selection()
        if not selection:
            return
        item_id = self._catalog_items.get(selection[0])
        if not item_id:
            return
        item = self._catalog.items.get(item_id, {})
        self._editor.apply_catalog_item(item)


def _extract_items(project_data: Dict[str, Any]) -> list[Dict[str, Any]]:
    items = project_data.get("misc_items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    answers = project_data.get("answers", {})
    if isinstance(answers, dict):
        items = answers.get("misc_items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []
