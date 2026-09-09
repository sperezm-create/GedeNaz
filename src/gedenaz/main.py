"""Punto de entrada de GedeNaz App.

Placeholder de la tarea 1.1 (Carta Gantt): confirma que el entorno de
desarrollo (Python + Tkinter + venv) esta correctamente configurado.
Las pantallas CRUD reales se agregan en las Fases 1-3 (ver
docs/specs/04-plan-de-trabajo.md).
"""

import tkinter as tk


def main() -> None:
    root = tk.Tk()
    root.title("GedeNaz App")
    root.geometry("400x200")

    tk.Label(
        root,
        text="GedeNaz App\nEntorno de desarrollo configurado correctamente.",
        justify="center",
        pady=40,
    ).pack()

    root.mainloop()


if __name__ == "__main__":
    main()
