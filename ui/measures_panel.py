from __future__ import annotations

from typing import Any, Dict

import tkinter as tk
from tkinter import ttk

from core.project_store import normalize_measures_data
from ui.measure_editor import MeasuresEditor


class MeasuresPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._editor = MeasuresEditor(self)
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._editor.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def load_project(self, project_data: Dict[str, Any]) -> None:
        normalize_measures_data(project_data)
        measures = _extract_measures(project_data)
        self._editor.set_measures(measures)

    def update_project(self, project_data: Dict[str, Any]) -> None:
        measures = self._editor.get_measures()
        project_data["measures"] = measures
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            answers = {}
        answers["measures"] = measures
        project_data["answers"] = answers


def _extract_measures(project_data: Dict[str, Any]) -> list[Dict[str, Any]]:
    measures = project_data.get("measures")
    if isinstance(measures, list):
        return [item for item in measures if isinstance(item, dict)]
    answers = project_data.get("answers", {})
    if isinstance(answers, dict):
        measures = answers.get("measures")
        if isinstance(measures, list):
            return [item for item in measures if isinstance(item, dict)]
    return []
