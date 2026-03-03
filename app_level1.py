import os
import tkinter as tk

os.environ["AUDITSTUDIO_AUDIT_PROFILE"] = "level1"

from ui.app import RetScreenApp


def main() -> None:
    root = tk.Tk()
    RetScreenApp(root, audit_label="Level 1")
    root.mainloop()


if __name__ == "__main__":
    main()
