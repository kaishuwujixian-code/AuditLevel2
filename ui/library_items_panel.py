from __future__ import annotations

from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.library_catalog import LibraryCatalog, load_library_catalog
from ui.misc_editor import MiscEditor


class LibraryItemsPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        storage_key: str,
        catalog_filename: str,
        title: str,
        item_label: str,
    ) -> None:
        super().__init__(master)
        self._storage_key = storage_key
        self._catalog_filename = catalog_filename
        self._title = title
        self._catalog: Optional[LibraryCatalog] = None
        self._catalog_tree: Optional[ttk.Treeview] = None
        self._editor: Optional[MiscEditor] = None
        self._catalog_items: Dict[str, str] = {}
        self._search_var = tk.StringVar(value="")
        self._selected_tree_ids: set[str] = set()
        self._build_ui(item_label=item_label)
        self._load_catalog()

    def _build_ui(self, *, item_label: str) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        catalog_frame = ttk.Frame(paned, padding=(6, 6))
        catalog_frame.columnconfigure(0, weight=1)
        catalog_frame.rowconfigure(2, weight=1)
        ttk.Label(catalog_frame, text=self._title).grid(row=0, column=0, sticky="w")

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
        catalog_scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self._catalog_tree.yview)
        catalog_xscroll = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self._catalog_tree.xview)
        self._catalog_tree.configure(yscrollcommand=catalog_scroll.set, xscrollcommand=catalog_xscroll.set)
        catalog_scroll.grid(row=0, column=1, sticky="ns")
        catalog_xscroll.grid(row=1, column=0, sticky="ew")
        self._search_var.trace_add("write", lambda *_args: self._populate_catalog_tree())
        self._catalog_tree.bind("<<TreeviewSelect>>", self._on_catalog_select)
        paned.add(catalog_frame, weight=1)

        editor_frame = ttk.Frame(paned, padding=(6, 6))
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)
        self._editor = MiscEditor(
            editor_frame,
            item_label=item_label,
            on_items_changed=self._sync_selected_tree_items,
        )
        self._editor.grid(row=0, column=0, sticky="nsew")
        paned.add(editor_frame, weight=3)

    def reload_catalog(self) -> None:
        self._load_catalog()

    def load_project(self, project_data: Dict[str, Any]) -> None:
        if not self._editor:
            return
        items = _extract_items(project_data, self._storage_key)
        self._editor.set_items(items)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        if not self._editor:
            return
        items = self._editor.get_items()
        project_data[self._storage_key] = items
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        answers[self._storage_key] = items
        project_data["answers"] = answers

    def clear_items(self) -> None:
        if not self._editor:
            return
        self._editor.set_items([])

    def _load_catalog(self) -> None:
        if not self._catalog_tree or not self._editor:
            return
        try:
            self._catalog = load_library_catalog(self._catalog_filename)
        except Exception:
            self._catalog = None
        if self._catalog:
            self._editor.set_categories(self._catalog.categories)
        self._populate_catalog_tree()
        self._sync_selected_tree_items()

    def _sort_catalog_alphabetically(self) -> None:
        if not self._catalog:
            return
        self._catalog.categories[:] = sorted(
            self._catalog.categories,
            key=lambda category: str(category.get("title", "") or category.get("code", "")).strip().lower(),
        )
        self._catalog.order[:] = sorted(
            self._catalog.order,
            key=lambda item_id: str(self._catalog.items.get(item_id, {}).get("title") or item_id).strip().lower(),
        )
        self._populate_catalog_tree()

    def _populate_catalog_tree(self) -> None:
        if not self._catalog_tree:
            return
        self._catalog_tree.delete(*self._catalog_tree.get_children())
        self._catalog_items = {}
        self._selected_tree_ids = set()
        if not self._catalog:
            self._catalog_tree.insert("", "end", text="Catalog not available.")
            return

        category_nodes: Dict[str, str] = {}
        term = self._search_var.get().strip().lower()
        for category in self._catalog.categories:
            code = str(category.get("code", "")).strip()
            label = str(category.get("title", "")).strip() or code or "Other"
            category_nodes[code] = self._catalog_tree.insert("", "end", text=label)

        visible_by_category: Dict[str, int] = {key: 0 for key in category_nodes}
        for item_id in self._catalog.order:
            item = self._catalog.items.get(item_id, {})
            category = str(item.get("category") or "").strip()
            parent = category_nodes.get(category, "")
            title = str(item.get("title") or item_id)
            if term and term not in title.lower() and term not in category.lower():
                continue
            row_id = self._catalog_tree.insert(parent, "end", text=title)
            self._catalog_items[row_id] = item_id
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
        item_id = self._catalog_items.get(selection[0])
        if not item_id:
            return
        item = self._catalog.items.get(item_id, {})
        self._editor.apply_catalog_item(item)

    def _sync_selected_tree_items(self) -> None:
        if not self._catalog_tree or not self._editor:
            return
        selected_catalog_ids = self._editor.selected_catalog_item_ids()
        for tree_id in self._selected_tree_ids:
            if self._catalog_tree.exists(tree_id):
                self._catalog_tree.item(tree_id, tags=())
        self._selected_tree_ids = set()
        for tree_id, catalog_id in self._catalog_items.items():
            if catalog_id in selected_catalog_ids and self._catalog_tree.exists(tree_id):
                self._catalog_tree.item(tree_id, tags=("chosen",))
                self._selected_tree_ids.add(tree_id)
        self._catalog_tree.tag_configure("chosen", foreground="#1d4ed8")


def _extract_items(project_data: Dict[str, Any], storage_key: str) -> list[Dict[str, Any]]:
    items = project_data.get(storage_key)
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    answers = project_data.get("answers", {})
    if isinstance(answers, dict):
        items = answers.get(storage_key)
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []
