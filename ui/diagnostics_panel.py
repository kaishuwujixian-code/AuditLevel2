from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class DiagnosticsPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text="Diagnostics output").grid(row=0, column=0, sticky="w")
        self._text = tk.Text(self, height=14, wrap="word")
        self._text.grid(row=1, column=0, sticky="nsew")

    def set_output(self, content: str) -> None:
        self._text.delete("1.0", tk.END)
        if content:
            self._text.insert("1.0", content)
