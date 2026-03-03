from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


ReportHandler = Callable[[], None]


class ReportPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, on_generate: ReportHandler, audit_label: str = "Level 1") -> None:
        super().__init__(master, padding=12)
        self._on_generate = on_generate
        self._audit_label = audit_label
        self._output_var = tk.StringVar(value="No report generated yet.")
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        ttk.Label(
            self,
            text=f"Generate the {self._audit_label} report using the selected project data.",
            wraplength=640,
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(self, text=f"Generate {self._audit_label} Report", command=self._on_generate).grid(
            row=1, column=0, sticky="w", pady=(8, 12)
        )
        ttk.Label(self, text="Latest output:").grid(row=2, column=0, sticky="w")
        ttk.Label(self, textvariable=self._output_var, wraplength=640).grid(
            row=3, column=0, sticky="w"
        )

    def update_output(self, path: Optional[str]) -> None:
        self._output_var.set(path or "No report generated yet.")
