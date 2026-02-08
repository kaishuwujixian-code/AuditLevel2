from __future__ import annotations

from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from core.misc_catalog import DEFAULT_MISC_CATALOG, load_misc_catalog, save_misc_catalog_data, validate_misc_catalog_data


class MiscLibraryPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._catalog_path = DEFAULT_MISC_CATALOG
        self._categories: List[Dict[str, Any]] = []
        self._items: List[Dict[str, Any]] = []
        self._selected_index: Optional[int] = None
        self._is_new_item = False
        self._item_id = ""
        self._build_ui()
        self._load_catalog()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(self)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=6)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(list_frame, show="tree", selectmode="browse")
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        editor = ttk.Frame(self)
        editor.grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=6)
        editor.columnconfigure(1, weight=1)

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
        self._text = tk.Text(editor, height=6, wrap="word")
        self._text.grid(row=2, column=1, sticky="ew", pady=2)

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
        ttk.Button(action_row, text="New Item", command=self._new_item).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Duplicate", command=self._duplicate_item).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Delete", command=self._delete_item).pack(side="left")

        footer = ttk.Frame(editor)
        footer.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Reload", command=self._load_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Validate", command=self._validate_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Save", command=self._save_catalog).pack(side="left")

    def _load_catalog(self) -> None:
        try:
            catalog = load_misc_catalog(self._catalog_path)
            self._categories = list(catalog.categories)
            self._items = [catalog.items[item_id] for item_id in catalog.order]
        except Exception as exc:
            messagebox.showerror("Misc Library", f"Load failed: {exc}")
            self._categories = []
            self._items = []
        self._reset_selection()
        self._refresh_ui()

    def _validate_catalog(self) -> None:
        data = {"categories": self._categories, "items": self._items}
        try:
            validate_misc_catalog_data(data)
        except Exception as exc:
            messagebox.showerror("Misc Library", str(exc))
            return
        messagebox.showinfo("Misc Library", "Catalog validation passed.")

    def _save_catalog(self) -> None:
        self._maybe_apply_item()
        data = {"categories": self._categories, "items": self._items}
        try:
            save_misc_catalog_data(data, self._catalog_path)
        except Exception as exc:
            messagebox.showerror("Misc Library", f"Save failed: {exc}")
            return
        messagebox.showinfo("Misc Library", "Catalog saved successfully.")

    def _refresh_ui(self) -> None:
        self._refresh_tree()
        self._refresh_category_combo()
        self._clear_form()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._tree_items: Dict[str, int] = {}
        self._tree_by_id: Dict[str, str] = {}
        categories = _category_lookup(self._categories)
        category_nodes: Dict[str, str] = {}
        for code, title in categories:
            category_nodes[code] = self._tree.insert("", "end", text=title)
        if "" not in category_nodes:
            category_nodes[""] = self._tree.insert("", "end", text="Uncategorized")
        for idx, item in enumerate(self._items):
            title = str(item.get("title", "")).strip()
            category = str(item.get("category", "")).strip()
            item_id = str(item.get("id", "")).strip()
            parent = category_nodes.get(category, category_nodes.get("", ""))
            node_id = self._tree.insert(parent, "end", text=title or "(Untitled)")
            self._tree_items[node_id] = idx
            if item_id:
                self._tree_by_id[item_id] = node_id
        for node_id in category_nodes.values():
            self._tree.item(node_id, open=True)

    def _refresh_category_combo(self) -> None:
        values = [code for code, _ in _category_lookup(self._categories)]
        self._category_combo.configure(values=values)

    def _reset_selection(self) -> None:
        self._selected_index = None
        self._is_new_item = False

    def _on_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        index = self._tree_items.get(selection[0])
        if index is None:
            return
        self._selected_index = index
        self._is_new_item = False
        self._load_form(self._items[index])

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

    def _duplicate_item(self) -> None:
        if self._selected_index is None:
            return
        base = dict(self._items[self._selected_index])
        base["id"] = ""
        base["title"] = f"Copy of {base.get('title', '')}".strip()
        self._items.append(base)
        self._refresh_tree()

    def _delete_item(self) -> None:
        if self._selected_index is None:
            return
        item = self._items[self._selected_index]
        if not messagebox.askyesno(
            "Delete Misc Item",
            f"Delete item '{item.get('title') or item.get('id')}'?",
        ):
            return
        self._items.pop(self._selected_index)
        self._reset_selection()
        self._refresh_tree()
        self._clear_form()

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
            messagebox.showerror("Misc Item", "Label is required.")
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


def _category_lookup(categories: List[Dict[str, Any]]) -> List[tuple[str, str]]:
    pairs: List[tuple[str, str]] = []
    for entry in categories:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "")).strip()
        title = str(entry.get("title", "")).strip()
        if code:
            pairs.append((code, title or code))
    return pairs


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


def _has_form_data(title: str, text: str) -> bool:
    return any(value.strip() for value in (title, text))


def _set_text(widget: tk.Text, value: Any) -> None:
    widget.delete("1.0", tk.END)
    if value is not None and str(value).strip():
        widget.insert("1.0", str(value))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c").strip()
