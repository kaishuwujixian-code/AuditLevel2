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
        self.root.title("Mann Engineering - Energy Audit Report Generator")
        self.root.geometry("1100x760")
        self.root.minsize(980, 680)
        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=7)
        container.rowconfigure(1, weight=2)
        container.columnconfigure(0, weight=1)

        self._hero_canvas = tk.Canvas(container, highlightthickness=0)
        self._hero_canvas.grid(row=0, column=0, sticky="nsew")
        self._hero_canvas.bind("<Configure>", self._draw_welcome_banner)

        footer = ttk.Frame(container, padding=(20, 16))
        footer.grid(row=1, column=0, sticky="nsew")
        footer.columnconfigure(0, weight=1)

        ttk.Label(
            footer,
            text="MANN ENGINEERING",
            font=("Arial", 24, "bold"),
            foreground="#1d4ea0",
        ).grid(row=0, column=0)
        ttk.Label(
            footer,
            text="A LEADER IN RENEWABLE STRATEGIES",
            font=("Arial", 14, "bold"),
            foreground="#ef6b1f",
        ).grid(row=1, column=0, pady=(2, 8))

        button_row = ttk.Frame(footer)
        button_row.grid(row=2, column=0, pady=(8, 8))

        ttk.Button(
            button_row,
            text="Enter Level 1 Generator",
            command=lambda: self._launch_profile("level1"),
            width=24,
        ).grid(row=0, column=0, padx=8)
        ttk.Button(
            button_row,
            text="Enter Level 2 Generator",
            command=lambda: self._launch_profile("level2"),
            width=24,
        ).grid(row=0, column=1, padx=8)

        ttk.Label(
            footer,
            text="© 2024 Mann Engineering. www.MannEngineering.com",
            font=("Arial", 13),
            foreground="#2b2b2b",
        ).grid(row=3, column=0, pady=(12, 0))

    def _draw_welcome_banner(self, event: tk.Event) -> None:
        width, height = max(event.width, 1), max(event.height, 1)
        canvas = self._hero_canvas
        canvas.delete("all")

        top = (22, 90, 191)
        bottom = (183, 219, 255)
        steps = 120
        for i in range(steps):
            y0 = int(i * height / steps)
            y1 = int((i + 1) * height / steps)
            ratio = i / max(steps - 1, 1)
            r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
            g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
            b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
            canvas.create_rectangle(0, y0, width, y1, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

        # soft radial highlight
        cx, cy = width * 0.5, height * 0.56
        for i in range(16):
            pad = i * 28
            alpha_ratio = 1 - i / 16
            color = int(255 * alpha_ratio)
            outline = f"#{color:02x}{color:02x}{color:02x}"
            canvas.create_oval(
                cx - 300 - pad,
                cy - 230 - pad,
                cx + 300 + pad,
                cy + 230 + pad,
                outline=outline,
                width=2,
            )

        canvas.create_text(
            width * 0.5,
            height * 0.19,
            text="MANN ENGINEERING",
            font=("Arial", max(int(width * 0.045), 24), "bold"),
            fill="#f1f7ff",
        )
        canvas.create_text(
            width * 0.5,
            height * 0.28,
            text="A LEADER IN RENEWABLE STRATEGIES",
            font=("Arial", max(int(width * 0.02), 13), "bold"),
            fill="#ffd2b0",
        )
        canvas.create_text(
            width * 0.5,
            height * 0.78,
            text="Energy Audit Report Generator™",
            font=("Arial", max(int(width * 0.05), 30), "bold"),
            fill="#eef4ff",
        )

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
