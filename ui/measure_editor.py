from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


MEASURE_CATEGORIES = [
    ("bas", "BAS"),
    ("boilers", "Boilers"),
    ("dhw", "DHW"),
    ("lighting", "Lighting"),
    ("ventilation", "Ventilation"),
    ("controls", "Controls"),
    ("envelope", "Envelope"),
    ("other", "Other"),
]


@dataclass
class MeasureFieldConfig:
    key: str
    label: str
    width: int = 16


NUMERIC_FIELDS = [
    MeasureFieldConfig("savings_electric_kwh", "Elec savings (kWh)", 16),
    MeasureFieldConfig("savings_gas_m3", "Gas savings (m³)", 16),
    MeasureFieldConfig("savings_water_m3", "Water savings (m³)", 16),
    MeasureFieldConfig("implementation_cost", "Implementation cost", 16),
    MeasureFieldConfig("incentive", "Incentive", 16),
    MeasureFieldConfig("simple_payback_years", "Simple payback (yrs)", 16),
]


class MeasuresEditor(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._cards: List[_MeasureCard] = []
        self._text_font = tkfont.nametofont("TkTextFont")
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text="Add Measure", command=self.add_measure).pack(
            side="left"
        )

        self._scroll = _ScrollableFrame(self)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)

    def add_measure(self, data: Optional[Dict[str, Any]] = None) -> None:
        card = _MeasureCard(
            self._scroll.content,
            text_font=self._text_font,
            on_move_up=lambda c=card: self._move_card(c, -1),
            on_move_down=lambda c=card: self._move_card(c, 1),
            on_remove=lambda c=card: self._remove_card(c),
        )
        self._cards.append(card)
        card.frame.pack(fill="x", pady=6)
        if data:
            card.set_data(data)
        self._refresh_controls()

    def set_measures(self, measures: List[Dict[str, Any]]) -> None:
        for card in self._cards:
            card.frame.destroy()
        self._cards = []
        for measure in measures:
            self.add_measure(measure)
        if not measures:
            self._refresh_controls()

    def get_measures(self) -> List[Dict[str, Any]]:
        measures = []
        for card in self._cards:
            data = card.get_data()
            if _has_measure_content(data):
                measures.append(data)
        return measures

    def _remove_card(self, card: "_MeasureCard") -> None:
        if card in self._cards:
            self._cards.remove(card)
            card.frame.destroy()
        self._refresh_controls()

    def _move_card(self, card: "_MeasureCard", offset: int) -> None:
        if card not in self._cards:
            return
        index = self._cards.index(card)
        new_index = index + offset
        if new_index < 0 or new_index >= len(self._cards):
            return
        self._cards[index], self._cards[new_index] = self._cards[new_index], self._cards[index]
        self._repack_cards()

    def _repack_cards(self) -> None:
        for card in self._cards:
            card.frame.pack_forget()
        for card in self._cards:
            card.frame.pack(fill="x", pady=6)
        self._refresh_controls()

    def _refresh_controls(self) -> None:
        for idx, card in enumerate(self._cards, start=1):
            card.update_index(idx, total=len(self._cards))


