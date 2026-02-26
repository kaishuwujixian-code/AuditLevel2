from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


@dataclass
class MiscCategory:
    code: str
    title: str


class MiscEditor(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        item_label: str = "Misc",
        on_items_changed=None,
    ) -> None:
        super().__init__(master)
        self._item_label = item_label
        self._cards: List[_MiscCard] = []
        self._active_card: Optional[_MiscCard] = None
        self._categories: List[MiscCategory] = []
        self._drag_card: Optional[_MiscCard] = None
        self._drop_target_index: Optional[int] = None
        self._on_items_changed = on_items_changed
        self._text_font = tkfont.nametofont("TkTextFont")
        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(toolbar, text=f"Add {self._item_label} Item", command=self.add_item).pack(side="left")

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

    def set_categories(self, categories: List[Dict[str, Any]]) -> None:
        self._categories = [
            MiscCategory(
                code=str(item.get("code", "")).strip(),
                title=str(item.get("title", "")).strip() or str(item.get("code", "")).strip(),
            )
            for item in categories
            if isinstance(item, dict)
        ]
        for card in self._cards:
            card.set_categories(self._categories)

    def add_item(self, data: Optional[Dict[str, Any]] = None) -> _MiscCard:
        card = _MiscCard(
            self._scroll.content,
            item_label=self._item_label,
            text_font=self._text_font,
            categories=self._categories,
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
        return card

    def set_items(self, items: List[Dict[str, Any]]) -> None:
        self._hide_drop_indicator()
        for card in self._cards:
            card.frame.destroy()
        self._cards = []
        self._active_card = None
        for item in items:
            self.add_item(item)
        if not items:
            self._refresh_controls()
        self._notify_items_changed()

    def get_items(self) -> List[Dict[str, Any]]:
        items = []
        for card in self._cards:
            data = card.get_data()
            if _has_content(data):
                items.append(data)
        return items

    def apply_catalog_item(self, item: Dict[str, Any]) -> None:
        target = self._active_card
        if target is None:
            target = self.add_item()
        target.set_data(
            {
                "misc_id": item.get("id"),
                "title": item.get("title") or "",
                "category": item.get("category") or "",
                "text": item.get("text") or "",
            }
        )
        self._set_active_card(target)
        self._notify_items_changed()

    def selected_catalog_item_ids(self) -> set[str]:
        selected_ids: set[str] = set()
        for card in self._cards:
            if card.misc_id:
                selected_ids.add(card.misc_id)
        return selected_ids

    def _remove_card(self, card: "_MiscCard") -> None:
        if card in self._cards:
            self._cards.remove(card)
            card.frame.destroy()
            if self._active_card is card:
                self._active_card = self._cards[-1] if self._cards else None
        self._refresh_controls()
        self._notify_items_changed()

    def _move_card(self, card: "_MiscCard", offset: int) -> None:
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

    def _set_active_card(self, card: Optional["_MiscCard"]) -> None:
        if card is None or card not in self._cards:
            return
        self._active_card = card
        self._refresh_controls()

    def _start_drag(self, card: "_MiscCard") -> None:
        if card not in self._cards:
            return
        self._drag_card = card
        self._set_active_card(card)

    def _drag_motion(self, card: "_MiscCard", y_root: int) -> None:
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
            self._drop_indicator.pack(in_=self._scroll.content, before=self._cards[0].frame, fill="x", pady=(0, 2))
            return
        if target_index >= len(self._cards):
            self._drop_indicator.pack(in_=self._scroll.content, after=self._cards[-1].frame, fill="x", pady=(2, 0))
            return
        self._drop_indicator.pack(
            in_=self._scroll.content,
            before=self._cards[target_index].frame,
            fill="x",
            pady=2,
        )

    def _hide_drop_indicator(self) -> None:
        self._drop_indicator.pack_forget()

    def _end_drag(self, card: "_MiscCard") -> None:
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

    def _notify_items_changed(self) -> None:
        if callable(self._on_items_changed):
            self._on_items_changed()


class _MiscCard:
    def __init__(
        self,
        master: tk.Misc,
        *,
        item_label: str,
        text_font: tkfont.Font,
        categories: List[MiscCategory],
        on_move_up,
        on_move_down,
        on_remove,
        on_activate,
        on_drag_start,
        on_drag_motion,
        on_drag_end,
    ) -> None:
        self._text_font = text_font
        self._item_label = item_label
        self._categories = categories
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_remove = on_remove
        self._on_activate = on_activate
        self._on_drag_start = on_drag_start
        self._on_drag_motion = on_drag_motion
        self._on_drag_end = on_drag_end
        self._misc_id: Optional[str] = None

        self.frame = tk.LabelFrame(
            master,
            text=f"{self._item_label} Item",
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
            values=[cat.title for cat in self._categories],
            state="readonly",
            width=18,
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

        ttk.Label(self.frame, text="Notes").grid(row=1, column=0, sticky="nw", pady=(10, 0))
        self._text = tk.Text(
            self.frame,
            height=5,
            wrap="word",
            font=self._text_font,
            bg="#ffffff",
            relief="solid",
            bd=1,
        )
        self._text.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(10, 0))

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
    def misc_id(self) -> Optional[str]:
        return self._misc_id

    def set_categories(self, categories: List[MiscCategory]) -> None:
        self._categories = categories
        self._category_combo.configure(values=[cat.title for cat in self._categories])

    def update_index(self, index: int, total: int, *, active: bool, dragging: bool) -> None:
        label = f"{self._item_label} Item {index}"
        if active:
            label = f"▶ {label} [SELECTED]"
        self.frame.configure(text=label)

        if dragging:
            # Tk 没有对单独 frame 的真实 alpha；用浅色+raised 模拟“半透明拖拽态”。
            self.frame.configure(relief="raised", bd=3, bg="#e9eefb")
            self._text.configure(bg="#f8faff")
            self._drag_handle.configure(foreground="#2563eb")
        elif active:
            self.frame.configure(relief="ridge", bd=2, bg="#eef4ff")
            self._text.configure(bg="#ffffff")
            self._drag_handle.configure(foreground="#1d4ed8")
        else:
            self.frame.configure(relief="groove", bd=1, bg="#f6f7fb")
            self._text.configure(bg="#ffffff")
            self._drag_handle.configure(foreground="#4b5563")

        self._up_button.configure(state="normal" if index > 1 else "disabled")
        self._down_button.configure(state="normal" if index < total else "disabled")

    def set_data(self, data: Dict[str, Any]) -> None:
        self._misc_id = _normalize_id(data.get("misc_id"))
        self._title_var.set(str(data.get("title", "")))
        category_label = _label_for_category(data.get("category"), self._categories)
        self._category_var.set(category_label)
        _set_text(self._text, data.get("text"))

    def get_data(self) -> Dict[str, Any]:
        payload = {
            "title": self._title_var.get().strip(),
            "category": _value_for_category(self._category_var.get(), self._categories),
            "text": _get_text(self._text),
        }
        if self._misc_id:
            payload["misc_id"] = self._misc_id
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


def _has_content(data: Dict[str, Any]) -> bool:
    for value in data.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _label_for_category(value: Any, categories: List[MiscCategory]) -> str:
    code = str(value).strip()
    if not code:
        return ""
    for cat in categories:
        if cat.code == code:
            return cat.title
    return code


def _value_for_category(label: str, categories: List[MiscCategory]) -> str:
    for cat in categories:
        if label == cat.title:
            return cat.code
    return label.strip().lower().replace(" ", "_") if label else ""


def _normalize_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
