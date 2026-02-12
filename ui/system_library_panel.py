from __future__ import annotations

from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from core.library_catalog import (
    load_library_catalog,
    save_library_catalog_data,
    validate_library_catalog_data,
)
from ui.ui_state import load_ui_state, save_ui_state


class SystemLibraryPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        catalog_filename: str,
        panel_title: str,
        state_key: str,
    ) -> None:
        super().__init__(master)
        self._catalog_filename = catalog_filename
        self._panel_title = panel_title
        self._state_key = state_key
        self._categories: List[Dict[str, Any]] = []
        self._items: List[Dict[str, Any]] = []
        self._selected_index: Optional[int] = None
        self._selected_category_code: Optional[str] = None
        self._is_new_item = False
        self._item_id = ""
        self._search_var = tk.StringVar(value="")
        self._build_ui()
        self._load_catalog()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._paned = ttk.PanedWindow(self, orient="horizontal")
        self._paned.grid(row=0, column=0, sticky="nsew")

        list_frame = ttk.Frame(self)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        search_row = ttk.Frame(list_frame)
        search_row.grid(row=0, column=0, sticky="ew", padx=(6, 8), pady=(6, 2))
        search_row.columnconfigure(1, weight=1)
        ttk.Label(search_row, text="Search").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._search_entry = ttk.Entry(search_row, textvariable=self._search_var)
        self._search_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(search_row, text="Clear", command=lambda: self._search_var.set("")).grid(
            row=0, column=2, padx=(6, 0)
        )
        ttk.Button(search_row, text="Sort A-Z", command=self._sort_alphabetically).grid(
            row=0, column=3, padx=(6, 0)
        )
        self._search_var.trace_add("write", lambda *_args: self._refresh_tree())

        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=(6, 8), pady=(0, 6))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        editor = ttk.Frame(self)
        editor.columnconfigure(1, weight=1)
        editor.rowconfigure(2, weight=1)

        ttk.Label(editor, text="Label").grid(row=0, column=0, sticky="w", pady=2)
        self._title_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self._title_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(editor, text="Category").grid(row=1, column=0, sticky="w", pady=2)
        self._category_var = tk.StringVar()
        self._category_combo = ttk.Combobox(
            editor, textvariable=self._category_var, state="readonly"
        )
        self._category_combo.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Notes").grid(row=2, column=0, sticky="nw", pady=4)
        text_frame = ttk.Frame(editor)
        text_frame.grid(row=2, column=1, sticky="nsew", pady=2)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self._text = tk.Text(text_frame, height=10, wrap="word")
        self._text.grid(row=0, column=0, sticky="nsew")
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=text_scroll.set)
        text_scroll.grid(row=0, column=1, sticky="ns")

        button_row = ttk.Frame(editor)
        button_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(button_row, text="Apply Changes", command=self._apply_item).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Up", command=lambda: self._move_item(-1)).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Down", command=lambda: self._move_item(1)).pack(
            side="left"
        )

        action_row = ttk.Frame(editor)
        action_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(action_row, text="New Category", command=self._new_category).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="New Item", command=self._new_item).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Duplicate", command=self._duplicate_item).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Delete", command=self._delete_selected).pack(side="left")

        footer = ttk.Frame(editor)
        footer.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Reload", command=self._load_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Validate", command=self._validate_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Save", command=self._save_catalog).pack(side="left")

        self._paned.add(list_frame, weight=2)
        self._paned.add(editor, weight=5)

        self.after(20, self._restore_paned_position)
        self._paned.bind("<ButtonRelease-1>", lambda _e: self._save_paned_position(), add=True)

    def _restore_paned_position(self) -> None:
        state = load_ui_state(self._state_key)
        pos = state.get("sash")
        if isinstance(pos, int) and pos > 120:
            try:
                self._paned.sashpos(0, pos)
            except Exception:
                pass

    def _save_paned_position(self) -> None:
        try:
            pos = int(self._paned.sashpos(0))
        except Exception:
            return
        save_ui_state(self._state_key, {"sash": pos})

    def _sort_alphabetically(self) -> None:
        self._maybe_apply_item()
        selected_item_id = self._item_id if self._item_id else ""
        self._categories.sort(
            key=lambda item: (
                str(item.get("title", "")).strip().lower(),
                str(item.get("code", "")).strip().lower(),
            )
        )
        self._items.sort(
            key=lambda item: (
                str(item.get("category", "")).strip().lower(),
                str(item.get("title", "")).strip().lower(),
            )
        )
        self._refresh_tree()
        self._refresh_category_combo()
        if selected_item_id:
            self._select_item_by_id(selected_item_id)

    def _load_catalog(self) -> None:
        try:
            catalog = load_library_catalog(self._catalog_filename)
            self._categories = list(catalog.categories)
            self._items = [catalog.items[item_id] for item_id in catalog.order]
        except Exception as exc:
            messagebox.showerror(self._panel_title, f"Load failed: {exc}")
            self._categories = []
            self._items = []
        self._reset_selection()
        self._refresh_ui()

    def _validate_catalog(self) -> None:
        data = {"categories": self._categories, "items": self._items}
        try:
            validate_library_catalog_data(data)
        except Exception as exc:
            messagebox.showerror(self._panel_title, str(exc))
            return
        messagebox.showinfo(self._panel_title, "Catalog validation passed.")

    def _save_catalog(self) -> None:
        self._maybe_apply_item()
        data = {"categories": self._categories, "items": self._items}
        try:
            save_library_catalog_data(self._catalog_filename, data)
        except Exception as exc:
            messagebox.showerror(self._panel_title, f"Save failed: {exc}")
            return
        messagebox.showinfo(self._panel_title, "Catalog saved.")
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        self._refresh_tree()
        self._refresh_category_combo()
        self._clear_form()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._tree_items: Dict[str, int] = {}
        self._tree_categories: Dict[str, str] = {}
        self._tree_by_id: Dict[str, str] = {}
        term = self._search_var.get().strip().lower()

        category_nodes: Dict[str, str] = {}
        categories_by_code = {
            str(entry.get("code", "")).strip(): str(entry.get("title", "")).strip()
            for entry in self._categories
            if isinstance(entry, dict)
        }
        for code, title in categories_by_code.items():
            if not code:
                continue
            node = self._tree.insert("", "end", text=title or code)
            category_nodes[code] = node
            self._tree_categories[node] = code

        visible_counts: Dict[str, int] = {key: 0 for key in category_nodes}
        for idx, item in enumerate(self._items):
            item_id = str(item.get("id", "")).strip()
            title = str(item.get("title", "")).strip()
            category = str(item.get("category", "")).strip()
            if term and term not in title.lower() and term not in category.lower():
                continue
            parent = category_nodes.get(category, "")
            node_id = self._tree.insert(parent, "end", text=title or "(Untitled)")
            self._tree_items[node_id] = idx
            if item_id:
                self._tree_by_id[item_id] = node_id
            if category in visible_counts:
                visible_counts[category] += 1

        for code, node_id in list(category_nodes.items()):
            if visible_counts.get(code, 0) == 0 and term:
                self._tree.delete(node_id)
                continue
            self._tree.item(node_id, open=True)

    def _refresh_category_combo(self) -> None:
        values = [str(entry.get("code", "")).strip() for entry in self._categories if str(entry.get("code", "")).strip()]
        self._category_combo.configure(values=values)

    def _reset_selection(self) -> None:
        self._selected_index = None
        self._selected_category_code = None
        self._is_new_item = False

    def _on_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        node_id = selection[0]
        index = self._tree_items.get(node_id)
        if index is not None:
            self._selected_index = index
            self._selected_category_code = None
            self._is_new_item = False
            self._load_form(self._items[index])
            return
        category_code = self._tree_categories.get(node_id)
        if category_code is not None:
            self._selected_index = None
            self._selected_category_code = category_code
            self._is_new_item = False
            self._clear_form()
            self._category_var.set(category_code)

    def _load_form(self, item: Dict[str, Any]) -> None:
        self._title_var.set(str(item.get("title", "")).strip())
        self._category_var.set(str(item.get("category", "")).strip())
        _set_text(self._text, item.get("text"))
        self._item_id = str(item.get("id", "")).strip()

    def _clear_form(self) -> None:
        self._title_var.set("")
        self._category_var.set("")
        _set_text(self._text, "")
        self._item_id = ""

    def _new_item(self) -> None:
        self._tree.selection_remove(self._tree.selection())
        self._selected_index = None
        self._is_new_item = True
        self._clear_form()
        if self._selected_category_code:
            self._category_var.set(self._selected_category_code)

    def _new_category(self) -> None:
        name = simpledialog.askstring(self._panel_title, "New category title:", parent=self)
        if not name:
            return
        title = name.strip()
        if not title:
            return
        code = _unique_category_code(_slugify(title), self._categories)
        self._categories.append({"code": code, "title": title})
        self._refresh_category_combo()
        self._refresh_tree()

    def _duplicate_item(self) -> None:
        if self._selected_index is None:
            return
        base = dict(self._items[self._selected_index])
        base["id"] = ""
        base["title"] = f"Copy of {base.get('title', '')}".strip()
        self._items.append(base)
        self._refresh_tree()

    def _delete_selected(self) -> None:
        if self._selected_index is not None:
            self._delete_item()
            return
        if self._selected_category_code:
            self._delete_category(self._selected_category_code)

    def _delete_item(self) -> None:
        if self._selected_index is None:
            return
        item = self._items[self._selected_index]
        if not messagebox.askyesno(
            self._panel_title,
            f"Delete item '{item.get('title') or item.get('id')}'?",
        ):
            return
        self._items.pop(self._selected_index)
        self._reset_selection()
        self._refresh_tree()
        self._clear_form()

    def _delete_category(self, category_code: str) -> None:
        category = next((entry for entry in self._categories if str(entry.get("code", "")).strip() == category_code), None)
        if not category:
            return
        title = str(category.get("title", "")).strip() or category_code
        if not messagebox.askyesno(
            self._panel_title,
            f"Delete category '{title}' and all items in this category?",
        ):
            return
        self._categories = [
            entry for entry in self._categories if str(entry.get("code", "")).strip() != category_code
        ]
        self._items = [
            item for item in self._items if str(item.get("category", "")).strip() != category_code
        ]
        self._reset_selection()
        self._refresh_ui()

    def _move_item(self, offset: int) -> None:
        if self._selected_index is None:
            return
        new_index = self._selected_index + offset
        if new_index < 0 or new_index >= len(self._items):
            return
        self._items[self._selected_index], self._items[new_index] = (
            self._items[new_index],
            self._items[self._selected_index],
        )
        self._selected_index = new_index
        self._refresh_tree()
        item_id = str(self._items[new_index].get("id", "")).strip()
        self._select_item_by_id(item_id)

    def _apply_item(self) -> None:
        item_id = self._item_id
        if not item_id:
            item_id = _unique_item_id(
                _slugify(self._title_var.get().strip()), self._items
            )
        if not item_id:
            messagebox.showerror(self._panel_title, "Label is required.")
            return
        payload = {
            "id": item_id,
            "title": self._title_var.get().strip(),
            "category": self._category_var.get().strip(),
            "text": _get_text(self._text),
        }
        if self._is_new_item or self._selected_index is None:
            self._items.append(payload)
            self._selected_index = len(self._items) - 1
            self._is_new_item = False
        else:
            current = self._items[self._selected_index]
            current.update(payload)
        self._refresh_tree()
        self._select_item_by_id(item_id)

    def _maybe_apply_item(self) -> None:
        if not _has_form_data(
            self._title_var.get().strip(), _get_text(self._text)
        ):
            return
        if self._is_new_item or self._selected_index is not None:
            self._apply_item()

    def _select_item_by_id(self, item_id: str) -> None:
        if not item_id:
            return
        node_id = self._tree_by_id.get(item_id)
        if node_id:
            self._tree.selection_set(node_id)


def _slugify(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.lower())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def _unique_item_id(candidate: str, items: List[Dict[str, Any]]) -> str:
    if not candidate:
        return ""
    existing = {str(item.get("id", "")).strip() for item in items}
    if candidate not in existing:
        return candidate
    index = 2
    while True:
        alt = f"{candidate}_{index}"
        if alt not in existing:
            return alt
        index += 1


def _unique_category_code(candidate: str, categories: List[Dict[str, Any]]) -> str:
    if not candidate:
        candidate = "new_category"
    existing = {str(item.get("code", "")).strip() for item in categories}
    if candidate not in existing:
        return candidate
    index = 2
    while True:
        alt = f"{candidate}_{index}"
        if alt not in existing:
            return alt
        index += 1


def _has_form_data(title: str, text: str) -> bool:
    return any(value.strip() for value in (title, text))


def _set_text(widget: tk.Text, value: Any) -> None:
    widget.delete("1.0", tk.END)
    if value is not None and str(value).strip():
        widget.insert("1.0", str(value))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c").strip()
