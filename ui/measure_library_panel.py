from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
        self._status_var = tk.StringVar(value="Ready")
        self._build_ui()
        self._load_catalog()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(6, 4))
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Button(toolbar, text="Reload Catalog", command=self._load_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(toolbar, text="Validate", command=self._validate_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(toolbar, text="Save Catalog", command=self._save_catalog).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(toolbar, text="Save As...", command=self._save_catalog_as).pack(
            side="left"
        )

        self._measures_tab = ttk.Frame(self, padding=(6, 6))
        self._measures_tab.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self._build_measures_tab()

        status_bar = ttk.Label(
            self,
            textvariable=self._status_var,
            anchor="w",
            relief="sunken",
            padding=(6, 4),
        )
        status_bar.grid(row=2, column=0, sticky="ew")

    def _build_measures_tab(self) -> None:
        self._measures_tab.columnconfigure(1, weight=1)
        self._measures_tab.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(self._measures_tab)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        ttk.Label(list_frame, text="Measure Library").grid(row=0, column=0, sticky="w")
        columns = ("id", "title", "category")
        self._measure_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
        )
        for col in columns:
            self._measure_tree.heading(col, text=col.title())
            self._measure_tree.column(col, width=140, anchor="w")
        self._measure_tree.grid(row=1, column=0, sticky="nsew")
        measure_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self._measure_tree.yview
        )
        self._measure_tree.configure(yscrollcommand=measure_scroll.set)
        measure_scroll.grid(row=1, column=1, sticky="ns")
        self._measure_tree.bind("<<TreeviewSelect>>", self._on_measure_select)

        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(button_frame, text="New", command=self._new_measure).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_frame, text="Duplicate", command=self._duplicate_measure).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_frame, text="Delete", command=self._delete_measure).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_frame, text="Move Up", command=lambda: self._move_measure(-1)).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(
            button_frame, text="Move Down", command=lambda: self._move_measure(1)
        ).pack(side="left", padx=(0, 6))
        ttk.Button(button_frame, text="Apply Changes", command=self._apply_measure).pack(
            side="left"
        )

        form = ttk.Frame(self._measures_tab)
        form.grid(row=0, column=1, sticky="nsew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Measure ID").grid(row=0, column=0, sticky="w", pady=2)
        self._measure_id_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._measure_id_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(form, text="Title").grid(row=1, column=0, sticky="w", pady=2)
        self._measure_title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._measure_title_var).grid(
            row=1, column=1, sticky="ew", pady=2
        )

        ttk.Label(form, text="Category").grid(row=2, column=0, sticky="w", pady=2)
        self._measure_category_var = tk.StringVar()
        self._measure_category_combo = ttk.Combobox(
            form, textvariable=self._measure_category_var, state="readonly"
        )
        self._measure_category_combo.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(form, text="Existing Conditions").grid(
            row=3, column=0, sticky="nw", pady=4
        )
        self._measure_existing = tk.Text(form, height=4, wrap="word")
        self._measure_existing.grid(row=3, column=1, sticky="ew", pady=2)

        ttk.Label(form, text="Retrofit Conditions").grid(
            row=4, column=0, sticky="nw", pady=4
        )
        self._measure_retrofit = tk.Text(form, height=4, wrap="word")
        self._measure_retrofit.grid(row=4, column=1, sticky="ew", pady=2)

        ttk.Label(form, text="Summary").grid(row=5, column=0, sticky="nw", pady=4)
        self._measure_summary = tk.Text(form, height=4, wrap="word")
        self._measure_summary.grid(row=5, column=1, sticky="ew", pady=2)

    def _set_status(self, message: str) -> None:
        self._status_var.set(message)

    def _load_catalog(self) -> None:
        try:
            data = load_measure_catalog_data(self._catalog_path)
        except Exception as exc:
            messagebox.showerror("Measure Catalog", f"Load failed: {exc}")
            self._measures = []
            self._categories = []
            self._refresh_ui()
            self._set_status("Failed to load catalog.")
            return

        self._measures = [dict(item) for item in data.get("measures", [])]
        self._categories = [dict(item) for item in data.get("categories", [])]
        self._reset_selection()
        self._refresh_ui()
        self._set_status(f"Loaded catalog: {self._catalog_path}")

    def _refresh_ui(self) -> None:
        self._refresh_measure_tree()
        self._refresh_category_combo()
        self._clear_measure_form()

    def _refresh_measure_tree(self) -> None:
        self._measure_tree.delete(*self._measure_tree.get_children())
        for idx, measure in enumerate(self._measures):
            measure_id = str(measure.get("id", "")).strip()
            title = str(measure.get("title", "")).strip()
            category = str(measure.get("category", "")).strip()
            self._measure_tree.insert(
                "", "end", iid=str(idx), values=(measure_id, title, category)
            )

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
        index = int(selection[0])
        self._selected_measure_index = index
        self._is_new_measure = False
        self._load_measure_form(self._measures[index])

    def _load_measure_form(self, measure: Dict[str, Any]) -> None:
        self._measure_id_var.set(str(measure.get("id", "")).strip())
        self._measure_title_var.set(str(measure.get("title", "")).strip())
        self._measure_category_var.set(str(measure.get("category", "")).strip())
        _set_text(self._measure_existing, measure.get("existing"))
        _set_text(self._measure_retrofit, measure.get("retrofit"))
        _set_text(self._measure_summary, measure.get("summary"))

    def _clear_measure_form(self) -> None:
        self._measure_id_var.set("")
        self._measure_title_var.set("")
        self._measure_category_var.set("")
        _set_text(self._measure_existing, "")
        _set_text(self._measure_retrofit, "")
        _set_text(self._measure_summary, "")

    def _new_measure(self) -> None:
        self._measure_tree.selection_remove(self._measure_tree.selection())
        self._selected_measure_index = None
        self._is_new_measure = True
        self._clear_measure_form()
        self._set_status("Creating new measure.")

    def _duplicate_measure(self) -> None:
        if self._selected_measure_index is None:
            return
        base = dict(self._measures[self._selected_measure_index])
        base["id"] = ""
        base["title"] = f"Copy of {base.get('title', '')}".strip()
        self._measures.append(base)
        self._refresh_measure_tree()
        self._set_status("Duplicated measure. Update the ID before saving.")

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
        self._set_status("Measure deleted.")

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
        self._measure_tree.selection_set(str(new_index))
        self._set_status("Measure order updated.")

    def _apply_measure(self) -> None:
        measure_id = self._measure_id_var.get().strip()
        if not measure_id:
            messagebox.showerror("Measure", "Measure ID is required.")
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
        self._measure_tree.selection_set(str(self._selected_measure_index))
        self._set_status("Measure updated.")

    def _validate_catalog(self) -> None:
        try:
            validate_measure_catalog_data(
                {"categories": self._categories, "measures": self._measures}
            )
        except Exception as exc:
            messagebox.showerror("Measure Catalog", f"Validation failed:\n{exc}")
            self._set_status("Validation failed.")
            return
        messagebox.showinfo("Measure Catalog", "Validation successful.")
        self._set_status("Validation successful.")

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
            self._set_status("Save failed.")
            return
        self._set_status(f"Saved catalog: {self._catalog_path}")
        if self._on_catalog_saved:
            try:
                self._on_catalog_saved(load_measure_catalog(self._catalog_path))
            except Exception:
                pass

    def _save_catalog_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Measure Catalog",
            initialdir=os.path.dirname(self._catalog_path) if self._catalog_path else None,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        self._catalog_path = path
        self._save_catalog()

    def _maybe_apply_measure(self) -> None:
        measure_id = self._measure_id_var.get().strip()
        if not measure_id:
            return
        if self._is_new_measure or self._selected_measure_index is not None:
            self._apply_measure()


def _set_text(widget: tk.Text, value: Any) -> None:
    widget.delete("1.0", tk.END)
    if value is not None and str(value).strip():
        widget.insert("1.0", str(value))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c").strip()
