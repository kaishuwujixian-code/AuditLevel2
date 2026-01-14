import tkinter as tk

from ui.main_window import MainWindow
from ui.project_browser import ProjectBrowserApp


def main() -> None:
    root = tk.Tk()
    MainWindow(root)
    ProjectBrowserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
