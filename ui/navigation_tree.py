import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List

from core.project_store import ProjectSummary


SelectionHandler = Callable[[str], None]


class NavigationTree(ttk.Frame):
    def __init__(self, master: tk.Misc, on_select: SelectionHandler) -> None:
        super().__init__(master)
        self._on_select = on_select
        self._project_nodes: Dict[str, str] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.root_id = self.tree.insert("", "end", text="Projects", open=True)
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)

    def populate(self, summaries: List[ProjectSummary]) -> None:
        self._project_nodes.clear()
        for child in self.tree.get_children(self.root_id):
            self.tree.delete(child)

        for summary in summaries:
            project_id = self.tree.insert(self.root_id, "end", text=summary.name, open=True)
            self._project_nodes[project_id] = summary.path
            for label in ("Inputs", "Measures", "Checklist", "Outputs"):
                child_id = self.tree.insert(project_id, "end", text=label)
                self._project_nodes[child_id] = summary.path

    def _handle_select(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        project_path = self._project_nodes.get(selected[0])
        if project_path:
            self._on_select(project_path)
