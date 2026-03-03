from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


DEFAULT_MEASURE_CATEGORIES = [
    ("bas", "BAS / Controls"),
    ("boiler", "Boiler / Plant"),
    ("boilers", "Boilers"),
    ("dhw", "DHW"),
    ("lighting", "Lighting"),
    ("ventilation", "Ventilation"),
    ("mua", "MUA / Ventilation"),
    ("controls", "Controls"),
    ("loop", "Hydronic Loops"),
    ("water", "Water & DHW"),
    ("pumps", "Pumps / Power / PF"),
    ("envelope", "Building Envelope"),
    ("other", "Other / Misc"),
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
    def __init__(
        self,
        master: tk.Misc,
        *,
        categories: Optional[List[dict]] = None,
        on_items_changed=None,
    ) -> None:
        super().__init__(master)
        self._cards: List[_MeasureCard] = []
        self._active_card: Optional[_MeasureCard] = None
        self._drag_card: Optional[_MeasureCard] = None
        self._drop_target_index: Optional[int] = None
        self._text_font = tkfont.nametofont("TkTextFont")
        self._category_options = _normalize_category_options(categories)
        self._on_items_changed = on_items_changed
        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text="Add Measure", command=self.add_measure).pack(side="left")

        self._scroll = _ScrollableFrame(self)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)

        self._drop_indicator = tk.Frame(
            self._scroll.content,
            height=3,
            bg="#2563eb",
            bd=0,
            highlightthickness=0,
        )

    def _bind_shortcuts(self) -> None:
        self.bind_all("<Alt-Up>", lambda event: self._on_shortcut_move(event, -1), add=True)
        self.bind_all("<Alt-Down>", lambda event: self._on_shortcut_move(event, 1), add=True)
        self.bind_all(
            "<Control-Shift-Up>", lambda event: self._on_shortcut_move(event, -1), add=True
        )
        self.bind_all(
            "<Control-Shift-Down>", lambda event: self._on_shortcut_move(event, 1), add=True
        )

    def _on_shortcut_move(self, event: tk.Event, offset: int) -> str | None:
        focus = self.focus_get()
        if not isinstance(focus, tk.Misc) or not _is_descendant(focus, self):
            return None
        if not self._active_card:
            return "break"
        self._move_card(self._active_card, offset)
        return "break"

    def add_measure(self, data: Optional[Dict[str, Any]] = None) -> _MeasureCard:
        card = _MeasureCard(
            self._scroll.content,
            text_font=self._text_font,
            category_options=self._category_options,
            on_move_up=lambda: self._move_card(card, -1),
            on_move_down=lambda: self._move_card(card, 1),
            on_remove=lambda: self._remove_card(card),
            on_activate=lambda: self._set_active_card(card),
            on_drag_start=lambda: self._start_drag(card),
            on_drag_motion=lambda y_root: self._drag_motion(card, y_root),
            on_drag_end=lambda: self._end_drag(card),
        )
        self._cards.append(card)
        card.frame.pack(fill="x", pady=6)
        if data:
            card.set_data(data)
        self._set_active_card(card)
        self._refresh_controls()
        self._notify_items_changed()
        return card

    def set_measures(self, measures: List[Dict[str, Any]]) -> None:
        self._hide_drop_indicator()
        for card in self._cards:
            card.frame.destroy()
        self._cards = []
        self._active_card = None
        self._drag_card = None
        self._drop_target_index = None
        for measure in measures:
            self.add_measure(measure)
        if not measures:
            self._refresh_controls()
        self._notify_items_changed()

    def get_measures(self) -> List[Dict[str, Any]]:
        measures = []
        for card in self._cards:
            data = card.get_data()
            if _has_measure_content(data):
                measures.append(data)
        return measures

    def selected_catalog_measure_ids(self) -> set[str]:
        selected_ids: set[str] = set()
        for card in self._cards:
            if card.measure_id:
                selected_ids.add(card.measure_id)
        return selected_ids

    def _remove_card(self, card: "_MeasureCard") -> None:
        if card in self._cards:
            self._cards.remove(card)
            card.frame.destroy()
            if self._active_card is card:
                self._active_card = self._cards[-1] if self._cards else None
        self._refresh_controls()
        self._notify_items_changed()

    def _move_card(self, card: "_MeasureCard", offset: int) -> None:
        if card not in self._cards:
            return
        index = self._cards.index(card)
        new_index = index + offset
        if new_index < 0 or new_index >= len(self._cards):
            return
        self._cards[index], self._cards[new_index] = self._cards[new_index], self._cards[index]
        self._repack_cards()
        self._notify_items_changed()

    def _repack_cards(self) -> None:
        self._hide_drop_indicator()
        for card in self._cards:
            card.frame.pack_forget()
        for card in self._cards:
            card.frame.pack(fill="x", pady=6)
        self._refresh_controls()

    def _refresh_controls(self) -> None:
        for idx, card in enumerate(self._cards, start=1):
            card.update_index(
                idx,
                total=len(self._cards),
                active=card is self._active_card,
                dragging=card is self._drag_card,
            )

    def _set_active_card(self, card: Optional["_MeasureCard"]) -> None:
        if card is None or card not in self._cards:
            return
        self._active_card = card
        self._refresh_controls()

    def _start_drag(self, card: "_MeasureCard") -> None:
        if card not in self._cards:
            return
        self._drag_card = card
        self._set_active_card(card)

    def _drag_motion(self, card: "_MeasureCard", y_root: int) -> None:
        if self._drag_card is not card or card not in self._cards:
            return
        self._set_drop_target_from_pointer(y_root)

    def _set_drop_target_from_pointer(self, y_root: int) -> None:
        if not self._cards:
            self._hide_drop_indicator()
            return

        target_index = len(self._cards)
        for index, candidate in enumerate(self._cards):
            top = candidate.frame.winfo_rooty()
            center = top + candidate.frame.winfo_height() // 2
            if y_root < center:
                target_index = index
                break

        self._drop_target_index = target_index
        self._show_drop_indicator(target_index)

    def _show_drop_indicator(self, target_index: int) -> None:
        self._drop_indicator.pack_forget()
        if not self._cards:
            return

        if target_index <= 0:
            self._drop_indicator.pack(
                in_=self._scroll.content,
                before=self._cards[0].frame,
                fill="x",
                pady=(0, 2),
            )
            return
        if target_index >= len(self._cards):
            self._drop_indicator.pack(
                in_=self._scroll.content,
                after=self._cards[-1].frame,
                fill="x",
                pady=(2, 0),
            )
            return
        self._drop_indicator.pack(
            in_=self._scroll.content,
            before=self._cards[target_index].frame,
            fill="x",
            pady=2,
        )

    def _hide_drop_indicator(self) -> None:
        self._drop_indicator.pack_forget()

    def _end_drag(self, card: "_MeasureCard") -> None:
        if self._drag_card is not card:
            return

        if self._drop_target_index is not None and card in self._cards:
            current_index = self._cards.index(card)
            target_index = self._drop_target_index
            if target_index > current_index:
                target_index -= 1
            target_index = max(0, min(target_index, len(self._cards) - 1))
            if target_index != current_index:
                self._cards.pop(current_index)
                self._cards.insert(target_index, card)

        self._drag_card = None
        self._drop_target_index = None
        self._repack_cards()
        self._notify_items_changed()

    def apply_catalog_measure(self, measure: Dict[str, Any]) -> None:
        target = self._active_card
        if target is None:
            target = self.add_measure()
        target.set_data(
            {
                "measure_id": measure.get("id"),
                "measure_title": measure.get("title") or measure.get("name") or "",
                "category": measure.get("category") or "",
                "existing_conditions": measure.get("existing") or "",
                "retrofit_conditions": measure.get("retrofit") or "",
                "notes": measure.get("summary") or "",
            }
        )
        self._set_active_card(target)
        self._notify_items_changed()

    def set_categories(self, categories: List[dict]) -> None:
        self._category_options = _normalize_category_options(categories)
        for card in self._cards:
            card.set_categories(self._category_options)

    def _notify_items_changed(self) -> None:
        if callable(self._on_items_changed):
            self._on_items_changed()


class _MeasureCard:
    def __init__(
        self,
        master: tk.Misc,
        *,
        text_font: tkfont.Font,
        category_options: List[tuple[str, str]],
        on_move_up,
        on_move_down,
        on_remove,
        on_activate,
        on_drag_start,
        on_drag_motion,
        on_drag_end,
    ) -> None:
        self._text_font = text_font
        self._category_options = category_options
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_remove = on_remove
        self._on_activate = on_activate
        self._on_drag_start = on_drag_start
        self._on_drag_motion = on_drag_motion
        self._on_drag_end = on_drag_end
        self._measure_id: Optional[str] = None

        self.frame = tk.LabelFrame(
            master,
            text="Measure",
            bd=1,
            relief="groove",
            padx=6,
            pady=6,
            bg="#f6f7fb",
        )
        self._build_ui()
        self._bind_activate()

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
        self._category_combo = ttk.Combobox(
            header,
            textvariable=self._category_var,
            values=[label for _, label in self._category_options],
            state="readonly",
            width=16,
        )
        self._category_combo.grid(row=0, column=3, sticky="e", padx=(6, 12))

        button_frame = ttk.Frame(header)
        button_frame.grid(row=0, column=4, sticky="e")
        self._drag_handle = ttk.Label(button_frame, text="☰ Drag", cursor="fleur")
        self._drag_handle.grid(row=0, column=0, padx=(0, 8))
        self._up_button = ttk.Button(button_frame, text="Up", command=self._on_move_up)
        self._up_button.grid(row=0, column=1, padx=(0, 4))
        self._down_button = ttk.Button(button_frame, text="Down", command=self._on_move_down)
        self._down_button.grid(row=0, column=2, padx=(0, 4))
        ttk.Button(button_frame, text="Remove", command=self._on_remove).grid(row=0, column=3)

        ttk.Label(self.frame, text="Existing Conditions").grid(
            row=1, column=0, sticky="nw", pady=(10, 0)
        )
        self._existing_text = tk.Text(
            self.frame,
            height=3,
            wrap="word",
            font=self._text_font,
            bg="#ffffff",
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            spacing1=2,
            spacing3=2,
            undo=True,
        )
        self._existing_text.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Label(self.frame, text="Retrofit Conditions").grid(
            row=2, column=0, sticky="nw", pady=(10, 0)
        )
        self._retrofit_text = tk.Text(
            self.frame,
            height=3,
            wrap="word",
            font=self._text_font,
            bg="#ffffff",
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            spacing1=2,
            spacing3=2,
            undo=True,
        )
        self._retrofit_text.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        self._numeric_vars: Dict[str, tk.StringVar] = {}

        ttk.Label(self.frame, text="Notes").grid(row=3, column=0, sticky="nw", pady=(10, 0))
        self._notes_text = tk.Text(
            self.frame,
            height=3,
            wrap="word",
            font=self._text_font,
            bg="#ffffff",
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            spacing1=2,
            spacing3=2,
            undo=True,
        )
        self._notes_text.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(10, 0))

    def _bind_activate(self) -> None:
        def bind_recursive(widget: tk.Misc) -> None:
            widget.bind("<Button-1>", lambda _event: self._on_activate(), add=True)
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(self.frame)
        self._drag_handle.bind("<ButtonPress-1>", self._on_drag_start_event, add=True)
        self._drag_handle.bind("<B1-Motion>", self._on_drag_motion_event, add=True)
        self._drag_handle.bind("<ButtonRelease-1>", self._on_drag_end_event, add=True)

    def _on_drag_start_event(self, _event: tk.Event) -> None:
        self._on_drag_start()

    def _on_drag_motion_event(self, event: tk.Event) -> None:
        self._on_drag_motion(event.y_root)

    def _on_drag_end_event(self, _event: tk.Event) -> None:
        self._on_drag_end()

    @property
    def measure_id(self) -> Optional[str]:
        return self._measure_id

    def update_index(self, index: int, total: int, *, active: bool, dragging: bool) -> None:
        label = f"Measure {index}"
        if active:
            label = f"▶ {label} [SELECTED]"
        self.frame.configure(text=label)

        if dragging:
            self.frame.configure(relief="raised", bd=3, bg="#e9eefb")
            self._existing_text.configure(bg="#f8faff")
            self._retrofit_text.configure(bg="#f8faff")
            self._notes_text.configure(bg="#f8faff")
            self._drag_handle.configure(foreground="#2563eb")
        elif active:
            self.frame.configure(relief="ridge", bd=2, bg="#eef4ff")
            self._existing_text.configure(bg="#ffffff")
            self._retrofit_text.configure(bg="#ffffff")
            self._notes_text.configure(bg="#ffffff")
            self._drag_handle.configure(foreground="#1d4ed8")
        else:
            self.frame.configure(relief="groove", bd=1, bg="#f6f7fb")
            self._existing_text.configure(bg="#ffffff")
            self._retrofit_text.configure(bg="#ffffff")
            self._notes_text.configure(bg="#ffffff")
            self._drag_handle.configure(foreground="#4b5563")

        self._up_button.configure(state="normal" if index > 1 else "disabled")
        self._down_button.configure(state="normal" if index < total else "disabled")

    def set_data(self, data: Dict[str, Any]) -> None:
        self._measure_id = _normalize_measure_id(data.get("measure_id"))
        self._title_var.set(str(data.get("measure_title", "")))
        category_label = _label_for_category(data.get("category"), self._category_options)
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
            "category": _value_for_category(self._category_var.get(), self._category_options),
            "existing_conditions": _get_text(self._existing_text),
            "retrofit_conditions": _get_text(self._retrofit_text),
            "notes": _get_text(self._notes_text),
        }
        if self._measure_id:
            payload["measure_id"] = self._measure_id
        for key, var in self._numeric_vars.items():
            payload[key] = _parse_optional_number(var.get())
        return payload

    def set_categories(self, options: List[tuple[str, str]]) -> None:
        self._category_options = options
        values = [label for _, label in options]
        self._category_combo.configure(values=values)
        current_label = self._category_var.get()
        if current_label and current_label not in values:
            code = _value_for_category(current_label, options)
            self._category_var.set(_label_for_category(code, options))


