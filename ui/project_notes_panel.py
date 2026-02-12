from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional

from ui.ui_state import load_ui_state, save_ui_state

_DEFAULT_QUARTERLY_GUIDANCE = (
    "每个 project 都建议 EV Charging Stations、Window Lifecycle Planning、"
    "Lighting Motion Sensor Control Retrofit 以及 ERV for MUA units。"
    "对于楼顶空间充足的大楼，可以额外建议 Solar PV system。"
)


class ProjectNotesPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._project_note_text: Optional[tk.Text] = None
        self._guidance_var = tk.StringVar(value=self._load_guidance())
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Project Notes").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        ttk.Label(self, text="季度主推建议（固定内容）").grid(
            row=0, column=1, sticky="w", padx=8, pady=(8, 4)
        )

        left_frame = ttk.Frame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        self._project_note_text = tk.Text(left_frame, wrap="word", height=20, undo=True)
        self._project_note_text.grid(row=0, column=0, sticky="nsew")
        left_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self._project_note_text.yview)
        self._project_note_text.configure(yscrollcommand=left_scroll.set)
        left_scroll.grid(row=0, column=1, sticky="ns")

        right_frame = ttk.Frame(self)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        guidance_box = ttk.Label(
            right_frame,
            textvariable=self._guidance_var,
            justify="left",
            wraplength=420,
            anchor="nw",
            relief="solid",
            padding=(10, 10),
        )
        guidance_box.grid(row=0, column=0, sticky="nsew")

        ttk.Button(right_frame, text="编辑", command=self._edit_guidance).grid(
            row=1, column=0, sticky="e", pady=(8, 0)
        )

    def load_project(self, project_data: Dict[str, Any]) -> None:
        note = str(project_data.get("project_notes", "") or "")
        self._set_text(note)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        project_data["project_notes"] = self._get_text().strip()

    def _set_text(self, value: str) -> None:
        if self._project_note_text is None:
            return
        self._project_note_text.delete("1.0", tk.END)
        if value:
            self._project_note_text.insert("1.0", value)

    def _get_text(self) -> str:
        if self._project_note_text is None:
            return ""
        return self._project_note_text.get("1.0", "end-1c")

    def _load_guidance(self) -> str:
        state = load_ui_state("project_notes")
        value = state.get("global_guidance")
        if isinstance(value, str) and value.strip():
            return value
        return _DEFAULT_QUARTERLY_GUIDANCE

    def _save_guidance(self, value: str) -> None:
        save_ui_state("project_notes", {"global_guidance": value})

    def _edit_guidance(self) -> None:
        updated = self._show_guidance_editor(self._guidance_var.get())
        if updated is None:
            return
        cleaned = updated.strip() or _DEFAULT_QUARTERLY_GUIDANCE
        self._guidance_var.set(cleaned)
        self._save_guidance(cleaned)

    def _show_guidance_editor(self, initial_value: str) -> Optional[str]:
        dialog = tk.Toplevel(self)
        dialog.title("编辑固定建议")
        dialog.transient(self.winfo_toplevel())
        dialog.geometry("760x460")
        dialog.minsize(620, 360)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)

        ttk.Label(dialog, text="编辑右侧固定内容（跨项目共享）：").grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 6)
        )

        text_wrap = ttk.Frame(dialog)
        text_wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        text_wrap.columnconfigure(0, weight=1)
        text_wrap.rowconfigure(0, weight=1)

        text = tk.Text(text_wrap, wrap="word", undo=True)
        text.grid(row=0, column=0, sticky="nsew")
        text.insert("1.0", initial_value)
        yscroll = ttk.Scrollbar(text_wrap, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=yscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")

        result: Dict[str, Optional[str]] = {"value": None}

        def _save() -> None:
            result["value"] = text.get("1.0", "end-1c")
            dialog.destroy()

        def _cancel() -> None:
            dialog.destroy()

        button_row = ttk.Frame(dialog)
        button_row.grid(row=2, column=0, sticky="e", padx=12, pady=(0, 12))
        ttk.Button(button_row, text="取消", command=_cancel).pack(side="right")
        ttk.Button(button_row, text="保存", command=_save).pack(side="right", padx=(0, 8))

        dialog.bind("<Escape>", lambda _e: _cancel())
        dialog.bind("<Control-Return>", lambda _e: _save())

        text.focus_set()
        dialog.grab_set()
        dialog.wait_window()
        return result["value"]
