from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

import os
import tkinter as tk
from tkinter import ttk

from core.project_store import scan_project_summaries


@dataclass(frozen=True)
class DashboardEntry:
    name: str
    path: str
    folder: str


class ProjectDashboardPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        projects_dir: str,
        on_open: Callable[[str], None],
        on_new: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._projects_dir = projects_dir
        self._on_open = on_open
        self._on_new = on_new
        self._entries: List[DashboardEntry] = []
        self._filtered_entries: List[DashboardEntry] = []
        self._build_ui()
        self.refresh_projects()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(10, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Project Dashboard", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        controls = ttk.Frame(header)
        controls.grid(row=1, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)

        search_frame = ttk.Frame(controls)
        search_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        search_frame.columnconfigure(0, weight=1)
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self._search_var)
        search_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(search_frame, text="Clear", command=self._clear_search).grid(
            row=0, column=1, padx=(6, 0)
        )
        self._search_var.trace_add("write", lambda *_args: self._apply_filter())

        actions = ttk.Frame(controls)
        actions.grid(row=0, column=1, sticky="e")
        ttk.Button(actions, text="New Project", command=self._on_new).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(actions, text="Open Selected", command=self._open_selected).grid(
            row=0, column=1, padx=(0, 6)
        )
        ttk.Button(actions, text="Refresh", command=self.refresh_projects).grid(
            row=0, column=2
        )

        list_frame = ttk.Frame(self, padding=(10, 4))
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            list_frame,
            columns=("name", "folder"),
            show="headings",
            height=12,
        )
        self._tree.heading("name", text="Project")
        self._tree.heading("folder", text="Folder")
        self._tree.column("name", width=280, anchor="w")
        self._tree.column("folder", width=420, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<Double-1>", lambda _event: self._open_selected())

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        self._status_var = tk.StringVar(value="")
        status = ttk.Label(self, textvariable=self._status_var, padding=(10, 4))
        status.grid(row=2, column=0, sticky="ew")

    def refresh_projects(self) -> None:
        os.makedirs(self._projects_dir, exist_ok=True)
        summaries, errors = scan_project_summaries(self._projects_dir)
        self._entries = [
            DashboardEntry(name=summary.name, path=summary.path, folder=summary.folder)
            for summary in summaries
        ]
        self._apply_filter()
        if errors:
            self._status_var.set(f"Loaded with {len(errors)} error(s).")
        else:
            self._status_var.set(f"{len(self._entries)} project(s) found.")

    def _clear_search(self) -> None:
        self._search_var.set("")

    def _apply_filter(self) -> None:
        term = self._search_var.get().strip().lower()
        if not term:
            self._filtered_entries = list(self._entries)
        else:
            self._filtered_entries = [
                entry
                for entry in self._entries
                if term in entry.name.lower() or term in entry.folder.lower()
            ]
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for entry in self._filtered_entries:
            self._tree.insert("", "end", values=(entry.name, entry.folder))

    def _open_selected(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        index = self._tree.index(selection[0])
        if index < 0 or index >= len(self._filtered_entries):
            return
        entry = self._filtered_entries[index]
        self._on_open(entry.path)
