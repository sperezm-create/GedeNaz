import tkinter as tk
from tkinter import messagebox, ttk

from gedenaz.logic.product_service import ProductService

LIGHT = "#f9f5f1"
WHITE = "#ffffff"
TEXT = "#2f2a2a"
ACCENT = "#c7a36a"
ACCENT_DARK = "#8a6b3b"
BORDER = "#e7d7bf"
CATEGORIES = ("Anillo", "Pulsera", "Collar", "Aros")


def build_inventory_label(product):
    return str(product.get("nombre", "")).strip() or "Sin nombre"


def build_product_details(product):
    return (
        f"Nombre: {product.get('nombre', '')}\n"
        f"Categoría: {product.get('categoria', '')}\n"
        f"Precio: {product.get('precio', '')}\n"
        f"Stock: {product.get('stock', '')}\n"
        f"Fecha creación: {product.get('fecha_creacion', 'N/A')}\n"
        f"Último ingreso de stock: {product.get('fecha_ultimo_ingreso', 'N/A')}\n"
        f"Fecha actualización: {product.get('fecha_actualizacion', 'N/A')}"
    )


class DashboardView:
    def __init__(self, root, service=None, on_logout=None):
        self.root = root
        self.service = service or ProductService()
        self.on_logout = on_logout or (lambda: None)
        self.product_map = {}

        self.root.title("GedeNaz - Inventario")
        self.root.geometry("1100x620")
        self.root.configure(bg=LIGHT)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        footer = ttk.Frame(self.root, padding=(18, 8, 18, 14))
        footer.pack(fill="x", side="bottom")
        ttk.Button(footer, text="Cerrar sesión", command=self.on_logout).pack(side="right")

        self.form_tab = ttk.Frame(notebook, padding=18)
        self.list_tab = ttk.Frame(notebook, padding=18)
        notebook.add(self.form_tab, text="Crear producto")
        notebook.add(self.list_tab, text="Inventario")

        self.build_form()
        self.build_inventory()

    def build_form(self):
        container = ttk.Frame(self.form_tab, padding=20)
        container.pack(fill="both", expand=True)

        self.nombre_var = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.precio_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        fields = [
            ("Nombre", self.nombre_var),
            ("Categoría", self.categoria_var),
            ("Precio", self.precio_var),
            ("Stock", self.stock_var),
        ]

        for index, (label, var) in enumerate(fields):
            ttk.Label(container, text=label).grid(row=index, column=0, sticky="w", padx=10, pady=8)
            if label == "Categoría":
                ttk.Combobox(
                    container,
                    textvariable=var,
                    values=CATEGORIES,
                    state="readonly",
                    width=32,
                ).grid(row=index, column=1, padx=10, pady=8)
            else:
                ttk.Entry(container, textvariable=var, width=35).grid(row=index, column=1, padx=10, pady=8)

        save_button = ttk.Button(container, text="Guardar producto", command=self.handle_form_save)
        save_button.grid(row=4, column=1, sticky="e", padx=10, pady=(18, 0))

    def build_inventory(self):
        self.list_box = tk.Listbox(
            self.list_tab,
            height=20,
            width=120,
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 10),
        )
        self.list_box.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        self.list_box.bind("<Double-Button-1>", self.show_selected_product)

        actions = ttk.Frame(self.list_tab)
        actions.pack(fill="x", padx=16, pady=(0, 16))

        self.edit_button = ttk.Button(actions, text="Editar", command=self.edit_selected_product)
        self.edit_button.pack(side="left", padx=(0, 8))

        self.delete_button = ttk.Button(actions, text="Eliminar", command=self.delete_selected_product)
        self.delete_button.pack(side="left")

        self.refresh_products()

    def handle_form_save(self):
        data = {
            "nombre": self.nombre_var.get(),
            "categoria": self.categoria_var.get(),
            "precio": self.precio_var.get(),
            "stock": self.stock_var.get(),
        }
        try:
            self.service.create(data)
            self.clear_form()
            self.refresh_products()
            messagebox.showinfo("Producto guardado", "El producto fue guardado exitosamente.")
        except ValueError as exc:
            messagebox.showerror("Validación", str(exc))
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("Error", f"No se pudo guardar: {exc}")

    def clear_form(self):
        self.nombre_var.set("")
        self.categoria_var.set("")
        self.precio_var.set("")
        self.stock_var.set("")

    def get_selected_product(self):
        selection = self.list_box.curselection()
        if not selection:
            return None
        index = selection[0]
        product = self.product_map.get(index)
        if product is not None:
            return product
        return self.product_map.get(self.list_box.get(index))

    def show_selected_product(self, event=None):
        product = self.get_selected_product()
        if product is None:
            return
        messagebox.showinfo(f"Detalle: {product.get('nombre', '')}", build_product_details(product))

    def open_edit_dialog(self):
        product = self.get_selected_product()
        if product is None:
            messagebox.showwarning("Selecciona un producto", "Haz clic en un producto del inventario antes de editarlo.")
            return None

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar: {product.get('nombre', '')}")
        dialog.geometry("420x300")
        dialog.transient(self.root)
        dialog.grab_set()

        fields = ttk.Frame(dialog, padding=16)
        fields.pack(fill="both", expand=True)

        nombre_var = tk.StringVar(value=product.get("nombre", ""))
        categoria_var = tk.StringVar(value=product.get("categoria", ""))
        precio_var = tk.StringVar(value=str(product.get("precio", "")))
        stock_var = tk.StringVar(value=str(product.get("stock", "")))

        ttk.Label(fields, text="Nombre:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=nombre_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Categoría:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(
            fields, textvariable=categoria_var, values=CATEGORIES, state="readonly", width=27
        ).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Precio:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=precio_var, width=30).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Stock:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=stock_var, width=30).grid(row=3, column=1, padx=5, pady=5)

        button_row = ttk.Frame(fields)
        button_row.grid(row=4, column=0, columnspan=2, sticky="e", padx=5, pady=(12, 0))

        def save_changes():
            data = {
                "nombre": nombre_var.get(),
                "categoria": categoria_var.get(),
                "precio": precio_var.get(),
                "stock": stock_var.get(),
            }
            try:
                self.service.update(product["id"], data)
                self.refresh_products()
                dialog.destroy()
                messagebox.showinfo("Cambios guardados", "El producto se guardó correctamente con los cambios realizados.")
            except ValueError as exc:
                messagebox.showerror("Validación", str(exc))
            except Exception as exc:  # pragma: no cover
                messagebox.showerror("Error", f"No se pudo guardar los cambios: {exc}")

        def cancel_changes():
            answer = messagebox.askyesno(
                "Cancelar edición",
                "Si cancelas, se perderán los cambios realizados. ¿Deseas continuar?",
            )
            if answer:
                dialog.destroy()
                messagebox.showinfo("Edición cancelada", "La modificación fue descartada.")

        save_button = ttk.Button(button_row, text="Guardar", command=save_changes)
        save_button.pack(side="left", padx=(0, 8))

        cancel_button = ttk.Button(button_row, text="Cancelar", command=cancel_changes)
        cancel_button.pack(side="left")

        dialog.save_button = save_button
        dialog.cancel_button = cancel_button
        return dialog

    def edit_selected_product(self):
        self.open_edit_dialog()

    def delete_selected_product(self):
        product = self.get_selected_product()
        if product is None:
            messagebox.showwarning("Selecciona un producto", "Selecciona un producto para eliminarlo.")
            return

        confirm = messagebox.askyesno(
            "Confirmación",
            f"¿Deseas eliminar el producto '{product.get('nombre', '')}' del inventario?",
        )
        if not confirm:
            return

        try:
            self.service.delete(product["id"])
            self.refresh_products()
            messagebox.showinfo("Producto eliminado", f"'{product.get('nombre', '')}' fue eliminado correctamente.")
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("Error", f"No se pudo eliminar: {exc}")

    def refresh_products(self):
        self.list_box.delete(0, tk.END)
        self.product_map = {}
        products = self.service.list()
        if not products:
            self.list_box.insert(tk.END, "No hay productos registrados.")
            return

        for index, product in enumerate(products):
            label = (
                f"{build_inventory_label(product)} | {product.get('categoria', '')} | "
                f"Stock: {product.get('stock', 0)} | "
                f"Ingreso: {product.get('fecha_ultimo_ingreso', product.get('fecha_creacion', 'N/A'))}"
            )
            self.product_map[index] = product
            self.list_box.insert(tk.END, label)