class _ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.content = ttk.Frame(self._canvas)

        self._canvas_frame = self._canvas.create_window((0, 0), window=self.content, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.content.bind(
            "<Configure>",
            lambda event: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind(
            "<Configure>",
            lambda event: self._canvas.itemconfigure(self._canvas_frame, width=event.width),
        )

        # 在整个右侧编辑区实现“悬停即滚动”的丝滑滚轮行为（含拖拽时）。
        self.bind_all("<MouseWheel>", self._on_mousewheel, add=True)
        self.bind_all("<Button-4>", self._on_mousewheel, add=True)
        self.bind_all("<Button-5>", self._on_mousewheel, add=True)

    def _on_mousewheel(self, event: tk.Event) -> str | None:
        widget = self.winfo_containing(event.x_root, event.y_root)
        if not isinstance(widget, tk.Misc) or not _is_descendant(widget, self):
            return None
        units = _mousewheel_units(event)
        if units == 0:
            return "break"
        self._canvas.yview_scroll(units, "units")
        return "break"


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


def _label_for_category(value: Any, options: List[tuple[str, str]]) -> str:
    for code, label in options:
        if str(value).strip().lower() == code:
            return label
    if value:
        return str(value)
    return ""


def _value_for_category(label: str, options: List[tuple[str, str]]) -> str:
    for code, display in options:
        if label == display:
            return code
    return label.strip().lower().replace(" ", "_") if label else ""


def _normalize_measure_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _has_measure_content(data: Dict[str, Any]) -> bool:
    for value in data.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _normalize_category_options(
    categories: Optional[List[dict]],
) -> List[tuple[str, str]]:
    options: List[tuple[str, str]] = []
    if categories:
        for entry in categories:
            if not isinstance(entry, dict):
                continue
            code = str(entry.get("code", "")).strip().lower()
            label = str(entry.get("tab_title", "")).strip() or code
            if not code:
                continue
            options.append((code, label))
    if not options:
        options = [(code, label) for code, label in DEFAULT_MEASURE_CATEGORIES]
    return options


def _is_descendant(widget: tk.Misc, ancestor: tk.Misc) -> bool:
    current = widget
    while current is not None:
        if current is ancestor:
            return True
        parent_name = current.winfo_parent()
        if not parent_name:
            break
        current = current.nametowidget(parent_name)
    return False


def _mousewheel_units(event: tk.Event) -> int:
    num = getattr(event, "num", None)
    if num == 4:
        return -1
    if num == 5:
        return 1
    delta = int(getattr(event, "delta", 0) or 0)
    if delta == 0:
        return 0
    steps = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
    if steps > 2:
        return 2
    if steps < -2:
        return -2
    return steps
