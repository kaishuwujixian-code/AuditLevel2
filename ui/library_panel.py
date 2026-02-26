from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.checklist_library_panel import ChecklistLibraryPanel
from ui.measure_library_panel import MeasureLibraryPanel
from ui.misc_library_panel import MiscLibraryPanel
from ui.ruleset_library_panel import RulesetLibraryPanel
from ui.system_library_panel import SystemLibraryPanel


class LibraryPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_checklist_saved=None,
        on_measure_catalog_saved=None,
        on_system_catalog_changed=None,
    ) -> None:
        super().__init__(master)
        self._on_checklist_saved = on_checklist_saved
        self._on_measure_catalog_saved = on_measure_catalog_saved
        self._on_system_catalog_changed = on_system_catalog_changed
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

        heating_library_panel = SystemLibraryPanel(
            notebook,
            catalog_filename="heating_catalog.json",
            panel_title="Heating Library",
            state_key="heating_library",
            on_catalog_changed=self._on_system_catalog_changed,
        )
        notebook.add(heating_library_panel, text="Heating Library")

        cooling_library_panel = SystemLibraryPanel(
            notebook,
            catalog_filename="cooling_catalog.json",
            panel_title="Cooling Library",
            state_key="cooling_library",
            on_catalog_changed=self._on_system_catalog_changed,
        )
        notebook.add(cooling_library_panel, text="Cooling Library")

        dhw_library_panel = SystemLibraryPanel(
            notebook,
            catalog_filename="dhw_catalog.json",
            panel_title="DHW Library",
            state_key="dhw_library",
            on_catalog_changed=self._on_system_catalog_changed,
        )
        notebook.add(dhw_library_panel, text="DHW Library")

        ventilation_library_panel = SystemLibraryPanel(
            notebook,
            catalog_filename="ventilation_catalog.json",
            panel_title="Ventilation Library",
            state_key="ventilation_library",
            on_catalog_changed=self._on_system_catalog_changed,
        )
        notebook.add(ventilation_library_panel, text="Ventilation Library")

        ruleset_panel = RulesetLibraryPanel(notebook)
        notebook.add(ruleset_panel, text="Ruleset Library")
