import tkinter as tk

from ui.app import RetScreenApp


def main() -> None:
    root = tk.Tk()
    RetScreenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