class _MeasureCard:
    def __init__(
        self,
        master: tk.Misc,
        *,
        text_font: tkfont.Font,
        on_move_up,
        on_move_down,
        on_remove,
    ) -> None:
        self._text_font = text_font
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_remove = on_remove
        self.frame = ttk.Labelframe(master, text="Measure")
        self._build_ui()

    def _build_ui(self) -> None:
        self.frame.columnconfigure(1, weight=1)
        header = ttk.Frame(self.frame)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="Title").grid(row=0, column=0, sticky="w")
        self._title_var = tk.StringVar()
        ttk.Entry(header, textvariable=self._title_var).grid(
            row=0, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(header, text="Category").grid(row=0, column=2, sticky="e")
        self._category_var = tk.StringVar()
        combo = ttk.Combobox(
            header,
            textvariable=self._category_var,
            values=[label for _, label in MEASURE_CATEGORIES],
            state="readonly",
            width=16,
        )
        combo.grid(row=0, column=3, sticky="e", padx=(6, 12))

        button_frame = ttk.Frame(header)
        button_frame.grid(row=0, column=4, sticky="e")
        self._up_button = ttk.Button(button_frame, text="Up", command=self._on_move_up)
        self._up_button.grid(row=0, column=0, padx=(0, 4))
        self._down_button = ttk.Button(
            button_frame, text="Down", command=self._on_move_down
        )
        self._down_button.grid(row=0, column=1, padx=(0, 4))
        ttk.Button(button_frame, text="Remove", command=self._on_remove).grid(
            row=0, column=2
        )

        ttk.Label(self.frame, text="Existing Conditions").grid(
            row=1, column=0, sticky="nw", pady=(10, 0)
        )
        self._existing_text = tk.Text(self.frame, height=3, wrap="word", font=self._text_font)
        self._existing_text.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Label(self.frame, text="Retrofit Conditions").grid(
            row=2, column=0, sticky="nw", pady=(10, 0)
        )
        self._retrofit_text = tk.Text(self.frame, height=3, wrap="word", font=self._text_font)
        self._retrofit_text.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        numeric_frame = ttk.LabelFrame(self.frame, text="Key Inputs")
        numeric_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        for col in range(3):
            numeric_frame.columnconfigure(col * 2 + 1, weight=1)

        self._numeric_vars: Dict[str, tk.StringVar] = {}
        for idx, field in enumerate(NUMERIC_FIELDS):
            row = idx // 3
            col = idx % 3
            ttk.Label(numeric_frame, text=field.label).grid(
                row=row, column=col * 2, sticky="w", padx=(6, 4), pady=4
            )
            var = tk.StringVar()
            self._numeric_vars[field.key] = var
            ttk.Entry(numeric_frame, textvariable=var, width=field.width).grid(
                row=row, column=col * 2 + 1, sticky="ew", padx=(0, 8), pady=4
            )

        ttk.Label(self.frame, text="Notes").grid(row=4, column=0, sticky="nw", pady=(10, 0))
        self._notes_text = tk.Text(self.frame, height=3, wrap="word", font=self._text_font)
        self._notes_text.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(10, 0))

    def update_index(self, index: int, total: int) -> None:
        self.frame.configure(text=f"Measure {index}")
        self._up_button.configure(state="normal" if index > 1 else "disabled")
        self._down_button.configure(state="normal" if index < total else "disabled")

    def set_data(self, data: Dict[str, Any]) -> None:
        self._title_var.set(str(data.get("measure_title", "")))
        category_label = _label_for_category(data.get("category"))
        self._category_var.set(category_label)
        _set_text(self._existing_text, data.get("existing_conditions"))
        _set_text(self._retrofit_text, data.get("retrofit_conditions"))
        _set_text(self._notes_text, data.get("notes"))
        for key, var in self._numeric_vars.items():
            value = data.get(key)
            var.set("" if value is None else str(value))

    def get_data(self) -> Dict[str, Any]:
        payload = {
            "measure_title": self._title_var.get().strip(),
            "category": _value_for_category(self._category_var.get()),
            "existing_conditions": _get_text(self._existing_text),
            "retrofit_conditions": _get_text(self._retrofit_text),
            "notes": _get_text(self._notes_text),
        }
        for key, var in self._numeric_vars.items():
            payload[key] = _parse_optional_number(var.get())
        return payload


class _ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.content = ttk.Frame(canvas)

        self._canvas_frame = canvas.create_window((0, 0), window=self.content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.content.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(self._canvas_frame, width=event.width))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c").strip()


def _set_text(widget: tk.Text, value: Any) -> None:
    widget.delete("1.0", tk.END)
    if value is not None and str(value).strip():
        widget.insert("1.0", str(value))


def _parse_optional_number(value: str) -> Optional[float]:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _label_for_category(value: Any) -> str:
    for code, label in MEASURE_CATEGORIES:
        if str(value).strip().lower() == code:
            return label
    if value:
        return str(value)
    return ""


def _value_for_category(label: str) -> str:
    for code, display in MEASURE_CATEGORIES:
        if label == display:
            return code
    return label.strip().lower().replace(" ", "_") if label else ""


def _has_measure_content(data: Dict[str, Any]) -> bool:
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False
