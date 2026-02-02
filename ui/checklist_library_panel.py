from __future__ import annotations

from copy import deepcopy
from typing import Dict, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from core.checklist_store import (
    load_template_checklists,
    save_template_checklists,
    validate_checklists,
)


class ChecklistLibraryPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, *, on_saved=None) -> None:
        super().__init__(master)
        self._on_saved = on_saved
        self._checklists: Dict[str, dict] = {}
        self._selection: Optional[Tuple[str, str, str]] = None
        self._build_ui()
        self._load_checklists()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(self, show="tree")
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=6)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        scroll = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=0, sticky="nse", padx=(0, 8), pady=6)

        editor = ttk.Frame(self)
        editor.grid(row=0, column=1, sticky="nsew", pady=6)
        editor.columnconfigure(1, weight=1)

        ttk.Label(editor, text="Level").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._level_var = tk.StringVar(value="")
        ttk.Label(editor, textvariable=self._level_var).grid(
            row=0, column=1, sticky="w", pady=(0, 4)
        )

        ttk.Label(editor, text="Label").grid(row=1, column=0, sticky="w")
        self._label_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self._label_var).grid(
            row=1, column=1, sticky="ew"
        )

        ttk.Label(editor, text="Item text").grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self._item_text = tk.Text(editor, height=4, wrap="word")
        self._item_text.grid(row=2, column=1, sticky="ew", pady=(8, 0))

        button_row = ttk.Frame(editor)
        button_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(button_row, text="Apply Changes", command=self._apply_edit).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Up", command=lambda: self._move_item(-1)).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Down", command=lambda: self._move_item(1)).pack(
            side="left", padx=(0, 6)
        )

        action_row = ttk.Frame(editor)
        action_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(action_row, text="New Group", command=self._new_group).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="New Category", command=self._new_category).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="New Item", command=self._new_item).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Delete", command=self._delete_selected).pack(
            side="left", padx=(0, 6)
        )

        footer = ttk.Frame(editor)
        footer.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Reload", command=self._load_checklists).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Validate", command=self._validate).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Save", command=self._save).pack(side="left")

    def _load_checklists(self) -> None:
        try:
            self._checklists = load_template_checklists()
        except Exception as exc:
            messagebox.showerror("Checklist Library", f"Load failed: {exc}")
            self._checklists = {}
        self._selection = None
        self._refresh_tree()
        self._clear_editor()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for group_name, categories in self._checklists.items():
            group_id = self._tree.insert("", "end", text=group_name, open=True)
            if not isinstance(categories, dict):
                continue
            for category_name, items in categories.items():
                category_id = self._tree.insert(group_id, "end", text=category_name, open=True)
                if not isinstance(items, list):
                    continue
                for item in items:
                    self._tree.insert(category_id, "end", text=str(item))

    def _on_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        item_id = selection[0]
        path = []
        while item_id:
            path.insert(0, self._tree.item(item_id, "text"))
            item_id = self._tree.parent(item_id)
        group = path[0] if len(path) >= 1 else ""
        category = path[1] if len(path) >= 2 else ""
        item = path[2] if len(path) >= 3 else ""
        self._selection = (group, category, item)
        self._load_editor()

    def _load_editor(self) -> None:
        group, category, item = self._selection or ("", "", "")
        if item:
            self._level_var.set("Item")
            self._label_var.set(item)
            _set_text(self._item_text, item)
        elif category:
            self._level_var.set("Category")
            self._label_var.set(category)
            _set_text(self._item_text, "")
        elif group:
            self._level_var.set("Group")
            self._label_var.set(group)
            _set_text(self._item_text, "")
        else:
            self._clear_editor()

    def _clear_editor(self) -> None:
        self._level_var.set("")
        self._label_var.set("")
        _set_text(self._item_text, "")

    def _apply_edit(self) -> None:
        if not self._selection:
            return
        group, category, item = self._selection
        label = self._label_var.get().strip()
        if item:
            new_text = _get_text(self._item_text).strip()
            if not new_text:
                messagebox.showerror("Checklist Library", "Item text cannot be empty.")
                return
            items = self._checklists.get(group, {}).get(category, [])
            if item not in items:
                return
            index = items.index(item)
            items[index] = new_text
            if label and label != item:
                items[index] = label
            self._selection = (group, category, items[index])
        elif category:
            if not label:
                messagebox.showerror("Checklist Library", "Category label cannot be empty.")
                return
            categories = self._checklists.get(group, {})
            if category not in categories:
                return
            if label != category:
                categories[label] = categories.pop(category)
                self._selection = (group, label, "")
        elif group:
            if not label:
                messagebox.showerror("Checklist Library", "Group label cannot be empty.")
                return
            if label != group:
                self._checklists[label] = self._checklists.pop(group)
                self._selection = (label, "", "")
        self._refresh_tree()
        self._restore_selection()

    def _restore_selection(self) -> None:
        if not self._selection:
            return
        group, category, item = self._selection
        for group_id in self._tree.get_children():
            if self._tree.item(group_id, "text") != group:
                continue
            if not category:
                self._tree.selection_set(group_id)
                return
            for category_id in self._tree.get_children(group_id):
                if self._tree.item(category_id, "text") != category:
                    continue
                if not item:
                    self._tree.selection_set(category_id)
                    return
                for item_id in self._tree.get_children(category_id):
                    if self._tree.item(item_id, "text") == item:
                        self._tree.selection_set(item_id)
                        return

    def _new_group(self) -> None:
        base = "New Group"
        name = _unique_key(self._checklists, base)
        self._checklists[name] = {}
        self._selection = (name, "", "")
        self._refresh_tree()
        self._restore_selection()

    def _new_category(self) -> None:
        group, _, _ = self._selection or ("", "", "")
        if not group:
            messagebox.showinfo("Checklist Library", "Select a group first.")
            return
        categories = self._checklists.get(group, {})
        name = _unique_key(categories, "New Category")
        categories[name] = []
        self._selection = (group, name, "")
        self._refresh_tree()
        self._restore_selection()

    def _new_item(self) -> None:
        group, category, _ = self._selection or ("", "", "")
        if not group or not category:
            messagebox.showinfo("Checklist Library", "Select a category first.")
            return
        items = self._checklists.get(group, {}).get(category, [])
        name = _unique_item(items, "New Item")
        items.append(name)
        self._selection = (group, category, name)
        self._refresh_tree()
        self._restore_selection()

    def _delete_selected(self) -> None:
        if not self._selection:
            return
        group, category, item = self._selection
        if item:
            items = self._checklists.get(group, {}).get(category, [])
            if item in items:
                items.remove(item)
                self._selection = (group, category, "")
        elif category:
            categories = self._checklists.get(group, {})
            if category in categories:
                del categories[category]
                self._selection = (group, "", "")
        elif group:
            if group in self._checklists:
                del self._checklists[group]
                self._selection = None
        self._refresh_tree()
        self._restore_selection()

    def _move_item(self, offset: int) -> None:
        if not self._selection:
            return
        group, category, item = self._selection
        if not item:
            return
        items = self._checklists.get(group, {}).get(category, [])
        if item not in items:
            return
        index = items.index(item)
        new_index = index + offset
        if new_index < 0 or new_index >= len(items):
            return
        items[index], items[new_index] = items[new_index], items[index]
        self._selection = (group, category, items[new_index])
        self._refresh_tree()
        self._restore_selection()

    def _validate(self) -> None:
        try:
            validate_checklists(deepcopy(self._checklists))
        except Exception as exc:
            messagebox.showerror("Checklist Library", f"Validation failed:\n{exc}")
            return
        messagebox.showinfo("Checklist Library", "Validation successful.")

    def _save(self) -> None:
        try:
            save_template_checklists(deepcopy(self._checklists))
        except Exception as exc:
            messagebox.showerror("Checklist Library", f"Save failed:\n{exc}")
            return
        messagebox.showinfo("Checklist Library", "Checklist library saved.")
        if self._on_saved:
            self._on_saved(deepcopy(self._checklists))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c")


def _set_text(widget: tk.Text, value: str) -> None:
    widget.delete("1.0", tk.END)
    if value:
        widget.insert("1.0", value)


def _unique_key(mapping: Dict[str, object], base: str) -> str:
    if base not in mapping:
        return base
    index = 2
    while True:
        candidate = f"{base} {index}"
        if candidate not in mapping:
            return candidate
        index += 1


def _unique_item(items: list, base: str) -> str:
    if base not in items:
        return base
    index = 2
    while True:
        candidate = f"{base} {index}"
        if candidate not in items:
            return candidate
        index += 1
