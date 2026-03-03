import argparse
import os
import subprocess
import sys
from pathlib import Path

import tkinter as tk
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
        self._build_ui()

    def _build_ui(self) -> None:
        self._canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

        try:
            self._background_image = Image.open(self._splash_path)
        except Exception:
            self._background_image = None

        panel = tk.Frame(self.root, bg="#0c2f68", padx=28, pady=24)
        title = tk.Label(
            panel,
            text="Welcome to Energy Audit Report Generator",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#0c2f68",
        )
        title.pack(pady=(0, 8))
        subtitle = tk.Label(
            panel,
            text="Please select the audit level to continue",
            font=("Arial", 12),
            fg="#d4e6ff",
            bg="#0c2f68",
        )
        subtitle.pack(pady=(0, 18))

        button_row = tk.Frame(panel, bg="#0c2f68")
        button_row.pack()

        tk.Button(
            button_row,
            text="Level 1",
            command=lambda: self._launch_profile("level1"),
            width=16,
            bg="#f28b24",
            fg="white",
            font=("Arial", 12, "bold"),
            activebackground="#ef7f11",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        ).grid(row=0, column=0, padx=10)
        tk.Button(
            button_row,
            text="Level 2",
            command=lambda: self._launch_profile("level2"),
            width=16,
            bg="#2f70ce",
            fg="white",
            font=("Arial", 12, "bold"),
            activebackground="#285fb0",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
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
