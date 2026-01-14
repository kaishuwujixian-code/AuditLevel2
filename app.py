import tkinter as tk

from ui.project_browser import ProjectBrowserApp


def main() -> None:
    root = tk.Tk()
    ProjectBrowserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
