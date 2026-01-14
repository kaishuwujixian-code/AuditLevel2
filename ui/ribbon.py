import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict


RibbonHandler = Callable[[], None]


class Ribbon(ttk.Frame):
    def __init__(self, master: tk.Misc, actions: Dict[str, RibbonHandler]) -> None:
        super().__init__(master, padding=(8, 6))
        self._actions = actions
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)

        self._notebook = ttk.Notebook(self)
        self._notebook.grid(row=0, column=0, sticky="ew")

        self._tabs = {
            "File": self._build_file_tab,
            "Location": self._build_placeholder_tab,
            "Facility": self._build_placeholder_tab,
            "Energy": self._build_placeholder_tab,
            "Cost": self._build_placeholder_tab,
            "Emission": self._build_placeholder_tab,
            "Finance": self._build_placeholder_tab,
            "Risk": self._build_placeholder_tab,
            "Report": self._build_report_tab,
        }

        for name, builder in self._tabs.items():
            frame = ttk.Frame(self._notebook, padding=(6, 6))
            builder(frame, name)
            self._notebook.add(frame, text=name)

    def _add_button(self, parent: ttk.Frame, label: str, action_key: str) -> None:
        handler = self._actions.get(action_key)
        state = "normal" if handler else "disabled"
        button = ttk.Button(parent, text=label, command=handler, state=state)
        button.pack(side="left", padx=(0, 6))

    def _build_file_tab(self, frame: ttk.Frame, _name: str) -> None:
        self._add_button(frame, "📁 Open Projects Folder", "open_projects")
        self._add_button(frame, "📂 Open Output Folder", "open_output")
        self._add_button(frame, "⚙ Settings", "settings")
        self._add_button(frame, "⏻ Exit", "exit")

    def _build_report_tab(self, frame: ttk.Frame, _name: str) -> None:
        self._add_button(frame, "▶ Generate Selected", "generate_selected")
        self._add_button(frame, "⏩ Generate All", "generate_all")
        self._add_button(frame, "✅ Validate", "validate")
        self._add_button(frame, "💾 Save", "save")
        self._add_button(frame, "📤 Export", "export")

    def _build_placeholder_tab(self, frame: ttk.Frame, name: str) -> None:
        placeholder = ttk.Label(frame, text=f"{name} tools coming soon")
        placeholder.pack(side="left")
