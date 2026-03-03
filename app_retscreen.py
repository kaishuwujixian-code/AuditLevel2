import argparse
import os
import subprocess
import sys
from pathlib import Path

import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk


class AuditEntryApp:
    def __init__(self, root: tk.Tk, script_path: Path) -> None:
        self.root = root
        self._script_path = script_path
        self.root.title("Mann Engineering - Energy Audit Report Generator")
        self.root.geometry("640x360")
        self.root.minsize(560, 320)
        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Welcome to Energy Audit Report Generator",
            font=("Arial", 16, "bold"),
        ).pack(pady=(12, 10))
        ttk.Label(
            container,
            text="Please select the audit level to continue",
            font=("Arial", 11),
        ).pack(pady=(0, 22))

        button_row = ttk.Frame(container)
        button_row.pack()

        ttk.Button(
            button_row,
            text="Level 1",
            command=lambda: self._launch_profile("level1"),
            width=20,
        ).grid(row=0, column=0, padx=8)
        ttk.Button(
            button_row,
            text="Level 2",
            command=lambda: self._launch_profile("level2"),
            width=20,
        ).grid(row=0, column=1, padx=8)

    def _launch_profile(self, profile: str) -> None:
        env = os.environ.copy()
        env["AUDITSTUDIO_AUDIT_PROFILE"] = profile
        subprocess.Popen([sys.executable, str(self._script_path), "--profile", profile], env=env)
        self.root.destroy()


def _create_splash(root: tk.Tk, image_path: Path) -> tk.Toplevel:
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)

    try:
        image = Image.open(image_path)
        photo = ImageTk.PhotoImage(image)
        splash._photo_ref = photo
        label = tk.Label(splash, image=photo, borderwidth=0, highlightthickness=0)
        label.pack()
        width, height = image.size
    except Exception:
        width, height = 700, 420
        label = tk.Label(
            splash,
            text="Energy Audit Report Generator",
            font=("Arial", 26, "bold"),
            bg="#1e64c8",
            fg="white",
            padx=40,
            pady=40,
        )
        label.pack(fill="both", expand=True)

    splash.update_idletasks()
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    return splash


def _run_profile(profile: str) -> None:
    os.environ["AUDITSTUDIO_AUDIT_PROFILE"] = profile
    from ui.app import RetScreenApp

    root = tk.Tk()
    audit_label = "Level 2" if profile == "level2" else "Level 1"
    RetScreenApp(root, audit_label=audit_label)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Studio launcher")
    parser.add_argument("--profile", choices=["level1", "level2"], default=None)
    args = parser.parse_args()

    if args.profile:
        _run_profile(args.profile)
        return

    root = tk.Tk()
    root.withdraw()

    assets_path = Path(__file__).resolve().parent / "assets" / "mann_splash.png"
    splash = _create_splash(root, assets_path)

    AuditEntryApp(root, Path(__file__).resolve())

    state = {"shown": False}

    def _show_main_window() -> None:
        if state["shown"]:
            return
        state["shown"] = True
        if splash.winfo_exists():
            splash.destroy()
        root.deiconify()

    root.after_idle(_show_main_window)
    root.after(1500, _show_main_window)
    root.mainloop()


if __name__ == "__main__":
    main()
