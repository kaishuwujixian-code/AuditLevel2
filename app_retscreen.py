import argparse
import os
import subprocess
import sys
from pathlib import Path

import tkinter as tk
from tkinter import ttk


class AuditEntryApp:
    def __init__(self, root: tk.Tk, script_path: Path) -> None:
        self.root = root
        self._script_path = script_path
        self.root.title("Audit Studio")
        self.root.geometry("560x320")
        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="欢迎进入 Audit Studio",
            font=("Arial", 16, "bold"),
        ).pack(pady=(12, 8))
        ttk.Label(container, text="请选择要生成的审计级别").pack(pady=(0, 24))

        button_row = ttk.Frame(container)
        button_row.pack()

        ttk.Button(
            button_row,
            text="Level 1",
            command=lambda: self._launch_profile("level1"),
            width=18,
        ).grid(row=0, column=0, padx=8)

        ttk.Button(
            button_row,
            text="Level 2",
            command=lambda: self._launch_profile("level2"),
            width=18,
        ).grid(row=0, column=1, padx=8)

    def _launch_profile(self, profile: str) -> None:
        env = os.environ.copy()
        env["AUDITSTUDIO_AUDIT_PROFILE"] = profile
        subprocess.Popen([sys.executable, str(self._script_path), "--profile", profile], env=env)
        self.root.destroy()


def _run_profile(profile: str) -> None:
    os.environ["AUDITSTUDIO_AUDIT_PROFILE"] = profile
    from ui.app import RetScreenApp

    root = tk.Tk()
    RetScreenApp(root)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Studio launcher")
    parser.add_argument("--profile", choices=["level1", "level2"], default=None)
    args = parser.parse_args()

    if args.profile:
        _run_profile(args.profile)
        return

    root = tk.Tk()
    AuditEntryApp(root, Path(__file__).resolve())
    root.mainloop()


if __name__ == "__main__":
    main()
