import tkinter as tk
from tkinter import ttk
from typing import Dict, Iterable, List, Optional


class LabeledEntry(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str) -> None:
        super().__init__(master)
        self.var = tk.StringVar()
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(self, textvariable=self.var)
        entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.columnconfigure(1, weight=1)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)


class LabeledCombo(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, options: Iterable[str]) -> None:
        super().__init__(master)
        self.var = tk.StringVar()
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(self, textvariable=self.var, values=list(options), state="readonly")
        combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.columnconfigure(1, weight=1)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)


class LabeledText(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, height: int = 4) -> None:
        super().__init__(master)
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        self.text = tk.Text(self, height=height, wrap="word")
        self.text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def get(self) -> str:
        return self.text.get("1.0", tk.END).strip()

    def set(self, value: str) -> None:
        self.text.delete("1.0", tk.END)
        if value:
            self.text.insert("1.0", value)


class SummaryBox(ttk.LabelFrame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, text="Project Summary", padding=(8, 6))
        self._vars = {
            "building": tk.StringVar(value="-"),
            "address": tk.StringVar(value="-"),
            "measures": tk.StringVar(value="0"),
            "checklists": tk.StringVar(value="0"),
        }
        ttk.Label(self, text="Building:").grid(row=0, column=0, sticky="w")
        ttk.Label(self, textvariable=self._vars["building"]).grid(row=0, column=1, sticky="w")
        ttk.Label(self, text="Address:").grid(row=1, column=0, sticky="w")
        ttk.Label(self, textvariable=self._vars["address"]).grid(row=1, column=1, sticky="w")
        ttk.Label(self, text="Selected measures:").grid(row=2, column=0, sticky="w")
        ttk.Label(self, textvariable=self._vars["measures"]).grid(row=2, column=1, sticky="w")
        ttk.Label(self, text="Checklist items:").grid(row=3, column=0, sticky="w")
        ttk.Label(self, textvariable=self._vars["checklists"]).grid(row=3, column=1, sticky="w")
        self.columnconfigure(1, weight=1)

    def update(
        self,
        building: str,
        address: str,
        measures_count: int,
        checklist_count: int,
    ) -> None:
        self._vars["building"].set(building or "-")
        self._vars["address"].set(address or "-")
        self._vars["measures"].set(str(measures_count))
        self._vars["checklists"].set(str(checklist_count))


class MultiSelectList(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, options: Iterable[str], height: int = 6) -> None:
        super().__init__(master)
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        self.listbox = tk.Listbox(self, selectmode="multiple", height=height)
        for option in options:
            self.listbox.insert(tk.END, option)
        self.listbox.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def get(self) -> List[str]:
        return [self.listbox.get(index) for index in self.listbox.curselection()]

    def set(self, values: Iterable[str]) -> None:
        selections = set(values)
        self.listbox.selection_clear(0, tk.END)
        for index in range(self.listbox.size()):
            if self.listbox.get(index) in selections:
                self.listbox.selection_set(index)


class MeasureMultiSelect(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        measures: Dict[str, dict],
        categories: Iterable[dict],
        order: Iterable[str],
    ) -> None:
        super().__init__(master)
        self._measures = measures
        self._order = list(order)
        self._rows: Dict[str, dict] = {}

        category_titles = {
            item.get("code", ""): item.get("tab_title", "")
            for item in categories
        }
        category_codes = [item.get("code", "") for item in categories]

        grouped: Dict[str, list[str]] = {code: [] for code in category_codes}
        grouped[""] = []
        for measure_id in self._order:
            measure = measures.get(measure_id, {})
            category = measure.get("category", "")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(measure_id)

        row = 0
        for category in category_codes:
            items = grouped.get(category, [])
            if not items:
                continue
            frame = ttk.Labelframe(self, text=category_titles.get(category, category))
            frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
            frame.columnconfigure(1, weight=1)
            row += 1
            for idx, measure_id in enumerate(items):
                measure = measures.get(measure_id, {})
                name = measure.get("title") or measure.get("name") or measure_id
                var = tk.BooleanVar(value=False)
                override_var = tk.StringVar()
                check = ttk.Checkbutton(frame, text=name, variable=var)
                check.grid(row=idx, column=0, sticky="w", padx=(6, 6), pady=2)
                entry = ttk.Entry(frame, textvariable=override_var, state="disabled")
                entry.grid(row=idx, column=1, sticky="ew", padx=(0, 6), pady=2)

                def _toggle_entry(*_args, entry_widget=entry, value=var) -> None:
                    entry_widget.configure(state="normal" if value.get() else "disabled")

                var.trace_add("write", _toggle_entry)
                self._rows[measure_id] = {
                    "selected": var,
                    "override": override_var,
                }

        self.columnconfigure(0, weight=1)

    def get_selected(self) -> List[str]:
        return [
            measure_id
            for measure_id in self._order
            if self._rows.get(measure_id, {}).get("selected", tk.BooleanVar()).get()
        ]

    def get_overrides(self) -> Dict[str, str]:
        overrides: Dict[str, str] = {}
        for measure_id, data in self._rows.items():
            if not data["selected"].get():
                continue
            text = data["override"].get().strip()
            if text:
                overrides[measure_id] = text
        return overrides

    def set_selected(self, values: Iterable[str]) -> None:
        selections = set(values)
        for measure_id, data in self._rows.items():
            data["selected"].set(measure_id in selections)

    def set_overrides(self, overrides: Dict[str, str]) -> None:
        if not overrides:
            return
        for measure_id, text in overrides.items():
            if measure_id in self._rows:
                self._rows[measure_id]["override"].set(text)
