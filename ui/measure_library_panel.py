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
from ui.ui_state import load_ui_state, save_ui_state


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
        self._search_var.trace_add("write", lambda *_args: self._refresh_measure_tree())

        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=(6, 8), pady=(0, 6))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self._measure_tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self._measure_tree.grid(row=0, column=0, sticky="nsew")
        self._measure_tree.bind("<<TreeviewSelect>>", self._on_measure_select)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self._measure_tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._measure_tree.xview)
        self._measure_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        editor = ttk.Frame(self)
        editor.columnconfigure(1, weight=1)
        editor.rowconfigure(2, weight=1)
        editor.rowconfigure(3, weight=1)
        editor.rowconfigure(4, weight=1)

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
        self._measure_existing = self._build_text_with_scroll(editor, row=2, column=1)

        ttk.Label(editor, text="Retrofit Conditions").grid(
            row=3, column=0, sticky="nw", pady=4
        )
        self._measure_retrofit = self._build_text_with_scroll(editor, row=3, column=1)

        ttk.Label(editor, text="Summary").grid(row=4, column=0, sticky="nw", pady=4)
        self._measure_summary = self._build_text_with_scroll(editor, row=4, column=1)

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
        ttk.Button(action_row, text="Delete", command=self._delete_measure).pack(side="left")

        footer = ttk.Frame(editor)
        footer.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 0))
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

        self.bind_all("<Control-s>", self._handle_ctrl_s, add=True)
        self.bind_all("<Control-f>", self._handle_ctrl_f, add=True)
        self.bind_all("<Control-Return>", self._handle_ctrl_enter, add=True)

    def _build_text_with_scroll(self, parent: ttk.Frame, *, row: int, column: int) -> tk.Text:
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="nsew", pady=2)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = tk.Text(frame, height=8, wrap="word")
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        return text

    def _restore_paned_position(self) -> None:
        state = load_ui_state("measure_library")
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
        save_ui_state("measure_library", {"sash": pos})

    def _handle_ctrl_s(self, _event: tk.Event) -> str:
        if self.winfo_ismapped():
            self._save_catalog()
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
            self._apply_measure()
            return "break"
        return ""

    def _sort_alphabetically(self) -> None:
        self._maybe_apply_measure()
        selected_measure_id = self._measure_id_var if self._measure_id_var else ""
        category_title_by_code = {
            str(item.get("code", "")).strip(): str(item.get("tab_title", "")).strip().lower()
            for item in self._categories
            if isinstance(item, dict)
        }
        self._categories.sort(
            key=lambda item: (
                str(item.get("tab_title", "")).strip().lower(),
                str(item.get("code", "")).strip().lower(),
            )
        )
        self._measures.sort(
            key=lambda item: (
                category_title_by_code.get(str(item.get("category", "")).strip(), "~"),
                str(item.get("title", "")).strip().lower(),
            )
        )
        self._refresh_measure_tree()
        if selected_measure_id:
            self._select_measure_by_id(selected_measure_id)

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
        self._measure_tree_by_id: Dict[str, str] = {}
        categories = _category_lookup(self._categories)
        category_nodes: Dict[str, str] = {}
        term = self._search_var.get().strip().lower()

        for code, title in categories:
            category_nodes[code] = self._measure_tree.insert("", "end", text=title)
        if "" not in category_nodes:
            category_nodes[""] = self._measure_tree.insert("", "end", text="Uncategorized")

        visible_counts: Dict[str, int] = {key: 0 for key in category_nodes}
        for idx, measure in enumerate(self._measures):
            title = str(measure.get("title", "")).strip()
            category = str(measure.get("category", "")).strip()
            item_id = str(measure.get("id", "")).strip()
            if term and term not in title.lower() and term not in category.lower():
                continue
            parent = category_nodes.get(category, category_nodes.get("", ""))
            node_id = self._measure_tree.insert(parent, "end", text=title or "(Untitled)")
            self._measure_tree_items[node_id] = idx
            if item_id:
                self._measure_tree_by_id[item_id] = node_id
            cat_key = category if category in visible_counts else ""
            visible_counts[cat_key] = visible_counts.get(cat_key, 0) + 1

        for key, node_id in list(category_nodes.items()):
            if visible_counts.get(key, 0) == 0:
                self._measure_tree.delete(node_id)
                continue
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
        measure_id = str(self._measures[new_index].get("id", "")).strip()
        self._select_measure_by_id(measure_id)

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
        self._select_measure_by_id(measure_id)

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
        messagebox.showinfo("Measure Catalog", "Catalog saved successfully.")
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

    def _select_measure_by_id(self, measure_id: str) -> None:
        if not measure_id:
            return
        item_id = self._measure_tree_by_id.get(measure_id)
        if item_id:
            self._measure_tree.selection_set(item_id)


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
