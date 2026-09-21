"""Punto de entrada principal de la aplicación GedeNaz."""

import tkinter as tk
from tkinter import messagebox

from gedenaz.auth import is_valid_admin_login
from gedenaz.data.product_repository import InMemoryProductRepository
from gedenaz.logic.product_service import ProductService
from gedenaz.ui.dashboard import DashboardView


class LoginView:
    def __init__(self, root, on_login):
        self.root = root
        self.on_login = on_login
        self.root.title("GedeNaz App - Login")
        self.root.geometry("420x260")
        self.root.configure(bg="#f6f1eb")

        frame = tk.Frame(root, bg="#f6f1eb", padx=28, pady=28)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="GedeNaz", font=("Segoe UI", 24, "bold"), bg="#f6f1eb", fg="#2d2d2d").pack(pady=(0, 10))
        tk.Label(frame, text="Iniciar sesión", font=("Segoe UI", 12), bg="#f6f1eb").pack(pady=(0, 15))

        tk.Label(frame, text="Usuario", bg="#f6f1eb").pack(anchor="w")
        self.username_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.username_var, width=30).pack(pady=(0, 10))

        tk.Label(frame, text="Contraseña", bg="#f6f1eb").pack(anchor="w")
        self.password_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.password_var, width=30, show="*").pack(pady=(0, 15))

        tk.Button(frame, text="Entrar", command=self.handle_login, width=24, bg="#c9a76a", fg="white", bd=0, relief="flat").pack()

    def handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not is_valid_admin_login(username, password):
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return

        self.on_login()


class AppController:
    def __init__(self, root):
        self.root = root
        self.service = ProductService(InMemoryProductRepository())
        self.show_login()

    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginView(self.root, self.show_dashboard)

    def show_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        DashboardView(self.root, self.service, on_logout=self.show_login)


def main() -> None:
    root = tk.Tk()
    root.minsize(900, 560)
    AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
