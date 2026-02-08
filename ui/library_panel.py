from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.checklist_library_panel import ChecklistLibraryPanel
from ui.measure_library_panel import MeasureLibraryPanel
from ui.misc_library_panel import MiscLibraryPanel


class LibraryPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_checklist_saved=None,
        on_measure_catalog_saved=None,
    ) -> None:
        super().__init__(master)
        self._on_checklist_saved = on_checklist_saved
        self._on_measure_catalog_saved = on_measure_catalog_saved
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew")

        checklist_panel = ChecklistLibraryPanel(
            notebook, on_saved=self._on_checklist_saved
        )
        notebook.add(checklist_panel, text="Checklist Library")

        measure_panel = MeasureLibraryPanel(
            notebook, on_catalog_saved=self._on_measure_catalog_saved
        )
        notebook.add(measure_panel, text="Measure Library")

        misc_panel = MiscLibraryPanel(notebook)
        notebook.add(misc_panel, text="Misc Library")
