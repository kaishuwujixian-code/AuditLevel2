from __future__ import annotations

from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from core.measure_catalog import (
    load_measure_catalog,
    load_measure_catalog_data,
    save_measure_catalog_data,
    validate_measure_catalog_data,
)
from core.paths import DEFAULT_MEASURE_CATALOG


class MeasureLibraryPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_catalog_saved=None,
    ) -> None:
        super().__init__(master)
        self._on_catalog_saved = on_catalog_saved
        self._catalog_path = DEFAULT_MEASURE_CATALOG
        self._measures: List[Dict[str, Any]] = []
        self._categories: List[Dict[str, Any]] = []
        self._selected_measure_index: Optional[int] = None
        self._is_new_measure = False
        self._measure_id_var = ""
        self._build_ui()
        self._load_catalog()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_measures_tab()

    def _build_measures_tab(self) -> None:
        list_frame = ttk.Frame(self)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=6)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._measure_tree = ttk.Treeview(
            list_frame, show="tree", selectmode="browse"
        )
        self._measure_tree.grid(row=0, column=0, sticky="nsew")
        measure_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self._measure_tree.yview
        )
        self._measure_tree.configure(yscrollcommand=measure_scroll.set)
        measure_scroll.grid(row=0, column=1, sticky="ns")
        self._measure_tree.bind("<<TreeviewSelect>>", self._on_measure_select)

        editor = ttk.Frame(self)
        editor.grid(row=0, column=1, sticky="nsew", pady=6, padx=(0, 6))
        editor.columnconfigure(1, weight=1)

        ttk.Label(editor, text="Label").grid(row=0, column=0, sticky="w", pady=2)
        self._measure_title_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self._measure_title_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(editor, text="Category").grid(row=1, column=0, sticky="w", pady=2)
        self._measure_category_var = tk.StringVar()
        self._measure_category_combo = ttk.Combobox(
            editor, textvariable=self._measure_category_var, state="readonly"
        )
        self._measure_category_combo.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Existing Conditions").grid(
            row=2, column=0, sticky="nw", pady=4
        )
        self._measure_existing = tk.Text(editor, height=4, wrap="word")
        self._measure_existing.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Retrofit Conditions").grid(
            row=3, column=0, sticky="nw", pady=4
        )
        self._measure_retrofit = tk.Text(editor, height=4, wrap="word")
        self._measure_retrofit.grid(row=3, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Summary").grid(row=4, column=0, sticky="nw", pady=4)
        self._measure_summary = tk.Text(editor, height=4, wrap="word")
        self._measure_summary.grid(row=4, column=1, sticky="ew", pady=2)

        button_row = ttk.Frame(editor)
        button_row.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(button_row, text="Apply Changes", command=self._apply_measure).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Up", command=lambda: self._move_measure(-1)).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Down", command=lambda: self._move_measure(1)).pack(
            side="left"
        )

        action_row = ttk.Frame(editor)
        action_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(action_row, text="New Item", command=self._new_measure).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Duplicate", command=self._duplicate_measure).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Delete", command=self._delete_measure).pack(
            side="left"
        )

        footer = ttk.Frame(editor)
        footer.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Reload", command=self._load_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Validate", command=self._validate_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Save", command=self._save_catalog).pack(side="left")

    def _load_catalog(self) -> None:
        try:
            data = load_measure_catalog_data(self._catalog_path)
        except Exception as exc:
            messagebox.showerror("Measure Catalog", f"Load failed: {exc}")
            self._measures = []
            self._categories = []
            self._refresh_ui()
            return

        self._measures = [dict(item) for item in data.get("measures", [])]
        self._categories = [dict(item) for item in data.get("categories", [])]
        self._reset_selection()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        self._refresh_measure_tree()
        self._refresh_category_combo()
        self._clear_measure_form()

    def _refresh_measure_tree(self) -> None:
        self._measure_tree.delete(*self._measure_tree.get_children())
        self._measure_tree_items: Dict[str, int] = {}
        categories = _category_lookup(self._categories)
        category_nodes: Dict[str, str] = {}
        for code, title in categories:
            category_nodes[code] = self._measure_tree.insert("", "end", text=title)
        if "" not in category_nodes:
            category_nodes[""] = self._measure_tree.insert("", "end", text="Uncategorized")
        for idx, measure in enumerate(self._measures):
            title = str(measure.get("title", "")).strip()
            category = str(measure.get("category", "")).strip()
            parent = category_nodes.get(category, category_nodes.get("", ""))
            item_id = self._measure_tree.insert(parent, "end", text=title or "(Untitled)")
            self._measure_tree_items[item_id] = idx
        for node_id in category_nodes.values():
            self._measure_tree.item(node_id, open=True)

    def _refresh_category_combo(self) -> None:
        values = [str(item.get("code", "")).strip() for item in self._categories if item]
        self._measure_category_combo.configure(values=values)

    def _reset_selection(self) -> None:
        self._selected_measure_index = None
        self._is_new_measure = False

    def _on_measure_select(self, _event: tk.Event) -> None:
        selection = self._measure_tree.selection()
        if not selection:
            return
        index = self._measure_tree_items.get(selection[0])
        if index is None:
            return
        self._selected_measure_index = index
        self._is_new_measure = False
        self._load_measure_form(self._measures[index])

    def _load_measure_form(self, measure: Dict[str, Any]) -> None:
        self._measure_title_var.set(str(measure.get("title", "")).strip())
        self._measure_category_var.set(str(measure.get("category", "")).strip())
        _set_text(self._measure_existing, measure.get("existing"))
        _set_text(self._measure_retrofit, measure.get("retrofit"))
        _set_text(self._measure_summary, measure.get("summary"))
        self._measure_id_var = str(measure.get("id", "")).strip()

    def _clear_measure_form(self) -> None:
        self._measure_title_var.set("")
        self._measure_category_var.set("")
        _set_text(self._measure_existing, "")
        _set_text(self._measure_retrofit, "")
        _set_text(self._measure_summary, "")
        self._measure_id_var = ""

    def _new_measure(self) -> None:
        self._measure_tree.selection_remove(self._measure_tree.selection())
        self._selected_measure_index = None
        self._is_new_measure = True
        self._clear_measure_form()

    def _duplicate_measure(self) -> None:
        if self._selected_measure_index is None:
            return
        base = dict(self._measures[self._selected_measure_index])
        base["id"] = ""
        base["title"] = f"Copy of {base.get('title', '')}".strip()
        self._measures.append(base)
        self._refresh_measure_tree()

    def _delete_measure(self) -> None:
        if self._selected_measure_index is None:
            return
        measure = self._measures[self._selected_measure_index]
        if not messagebox.askyesno(
            "Delete Measure",
            f"Delete measure '{measure.get('title') or measure.get('id')}'?",
        ):
            return
        self._measures.pop(self._selected_measure_index)
        self._reset_selection()
        self._refresh_measure_tree()
        self._clear_measure_form()

    def _move_measure(self, offset: int) -> None:
        if self._selected_measure_index is None:
            return
        new_index = self._selected_measure_index + offset
        if new_index < 0 or new_index >= len(self._measures):
            return
        self._measures[self._selected_measure_index], self._measures[new_index] = (
            self._measures[new_index],
            self._measures[self._selected_measure_index],
        )
        self._selected_measure_index = new_index
        self._refresh_measure_tree()
        for item_id, idx in self._measure_tree_items.items():
            if idx == new_index:
                self._measure_tree.selection_set(item_id)
                break

    def _apply_measure(self) -> None:
        measure_id = self._measure_id_var
        if not measure_id:
            measure_id = _unique_measure_id(
                _slugify(self._measure_title_var.get().strip()), self._measures
            )
        if not measure_id:
            messagebox.showerror("Measure", "Label is required.")
            return
        payload = {
            "id": measure_id,
            "title": self._measure_title_var.get().strip(),
            "category": self._measure_category_var.get().strip(),
            "existing": _get_text(self._measure_existing),
            "retrofit": _get_text(self._measure_retrofit),
            "summary": _get_text(self._measure_summary),
        }
        if self._is_new_measure or self._selected_measure_index is None:
            self._measures.append(payload)
            self._selected_measure_index = len(self._measures) - 1
            self._is_new_measure = False
        else:
            current = self._measures[self._selected_measure_index]
            current.update(payload)
        self._refresh_measure_tree()
        for item_id, idx in self._measure_tree_items.items():
            if idx == self._selected_measure_index:
                self._measure_tree.selection_set(item_id)
                break

    def _validate_catalog(self) -> None:
        try:
            validate_measure_catalog_data(
                {"categories": self._categories, "measures": self._measures}
            )
        except Exception as exc:
            messagebox.showerror("Measure Catalog", f"Validation failed:\n{exc}")
            return
        messagebox.showinfo("Measure Catalog", "Validation successful.")

    def _save_catalog(self) -> None:
        self._maybe_apply_measure()
        try:
            save_measure_catalog_data(
                {"categories": self._categories, "measures": self._measures},
                path=self._catalog_path,
                backup=True,
            )
        except Exception as exc:
            messagebox.showerror("Measure Catalog", f"Save failed:\n{exc}")
            return
        if self._on_catalog_saved:
            try:
                self._on_catalog_saved(load_measure_catalog(self._catalog_path))
            except Exception:
                pass

    def _maybe_apply_measure(self) -> None:
        if not _has_form_data(
            self._measure_title_var.get().strip(),
            _get_text(self._measure_existing),
            _get_text(self._measure_retrofit),
            _get_text(self._measure_summary),
        ):
            return
        if self._is_new_measure or self._selected_measure_index is not None:
            self._apply_measure()


def _set_text(widget: tk.Text, value: Any) -> None:
    widget.delete("1.0", tk.END)
    if value is not None and str(value).strip():
        widget.insert("1.0", str(value))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c").strip()


def _category_lookup(categories: List[Dict[str, Any]]) -> List[tuple[str, str]]:
    pairs: List[tuple[str, str]] = []
    for entry in categories:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "")).strip()
        title = str(entry.get("tab_title", "")).strip()
        if code:
            pairs.append((code, title or code))
    return pairs


def _slugify(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.lower())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def _unique_measure_id(candidate: str, measures: List[Dict[str, Any]]) -> str:
    if not candidate:
        return ""
    existing = {str(item.get("id", "")).strip() for item in measures}
    if candidate not in existing:
        return candidate
    index = 2
    while True:
        alt = f"{candidate}_{index}"
        if alt not in existing:
            return alt
        index += 1


def _has_form_data(title: str, existing: str, retrofit: str, summary: str) -> bool:
    return any(value.strip() for value in (title, existing, retrofit, summary))
