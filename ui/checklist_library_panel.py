from __future__ import annotations

from copy import deepcopy
from typing import Dict, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from ui.ui_state import load_ui_state, save_ui_state

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
        self._target_options = [
            ("Central Heating/Cooling", "heating"),
            ("Central Ventilation", "ventilation"),
            ("DHW", "dhw"),
            ("Miscellaneous", "misc"),
        ]
        self._search_var = tk.StringVar(value="")
        self._build_ui()
        self._load_checklists()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._paned = ttk.PanedWindow(self, orient="horizontal")
        self._paned.grid(row=0, column=0, sticky="nsew")

        list_frame = ttk.Frame(self)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        search_row = ttk.Frame(list_frame)
        search_row.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(6, 2))
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
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 6))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(tree_frame, show="tree")
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        editor = ttk.Frame(self)
        editor.columnconfigure(1, weight=1)
        editor.rowconfigure(3, weight=1)

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

        ttk.Label(editor, text="Target section").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._target_var = tk.StringVar()
        self._target_combo = ttk.Combobox(
            editor,
            textvariable=self._target_var,
            values=[label for label, _ in self._target_options],
            state="readonly",
        )
        self._target_combo.grid(row=2, column=1, sticky="w", pady=(8, 0))

        ttk.Label(editor, text="Item text").grid(row=3, column=0, sticky="nw", pady=(8, 0))
        text_frame = ttk.Frame(editor)
        text_frame.grid(row=3, column=1, sticky="nsew", pady=(8, 0))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self._item_text = tk.Text(text_frame, height=10, wrap="word")
        self._item_text.grid(row=0, column=0, sticky="nsew")
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self._item_text.yview)
        self._item_text.configure(yscrollcommand=text_scroll.set)
        text_scroll.grid(row=0, column=1, sticky="ns")

        button_row = ttk.Frame(editor)
        button_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
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
        action_row.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
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
        footer.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Reload", command=self._load_checklists).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Validate", command=self._validate).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Save", command=self._save).pack(side="left")

        self._paned.add(list_frame, weight=2)
        self._paned.add(editor, weight=5)

        self.after(20, self._restore_paned_position)
        self._paned.bind("<ButtonRelease-1>", lambda _e: self._save_paned_position(), add=True)

        self.bind_all("<Control-s>", self._handle_ctrl_s, add=True)
        self.bind_all("<Control-f>", self._handle_ctrl_f, add=True)
        self.bind_all("<Control-Return>", self._handle_ctrl_enter, add=True)

    def _restore_paned_position(self) -> None:
        state = load_ui_state("checklist_library")
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
        save_ui_state("checklist_library", {"sash": pos})

    def _handle_ctrl_s(self, _event: tk.Event) -> str:
        if self.winfo_ismapped():
            self._save()
            return "break"
        return ""

    def _handle_ctrl_f(self, _event: tk.Event) -> str:
        if self.winfo_ismapped():
            self._search_entry.focus_set()
            self._search_entry.selection_range(0, tk.END)
            return "break"
        return ""

    def _handle_ctrl_enter(self, _event: tk.Event) -> str:
        if self.winfo_ismapped():
            self._apply_edit()
            return "break"
        return ""

    def _sort_alphabetically(self) -> None:
        selection = self._selection
        self._checklists = _sorted_checklists(self._checklists)
        self._refresh_tree()
        self._selection = selection
        self._restore_selection()

    def _load_checklists(self) -> None:
        try:
            self._checklists = _normalize_checklists(load_template_checklists())
        except Exception as exc:
            messagebox.showerror("Checklist Library", f"Load failed: {exc}")
            self._checklists = {}
        self._selection = None
        self._refresh_tree()
        self._clear_editor()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        term = self._search_var.get().strip().lower()
        for group_name, categories in self._checklists.items():
            if not isinstance(categories, dict):
                continue
            group_match = bool(term and term in group_name.lower())
            visible_categories = []
            for category_name in categories.keys():
                item_list = _get_category_items(self._checklists, group_name, category_name)
                labels = [_item_label(item) for item in item_list]
                category_match = bool(term and term in category_name.lower())
                matching_labels = [label for label in labels if term and term in label.lower()]
                if not term or group_match or category_match or matching_labels:
                    visible_categories.append((category_name, labels, matching_labels, category_match))
            if term and not group_match and not visible_categories:
                continue
            group_id = self._tree.insert("", "end", text=group_name, open=True)
            for category_name, labels, matching_labels, category_match in visible_categories:
                category_id = self._tree.insert(group_id, "end", text=category_name, open=True)
                labels_to_show = labels if (not term or group_match or category_match) else matching_labels
                for label in labels_to_show:
                    self._tree.insert(category_id, "end", text=label)

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
            item_data = _find_item(self._checklists, group, category, item)
            self._label_var.set(_item_label(item_data))
            _set_text(self._item_text, _item_text(item_data))
            self._target_var.set("")
            self._target_combo.configure(state="disabled")
        elif category:
            self._level_var.set("Category")
            self._label_var.set(category)
            _set_text(self._item_text, "")
            target = _get_category_target(self._checklists, group, category)
            self._target_var.set(_label_for_target(target, self._target_options))
            self._target_combo.configure(state="readonly")
        elif group:
            self._level_var.set("Group")
            self._label_var.set(group)
            _set_text(self._item_text, "")
            self._target_var.set("")
            self._target_combo.configure(state="disabled")
        else:
            self._clear_editor()

    def _clear_editor(self) -> None:
        self._level_var.set("")
        self._label_var.set("")
        self._target_var.set("")
        self._target_combo.configure(state="disabled")
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
            items = _get_category_items(self._checklists, group, category)
            item_data = _find_item(self._checklists, group, category, item)
            if item_data is None:
                return
            if label:
                item_data["label"] = label
            item_data["text"] = new_text
            self._selection = (group, category, item_data["label"])
        elif category:
            if not label:
                messagebox.showerror("Checklist Library", "Category label cannot be empty.")
                return
            categories = self._checklists.get(group, {})
            if category not in categories:
                return
            target_value = _value_for_target(self._target_var.get(), self._target_options)
            if label != category:
                categories[label] = categories.pop(category)
                self._selection = (group, label, "")
                _set_category_target(categories[label], target_value)
            else:
                _set_category_target(categories[category], target_value)
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
        categories[name] = {"items": [], "target_block": "misc"}
        self._selection = (group, name, "")
        self._refresh_tree()
        self._restore_selection()

    def _new_item(self) -> None:
        group, category, _ = self._selection or ("", "", "")
        if not group or not category:
            messagebox.showinfo("Checklist Library", "Select a category first.")
            return
        items = _get_category_items(self._checklists, group, category)
        name = _unique_item([_item_label(item) for item in items], "New Item")
        items.append({"label": name, "text": ""})
        self._selection = (group, category, name)
        self._refresh_tree()
        self._restore_selection()

    def _delete_selected(self) -> None:
        if not self._selection:
            return
        group, category, item = self._selection
        if item:
            items = _get_category_items(self._checklists, group, category)
            item_data = _find_item(self._checklists, group, category, item)
            if item_data in items:
                items.remove(item_data)
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
        items = _get_category_items(self._checklists, group, category)
        item_data = _find_item(self._checklists, group, category, item)
        if item_data is None:
            return
        index = items.index(item_data)
        new_index = index + offset
        if new_index < 0 or new_index >= len(items):
            return
        items[index], items[new_index] = items[new_index], items[index]
        self._selection = (group, category, _item_label(items[new_index]))
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


