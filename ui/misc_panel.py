from __future__ import annotations

import tkinter as tk

from ui.library_items_panel import LibraryItemsPanel


class MiscPanel(LibraryItemsPanel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            storage_key="misc_items",
            catalog_filename="misc_catalog.json",
            title="Miscellaneous Library",
            item_label="Misc",
        )
