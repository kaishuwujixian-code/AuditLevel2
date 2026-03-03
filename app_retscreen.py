import argparse
import os
import subprocess
import sys
from pathlib import Path

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class AuditEntryApp:
    def __init__(self, root: tk.Tk, script_path: Path, splash_path: Path) -> None:
        self.root = root
        self._script_path = script_path
        self._splash_path = splash_path
        self._background_image = None
        self._background_photo = None
        self.root.title("Mann Engineering - Energy Audit Report Generator")
        self.root.geometry("1100x700")
        self.root.minsize(860, 540)
        self._apply_theme()
        self._build_ui()

    def _apply_theme(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        palette = {
            "panel": "#0c2f68",
            "title": "#FFFFFF",
            "subtitle": "#D4E6FF",
            "primary": "#F28B24",
            "primary_active": "#EF7F11",
            "secondary": "#2F70CE",
            "secondary_active": "#285FB0",
        }

        style.configure("EntryPanel.TFrame", background=palette["panel"])
        style.configure(
            "EntryTitle.TLabel",
            background=palette["panel"],
            foreground=palette["title"],
            font=("Arial", 20, "bold"),
        )
        style.configure(
            "EntrySubtitle.TLabel",
            background=palette["panel"],
            foreground=palette["subtitle"],
            font=("Arial", 12),
        )

        style.configure(
            "Level1.TButton",
            font=("Arial", 12, "bold"),
            foreground="white",
            background=palette["primary"],
            borderwidth=0,
            padding=(24, 10),
        )
        style.map("Level1.TButton", background=[("active", palette["primary_active"])])

        style.configure(
            "Level2.TButton",
            font=("Arial", 12, "bold"),
            foreground="white",
            background=palette["secondary"],
            borderwidth=0,
            padding=(24, 10),
        )
        style.map("Level2.TButton", background=[("active", palette["secondary_active"])])

    def _build_ui(self) -> None:
        self._canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

        try:
            self._background_image = Image.open(self._splash_path)
        except Exception:
            self._background_image = None

        panel = ttk.Frame(self.root, style="EntryPanel.TFrame", padding=(28, 24))
        title = ttk.Label(
            panel,
            text="Welcome to Energy Audit Report Generator",
            style="EntryTitle.TLabel",
        )
        title.pack(pady=(0, 8))
        subtitle = ttk.Label(
            panel,
            text="Please select the audit level to continue",
            style="EntrySubtitle.TLabel",
        )
        subtitle.pack(pady=(0, 18))

        button_row = ttk.Frame(panel, style="EntryPanel.TFrame")
        button_row.pack()

        ttk.Button(
            button_row,
            text="Level 1",
            command=lambda: self._launch_profile("level1"),
            style="Level1.TButton",
        ).grid(row=0, column=0, padx=10)
        ttk.Button(
            button_row,
            text="Level 2",
            command=lambda: self._launch_profile("level2"),
            style="Level2.TButton",
        ).grid(row=0, column=1, padx=10)

        self._panel_window = self._canvas.create_window(0, 0, window=panel)
        self.root.bind("<Configure>", self._on_resize)
        self.root.after_idle(self._redraw)

    def _on_resize(self, _event: tk.Event) -> None:
        self._redraw()

    def _redraw(self) -> None:
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        self._canvas.config(width=width, height=height)
        self._canvas.delete("bg")

        if self._background_image is not None:
            resized = self._background_image.resize((width, height), Image.Resampling.LANCZOS)
            self._background_photo = ImageTk.PhotoImage(resized)
            self._canvas.create_image(0, 0, image=self._background_photo, anchor="nw", tags="bg")
        else:
            self._canvas.create_rectangle(0, 0, width, height, fill="#1e64c8", outline="", tags="bg")

        self._canvas.coords(self._panel_window, width // 2, int(height * 0.7))

    def _launch_profile(self, profile: str) -> None:
        env = os.environ.copy()
        env["AUDITSTUDIO_AUDIT_PROFILE"] = profile
        subprocess.Popen([sys.executable, str(self._script_path), "--profile", profile], env=env)
        self.root.destroy()


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

    assets_path = Path(__file__).resolve().parent / "assets" / "mann_splash.png"
    root = tk.Tk()
    AuditEntryApp(root, Path(__file__).resolve(), assets_path)
    root.mainloop()


if __name__ == "__main__":
    main()
