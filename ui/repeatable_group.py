from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import tkinter as tk
from tkinter import ttk


@dataclass
class _RepeatableRow:
    frame: ttk.Frame
    label: ttk.Label
    fields: Dict[str, Dict[str, Any]]


class RepeatableGroupWidget(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        fields: List[Dict[str, Any]],
        *,
        add_label: str = "Add Item",
        row_label: str = "Item",
    ) -> None:
        super().__init__(master)
        self._fields = fields
        self._rows: List[_RepeatableRow] = []
        self._row_label = row_label
        self._required_fields = [
            field.get("id")
            for field in fields
            if field.get("required") and field.get("id")
        ]

        self.columnconfigure(0, weight=1)
        self._rows_container = ttk.Frame(self)
        self._rows_container.grid(row=0, column=0, sticky="ew")
        self._rows_container.columnconfigure(0, weight=1)

        add_button = ttk.Button(self, text=add_label, command=self.add_row)
        add_button.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.add_row()

    def add_row(self, values: Dict[str, Any] | None = None) -> None:
        row_index = len(self._rows)
        row_frame = ttk.Frame(self._rows_container, padding=(6, 6))
        row_frame.grid(row=row_index, column=0, sticky="ew", pady=4)
        row_frame.columnconfigure(1, weight=1)

        header_frame = ttk.Frame(row_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        header_frame.columnconfigure(0, weight=1)
        label = ttk.Label(header_frame, text=f"{self._row_label} {row_index + 1}")
        label.grid(row=0, column=0, sticky="w")
        remove_button = ttk.Button(header_frame, text="Remove")
        remove_button.grid(row=0, column=1, sticky="e")

        fields: Dict[str, Dict[str, Any]] = {}
        row_offset = 1
        for idx, field in enumerate(self._fields):
            field_id = field.get("id")
            field_title = field.get("title") or field_id or f"Field {idx + 1}"
            field_type = field.get("type", "text")
            if not field_id:
                continue

            ttk.Label(row_frame, text=field_title).grid(
                row=row_offset, column=0, sticky="nw", padx=(0, 12), pady=4
            )

            widget_info: Dict[str, Any] = {"type": field_type}
            if field_type == "notes":
                widget = tk.Text(row_frame, height=4, wrap="word")
                widget.grid(row=row_offset, column=1, sticky="ew", pady=4)
                widget_info["widget"] = widget
            elif field_type == "boolean":
                var = tk.BooleanVar(value=field.get("default", True))
                widget = ttk.Checkbutton(row_frame, variable=var)
                widget.grid(row=row_offset, column=1, sticky="w", pady=4)
                widget_info["widget"] = widget
                widget_info["var"] = var
            else:
                var = tk.StringVar()
                widget = ttk.Entry(row_frame, textvariable=var)
                widget.grid(row=row_offset, column=1, sticky="ew", pady=4)
                widget_info["widget"] = widget
                widget_info["var"] = var

            fields[field_id] = widget_info
            row_offset += 1

        row_data = _RepeatableRow(frame=row_frame, label=label, fields=fields)
        remove_button.configure(command=lambda row=row_data: self._remove_row(row))
        self._rows.append(row_data)
        self._populate_row(row_data, values or {})

    def clear_rows(self) -> None:
        for row in self._rows:
            row.frame.destroy()
        self._rows.clear()

    def get_value(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for row in self._rows:
            entry: Dict[str, Any] = {}
            has_content = False
            for field_id, meta in row.fields.items():
                field_type = meta["type"]
                if field_type == "notes":
                    value = meta["widget"].get("1.0", "end-1c").strip()
                elif field_type == "boolean":
                    value = bool(meta["var"].get())
                else:
                    value = meta["var"].get().strip()
                entry[field_id] = value
                if field_id in self._required_fields and isinstance(value, str) and value:
                    has_content = True
                if field_id not in self._required_fields and isinstance(value, str) and value:
                    has_content = True
            if has_content:
                results.append(entry)
        return results

    def set_value(self, values: Any) -> None:
        self.clear_rows()
        if isinstance(values, list) and values:
            for item in values:
                if isinstance(item, dict):
                    self.add_row(item)
                else:
                    self.add_row({})
        else:
            self.add_row()
        self._refresh_row_labels()

    def _populate_row(self, row: _RepeatableRow, values: Dict[str, Any]) -> None:
        for field_id, meta in row.fields.items():
            if field_id not in values:
                continue
            value = values.get(field_id)
            if meta["type"] == "notes":
                meta["widget"].delete("1.0", tk.END)
                if value:
                    meta["widget"].insert("1.0", str(value))
            elif meta["type"] == "boolean":
                meta["var"].set(bool(value) if value is not None else True)
            else:
                meta["var"].set("" if value is None else str(value))

    def _remove_row(self, row: _RepeatableRow) -> None:
        if row not in self._rows:
            return
        self._rows.remove(row)
        row.frame.destroy()
        self._refresh_row_labels()
        if not self._rows:
            self.add_row()

    def _refresh_row_labels(self) -> None:
        for idx, row in enumerate(self._rows):
            row.label.configure(text=f"{self._row_label} {idx + 1}")