def _normalize_checklists(checklists: Dict[str, dict]) -> Dict[str, dict]:
    normalized: Dict[str, dict] = {}
    for group_name, categories in checklists.items():
        if not isinstance(categories, dict):
            continue
        normalized[group_name] = {}
        for category_name, items in categories.items():
            if isinstance(items, list):
                normalized[group_name][category_name] = {
                    "items": [_item_dict(item) for item in items],
                    "target_block": "misc",
                }
            elif isinstance(items, dict):
                item_list = items.get("items", [])
                target = items.get("target_block", "misc")
                normalized[group_name][category_name] = {
                    "items": [_item_dict(item) for item in item_list]
                    if isinstance(item_list, list)
                    else [],
                    "target_block": str(target) if target else "misc",
                }
    return normalized


def _sorted_checklists(checklists: Dict[str, dict]) -> Dict[str, dict]:
    sorted_groups: Dict[str, dict] = {}
    for group_name in sorted(checklists.keys(), key=lambda value: value.lower()):
        categories = checklists.get(group_name, {})
        if not isinstance(categories, dict):
            continue
        sorted_categories: Dict[str, dict] = {}
        for category_name in sorted(categories.keys(), key=lambda value: value.lower()):
            category_data = categories.get(category_name, {})
            if not isinstance(category_data, dict):
                continue
            target_block = str(category_data.get("target_block", "misc") or "misc")
            items = [dict(item) if isinstance(item, dict) else _item_dict(item) for item in _get_category_items(checklists, group_name, category_name)]
            items.sort(key=lambda item: _item_label(item).lower())
            sorted_categories[category_name] = {
                "items": items,
                "target_block": target_block,
            }
        sorted_groups[group_name] = sorted_categories
    return sorted_groups


def _get_category_items(
    checklists: Dict[str, dict], group: str, category: str
) -> list:
    category_data = checklists.get(group, {}).get(category, {})
    if isinstance(category_data, dict):
        items = category_data.get("items", [])
        if isinstance(items, list):
            return items
    if isinstance(category_data, list):
        return [_item_dict(item) for item in category_data]
    return []


def _get_category_target(checklists: Dict[str, dict], group: str, category: str) -> str:
    category_data = checklists.get(group, {}).get(category, {})
    if isinstance(category_data, dict):
        target = category_data.get("target_block", "misc")
        return str(target or "misc")
    return "misc"


def _set_category_target(category_data: object, target: str) -> None:
    if isinstance(category_data, dict):
        category_data["target_block"] = target or "misc"


def _label_for_target(value: str, options: list[tuple[str, str]]) -> str:
    for label, code in options:
        if code == value:
            return label
    return options[-1][0] if options else ""


def _value_for_target(label: str, options: list[tuple[str, str]]) -> str:
    for opt_label, code in options:
        if opt_label == label:
            return code
    return options[-1][1] if options else "misc"


def _item_dict(value: object) -> dict:
    if isinstance(value, dict):
        label = value.get("label")
        text = value.get("text")
        return {
            "label": str(label) if label is not None else "",
            "text": str(text) if text is not None else str(label or ""),
        }
    text = str(value) if value is not None else ""
    return {"label": text, "text": text}


def _item_label(item: object) -> str:
    if isinstance(item, dict):
        label = item.get("label")
        if isinstance(label, str) and label.strip():
            return label
        text = item.get("text")
        return str(text) if text is not None else ""
    return str(item) if item is not None else ""


def _item_text(item: object) -> str:
    if isinstance(item, dict):
        text = item.get("text")
        if isinstance(text, str):
            return text
        label = item.get("label")
        return str(label) if label is not None else ""
    return str(item) if item is not None else ""


def _find_item(
    checklists: Dict[str, dict], group: str, category: str, label: str
) -> Optional[dict]:
    for item in _get_category_items(checklists, group, category):
        if _item_label(item) == label:
            return item
    return None
