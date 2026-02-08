from __future__ import annotations

from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from core.misc_catalog import (
    DEFAULT_MISC_CATALOG,
    load_misc_catalog,
    save_misc_catalog_data,
    validate_misc_catalog_data,
)
from ui.misc_editor import MiscEditor


class MiscLibraryPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._catalog_path = DEFAULT_MISC_CATALOG
        self._catalog: Optional[Dict[str, Any]] = None
        self._editor: Optional[MiscEditor] = None
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
            side="left"
        )

        self._editor = MiscEditor(self)
        self._editor.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

        status_bar = ttk.Label(
            self,
            textvariable=self._status_var,
            anchor="w",
            relief="sunken",
            padding=(6, 4),
        )
        status_bar.grid(row=2, column=0, sticky="ew")

    def _load_catalog(self) -> None:
        if not self._editor:
            return
        try:
            catalog = load_misc_catalog(self._catalog_path)
            ordered_items = [catalog.items[item_id] for item_id in catalog.order]
            self._catalog = {
                "categories": catalog.categories,
                "items": ordered_items,
            }
            self._editor.set_categories(catalog.categories)
            self._editor.set_items(ordered_items)
            self._set_status("Catalog loaded.")
        except Exception as exc:
            self._catalog = None
            messagebox.showerror("Misc Library", f"Load failed: {exc}")
            self._set_status("Load failed.")

    def _validate_catalog(self) -> None:
        if not self._editor:
            return
        data = self._collect_payload()
        try:
            validate_misc_catalog_data(data)
        except Exception as exc:
            messagebox.showerror("Misc Library", str(exc))
            self._set_status("Validation failed.")
            return
        messagebox.showinfo("Misc Library", "Catalog validation passed.")
        self._set_status("Catalog validated.")

    def _save_catalog(self) -> None:
        if not self._editor:
            return
        data = self._collect_payload()
        try:
            save_misc_catalog_data(data, self._catalog_path)
        except Exception as exc:
            messagebox.showerror("Misc Library", f"Save failed: {exc}")
            self._set_status("Save failed.")
            return
        messagebox.showinfo("Misc Library", "Catalog saved successfully.")
        self._set_status("Catalog saved.")

    def _collect_payload(self) -> Dict[str, Any]:
        items = self._editor.get_items() if self._editor else []
        categories = []
        if self._catalog:
            categories = list(self._catalog.get("categories", []))
        return {"categories": categories, "items": items}

    def _set_status(self, message: str) -> None:
        self._status_var.set(message)
