import tkinter as tk

from ui.questionnaire_app import QuestionnaireApp


def main() -> None:
    root = tk.Tk()
    QuestionnaireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
