from __future__ import annotations

from typing import Any, Dict, Optional

import tkinter as tk
from tkinter import ttk

from core.template_store import TemplateData


class MeasuresPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, template: TemplateData) -> None:
        super().__init__(master)
        self._template = template
        self._measure_vars: Dict[str, tk.BooleanVar] = {
            measure_id: tk.BooleanVar(value=False)
            for measure_id in template.measure_order
        }
        self._override_texts: Dict[str, str] = {}
        self._current_measure: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=0, column=0, sticky="nsew")

        category_frame = ttk.Frame(paned, padding=(8, 8))
        category_frame.columnconfigure(0, weight=1)
        category_frame.rowconfigure(1, weight=1)
        ttk.Label(category_frame, text="Categories", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self._category_list = tk.Listbox(category_frame, height=12)
        self._category_list.grid(row=1, column=0, sticky="nsew")
        category_scroll = ttk.Scrollbar(
            category_frame, orient="vertical", command=self._category_list.yview
        )
        self._category_list.configure(yscrollcommand=category_scroll.set)
        category_scroll.grid(row=1, column=1, sticky="ns")
        self._category_list.bind("<<ListboxSelect>>", self._on_category_select)
        paned.add(category_frame, weight=1)

        measures_frame = ttk.Frame(paned, padding=(8, 8))
        measures_frame.columnconfigure(0, weight=1)
        measures_frame.rowconfigure(1, weight=1)
        ttk.Label(measures_frame, text="Measures", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self._measures_scroll = _ScrollableFrame(measures_frame)
        self._measures_scroll.grid(row=1, column=0, sticky="nsew")
        paned.add(measures_frame, weight=2)

        preview_frame = ttk.Frame(paned, padding=(8, 8))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        ttk.Label(preview_frame, text="Preview", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self._preview_text = tk.Text(preview_frame, height=12, wrap="word")
        self._preview_text.grid(row=1, column=0, sticky="nsew")
        self._preview_text.configure(state="disabled")
        ttk.Label(preview_frame, text="Override narrative").grid(
            row=2, column=0, sticky="w", pady=(8, 4)
        )
        self._override_text = tk.Text(preview_frame, height=6, wrap="word")
        self._override_text.grid(row=3, column=0, sticky="nsew")
        self._override_text.bind("<FocusOut>", lambda _event: self._store_current_override())
        preview_frame.rowconfigure(3, weight=1)
        paned.add(preview_frame, weight=2)

        self._populate_categories()

    def _populate_categories(self) -> None:
        self._category_list.delete(0, tk.END)
        for category in self._template.ui_categories:
            title = category.get("tab_title", "")
            code = category.get("code", "")
            label = f"{title}" if title else code
            self._category_list.insert(tk.END, label)
        if self._category_list.size() > 0:
            self._category_list.selection_set(0)
            self._on_category_select(None)

    def _on_category_select(self, _event: Any) -> None:
        selection = self._category_list.curselection()
        if not selection:
            return
        index = selection[0]
        category = self._template.ui_categories[index]
        category_code = category.get("code", "")
        self._build_measures_list(category_code)

    def _build_measures_list(self, category_code: str) -> None:
        self._store_current_override()
        container = self._measures_scroll.content
        for child in container.winfo_children():
            child.destroy()

        measures = self._measures_for_category(category_code)
        if not measures:
            ttk.Label(container, text="No measures in this category.").pack(anchor="w")
            return

        for measure_id in measures:
            measure = self._template.measures.get(measure_id, {})
            name = measure.get("title") or measure.get("name") or measure_id
            var = self._measure_vars[measure_id]
            row = ttk.Frame(container)
            row.pack(fill="x", pady=2)
            check = ttk.Checkbutton(
                row,
                text=name,
                variable=var,
                command=lambda mid=measure_id: self._select_measure(mid),
            )
            check.pack(anchor="w")

    def _measures_for_category(self, category_code: str) -> list[str]:
        measures = []
        for measure_id in self._template.measure_order:
            measure = self._template.measures.get(measure_id, {})
            category = measure.get("category") or self._template.category_overrides.get(measure_id, "")
            if category == category_code:
                measures.append(measure_id)
        return measures

    def _select_measure(self, measure_id: str) -> None:
        if self._current_measure == measure_id:
            self._update_preview(measure_id)
            return
        self._store_current_override()
        self._current_measure = measure_id
        self._update_preview(measure_id)
        override_text = self._override_texts.get(measure_id, "")
        self._override_text.delete("1.0", tk.END)
        if override_text:
            self._override_text.insert("1.0", override_text)

    def _update_preview(self, measure_id: str) -> None:
        measure = self._template.measures.get(measure_id, {})
        parts = [
            measure.get("title") or measure.get("name") or measure_id,
            "",
        ]
        summary = measure.get("summary")
        if summary:
            parts.extend(["Summary:", summary, ""])
        existing = measure.get("existing")
        if existing:
            parts.extend(["Existing:", existing, ""])
        retrofit = measure.get("retrofit")
        if retrofit:
            parts.extend(["Retrofit:", retrofit, ""])

        self._preview_text.configure(state="normal")
        self._preview_text.delete("1.0", tk.END)
        self._preview_text.insert("1.0", "\n".join(part for part in parts if part is not None).strip())
        self._preview_text.configure(state="disabled")

    def _store_current_override(self) -> None:
        if not self._current_measure:
            return
        text = self._override_text.get("1.0", "end-1c").strip()
        if text:
            self._override_texts[self._current_measure] = text
        elif self._current_measure in self._override_texts:
            self._override_texts.pop(self._current_measure, None)

    def load_project(self, project_data: Dict[str, Any]) -> None:
        selected = project_data.get("selected_measures", [])
        if not isinstance(selected, list):
            selected = []
        normalized = self._normalize_selected(selected)
        project_data["selected_measures"] = normalized

        overrides = project_data.get("measure_overrides", {})
        if not isinstance(overrides, dict):
            overrides = {}
        normalized_overrides: Dict[str, str] = {}
        for key, value in overrides.items():
            measure_id = self._template.legacy_key_map.get(key, key)
            normalized_overrides[measure_id] = _extract_override_text(value)
        self._override_texts = normalized_overrides

        for measure_id, var in self._measure_vars.items():
            var.set(measure_id in normalized)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        self._store_current_override()
        selected = [
            measure_id
            for measure_id in self._template.measure_order
            if self._measure_vars[measure_id].get()
        ]
        project_data["selected_measures"] = selected
        overrides = {
            measure_id: text
            for measure_id, text in self._override_texts.items()
            if text and measure_id in selected
        }
        project_data["measure_overrides"] = overrides

    def _normalize_selected(self, selected: list[str]) -> list[str]:
        mapped = []
        for item in selected:
            if item in self._template.measures:
                mapped.append(item)
            else:
                mapped.append(self._template.legacy_key_map.get(item, item))
        return mapped


class _ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.content = ttk.Frame(self._canvas)

        self._canvas_frame = self._canvas.create_window((0, 0), window=self.content, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        self.content.bind(
            "<Configure>",
            lambda event: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfigure(self._canvas_frame, width=event.width)


def _extract_override_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("narrative", "notes", "justification", "title"):
            entry = value.get(key)
            if isinstance(entry, str) and entry.strip():
                return entry.strip()
        return ""
    if isinstance(value, str):
        return value.strip()
    return ""
