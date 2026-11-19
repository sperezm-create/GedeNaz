"""Punto de entrada principal de la aplicación GedeNaz."""

import tkinter as tk

from gedenaz.auth import is_valid_admin_login
from gedenaz.data.product_repository import ProductRepository
from gedenaz.data.sales_repository import SalesRepository
from gedenaz.logic.product_service import ProductService
from gedenaz.logic.sales_service import SalesService
from gedenaz.ui.dashboard import DashboardView


BG = "#f1e9dc"        # beige plano, suave para la vista
FIELD_BG = "#faf6ee"
TEXT = "#3b3329"
MUTED = "#7a6e5d"
ACCENT = "#a8814a"
ACCENT_HOVER = "#8f6d3b"
ERROR = "#a63d2f"
FONT = "Segoe UI"


class LoginView:
    def __init__(self, root, on_login):
        self.root = root
        self.on_login = on_login
        self.root.title("GedeNaz - Iniciar sesión")
        self.root.configure(bg=BG)
        self.root.minsize(380, 440)
        self._place_window(400, 460)

        frame = tk.Frame(root, bg=BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="GedeNaz", font=(FONT, 28, "bold"), bg=BG, fg=TEXT).pack()
        tk.Label(
            frame, text="Ingresa con tu usuario", font=(FONT, 11), bg=BG, fg=MUTED
        ).pack(pady=(2, 26))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.username_entry = self._field(frame, "Usuario", self.username_var)
        self.password_entry = self._field(frame, "Contraseña", self.password_var, show="•")

        # Mensaje de error en la misma pantalla (sin ventanas emergentes).
        self.error_label = tk.Label(
            frame, text="", font=(FONT, 10), bg=BG, fg=ERROR, height=2,
            wraplength=280, justify="center",
        )
        self.error_label.pack(pady=(4, 6))

        self.button = tk.Button(
            frame, text="Entrar", command=self.handle_login, width=24,
            font=(FONT, 11, "bold"), bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            activeforeground="white", bd=0, relief="flat", cursor="hand2", pady=8,
        )
        self.button.pack()
        self.button.bind("<Enter>", lambda _e: self.button.config(bg=ACCENT_HOVER))
        self.button.bind("<Leave>", lambda _e: self.button.config(bg=ACCENT))

        # Enter envía el formulario; escribir de nuevo limpia el error.
        self.root.bind("<Return>", lambda _e: self.handle_login())
        self.username_var.trace_add("write", lambda *_: self._clear_error())
        self.password_var.trace_add("write", lambda *_: self._clear_error())
        self.username_entry.focus_set()

    def _place_window(self, width, height):
        self.root.update_idletasks()
        x = max((self.root.winfo_screenwidth() - width) // 2, 0)
        y = max((self.root.winfo_screenheight() - height) // 3, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _field(self, parent, label, variable, show=""):
        tk.Label(parent, text=label, font=(FONT, 10), bg=BG, fg=MUTED, anchor="w").pack(
            fill="x"
        )
        entry = tk.Entry(
            parent, textvariable=variable, width=30, show=show, font=(FONT, 12),
            bg=FIELD_BG, fg=TEXT, insertbackground=TEXT, relief="flat",
            highlightthickness=1, highlightbackground="#d9cbb3", highlightcolor=ACCENT,
        )
        entry.pack(ipady=7, pady=(2, 14))
        return entry

    def _clear_error(self):
        self.error_label.config(text="")

    def handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.error_label.config(text="Escribe tu usuario y contraseña.")
            (self.username_entry if not username else self.password_entry).focus_set()
            return

        if not is_valid_admin_login(username, password):
            self.password_var.set("")  # permite reintentar de inmediato
            self.error_label.config(text="Usuario o contraseña incorrectos.")
            self.password_entry.focus_set()
            return

        self.root.unbind("<Return>")
        self.on_login()


class AppController:
    def __init__(self, root):
        self.root = root
        self.service = ProductService(ProductRepository(), fallback_on_error=False)
        self.sales_service = SalesService(SalesRepository())
        self.show_login()

    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginView(self.root, self.show_dashboard)

    def show_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.minsize(900, 560)
        DashboardView(
            self.root,
            self.service,
            on_logout=self.show_login,
            sales_service=self.sales_service,
        )


def main() -> None:
    root = tk.Tk()
    AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
