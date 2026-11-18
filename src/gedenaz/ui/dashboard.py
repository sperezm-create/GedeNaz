import calendar as calendar_module
from datetime import date, datetime
from decimal import Decimal
import tkinter as tk
from tkinter import messagebox, ttk

from gedenaz.codes import product_code, receipt_code
from gedenaz.data.sales_repository import InMemorySalesRepository
from gedenaz.logic.product_service import ProductService
from gedenaz.logic.sales_service import SalesService

LIGHT = "#f9f5f1"
WHITE = "#ffffff"
TEXT = "#2f2a2a"
ACCENT = "#c7a36a"
ACCENT_DARK = "#8a6b3b"
BORDER = "#e7d7bf"
CATEGORIES = ("Anillo", "Pulsera", "Collar", "Aros")
MONTHS = (
    "01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril",
    "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto",
    "09 - Septiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre",
)


def build_inventory_label(product):
    return str(product.get("nombre", "")).strip() or "Sin nombre"


def format_clp(amount):
    value = Decimal(str(amount))
    decimals = 2 if value != value.to_integral_value() else 0
    formatted = f"{value:,.{decimals}f}"
    if decimals:
        formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    else:
        formatted = formatted.replace(",", ".")
    return f"${formatted}"


def build_product_details(product):
    return (
        f"Código: {product_code(product.get('id', 0))}\n"
        f"Nombre: {product.get('nombre', '')}\n"
        f"Categoría: {product.get('categoria', '')}\n"
        f"Material: {product.get('material', 'Sin especificar')}\n"
        f"Talla: {product.get('talla', 'Única')}\n"
        f"Precio: {product.get('precio', '')}\n"
        f"Stock: {product.get('stock', '')}\n"
        f"Fecha creación: {product.get('fecha_creacion', 'N/A')}\n"
        f"Último ingreso de stock: {product.get('fecha_ultimo_ingreso', 'N/A')}\n"
        f"Fecha actualización: {product.get('fecha_actualizacion', 'N/A')}"
    )


class DashboardView:
    def __init__(self, root, service=None, on_logout=None, sales_service=None):
        self.root = root
        self.service = service or ProductService()
        self.sales_service = sales_service or SalesService(
            InMemorySalesRepository(getattr(self.service, "repository", None))
        )
        self.on_logout = on_logout or (lambda: None)
        self.product_map = {}
        self.sale_product_map = {}
        self.sale_cart = {}
        self.sales_history_map = {}
        self.calendar_sales_map = {}

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
        self.sales_tab = ttk.Frame(notebook, padding=18)
        self.stats_tab = ttk.Frame(notebook, padding=18)
        self.calendar_tab = ttk.Frame(notebook, padding=18)
        notebook.add(self.form_tab, text="Crear producto")
        notebook.add(self.list_tab, text="Inventario")
        notebook.add(self.sales_tab, text="Ventas")
        notebook.add(self.calendar_tab, text="Calendario de ventas")
        notebook.add(self.stats_tab, text="Estadísticas")

        self.build_form()
        self.build_inventory()
        self.build_sales()
        self.build_calendar()
        self.build_statistics()
        self.refresh_sale_products()
        self.refresh_sales_data()

    def build_form(self):
        container = ttk.Frame(self.form_tab, padding=20)
        container.pack(fill="both", expand=True)

        self.nombre_var = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.material_var = tk.StringVar(value="Sin especificar")
        self.talla_var = tk.StringVar(value="Única")
        self.precio_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        fields = [
            ("Nombre", self.nombre_var),
            ("Categoría", self.categoria_var),
            ("Material", self.material_var),
            ("Talla", self.talla_var),
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
        save_button.grid(row=len(fields), column=1, sticky="e", padx=10, pady=(18, 0))

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

    def build_sales(self):
        container = ttk.Frame(self.sales_tab, padding=12)
        container.pack(fill="both", expand=True)

        selector = ttk.Frame(container)
        selector.pack(fill="x", pady=(0, 10))

        self.sale_product_var = tk.StringVar()
        self.sale_product_combo = ttk.Combobox(
            selector, textvariable=self.sale_product_var, state="readonly", width=62
        )
        self.sale_product_combo.pack(side="left", padx=(0, 8))

        self.sale_quantity_var = tk.StringVar(value="1")
        ttk.Label(selector, text="Cantidad:").pack(side="left", padx=(4, 4))
        ttk.Entry(selector, textvariable=self.sale_quantity_var, width=8).pack(side="left", padx=(0, 8))
        ttk.Label(selector, text="Para:").pack(side="left", padx=(4, 4))
        self.sale_recipient_var = tk.StringVar(value="Hombre")
        ttk.Combobox(
            selector,
            textvariable=self.sale_recipient_var,
            values=("Hombre", "Mujer"),
            state="readonly",
            width=12,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(selector, text="Agregar al carrito", command=self.add_sale_item).pack(side="left")

        payment_options = ttk.Frame(container)
        payment_options.pack(fill="x", pady=(0, 8))
        self.payment_type_var = tk.StringVar(value="Pago completo")
        self.installment_count_var = tk.StringVar(value="3")
        self.installment_frequency_var = tk.StringVar(value="Mensual")
        today = date.today()
        next_month = today.month % 12 + 1
        next_month_year = today.year + today.month // 12
        next_month_day = min(
            today.day,
            calendar_module.monthrange(next_month_year, next_month)[1],
        )
        self.first_due_date_var = tk.StringVar(
            value=date(next_month_year, next_month, next_month_day).isoformat()
        )
        ttk.Label(payment_options, text="Forma de pago:").pack(side="left")
        self.payment_type_combo = ttk.Combobox(
            payment_options,
            textvariable=self.payment_type_var,
            values=("Pago completo", "En cuotas"),
            state="readonly",
            width=16,
        )
        self.payment_type_combo.pack(side="left", padx=(4, 12))
        self.payment_type_combo.bind("<<ComboboxSelected>>", self.on_payment_type_change)
        ttk.Label(payment_options, text="Cuotas:").pack(side="left")
        self.installment_count_entry = ttk.Entry(
            payment_options, textvariable=self.installment_count_var, width=6
        )
        self.installment_count_entry.pack(side="left", padx=(4, 12))
        ttk.Label(payment_options, text="Frecuencia:").pack(side="left")
        self.installment_frequency_combo = ttk.Combobox(
            payment_options,
            textvariable=self.installment_frequency_var,
            values=("Semanal", "Quincenal", "Mensual"),
            state="readonly",
            width=12,
        )
        self.installment_frequency_combo.pack(side="left", padx=(4, 12))
        ttk.Label(payment_options, text="Primer vencimiento (AAAA-MM-DD):").pack(side="left")
        self.first_due_date_entry = ttk.Entry(
            payment_options, textvariable=self.first_due_date_var, width=12
        )
        self.first_due_date_entry.pack(side="left", padx=(4, 0))
        self.on_payment_type_change()

        self.sale_cart_tree = ttk.Treeview(
            container,
            columns=("codigo", "nombre", "material", "talla", "destinatario", "cantidad", "precio", "subtotal"),
            show="headings",
            height=8,
        )
        for column, title, width in (
            ("codigo", "Código", 110),
            ("nombre", "Producto", 190),
            ("material", "Material", 110),
            ("talla", "Talla", 75),
            ("destinatario", "Para", 90),
            ("cantidad", "Cantidad", 90),
            ("precio", "Precio unitario", 130),
            ("subtotal", "Subtotal", 130),
        ):
            self.sale_cart_tree.heading(column, text=title)
            self.sale_cart_tree.column(column, width=width, anchor="w" if column in ("codigo", "nombre") else "e")
        self.sale_cart_tree.pack(fill="both", expand=True, pady=(0, 8))

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 14))
        self.sale_total_var = tk.StringVar(value="Total: $0")
        ttk.Label(actions, textvariable=self.sale_total_var, font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(actions, text="Vaciar carrito", command=self.clear_sale_cart).pack(side="right", padx=(8, 0))
        self.complete_sale_button = ttk.Button(
            actions, text="Confirmar venta y generar boleta", command=self.complete_sale
        )
        self.complete_sale_button.pack(side="right")

        ttk.Label(container, text="Ventas registradas (doble clic para ver la boleta)").pack(anchor="w")
        self.sales_list_box = tk.Listbox(container, height=5, bg=WHITE, fg=TEXT, font=("Segoe UI", 9))
        self.sales_list_box.pack(fill="x", pady=(5, 0))
        self.sales_list_box.bind("<Double-Button-1>", self.show_selected_sale)
        history_actions = ttk.Frame(container)
        history_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(
            history_actions,
            text="Gestionar cuotas / registrar abono",
            command=self.manage_selected_payments,
        ).pack(side="left")
        self.cancel_sale_button = ttk.Button(
            history_actions,
            text="Anular boleta y devolver productos al inventario",
            command=self.cancel_selected_sale,
        )
        self.cancel_sale_button.pack(side="right")

    def on_payment_type_change(self, event=None):
        state = "normal" if self.payment_type_var.get() == "En cuotas" else "disabled"
        self.installment_count_entry.configure(state=state)
        self.installment_frequency_combo.configure(state="readonly" if state == "normal" else "disabled")
        self.first_due_date_entry.configure(state=state)

    def build_calendar(self):
        container = ttk.Frame(self.calendar_tab, padding=8)
        container.pack(fill="both", expand=True)

        filters = ttk.Frame(container)
        filters.pack(fill="x", pady=(0, 8))

        now = datetime.now()
        self.calendar_year_var = tk.StringVar(value=str(now.year))
        self.calendar_month_var = tk.StringVar(value=MONTHS[now.month - 1])
        self.calendar_day_var = tk.StringVar(value=str(now.day))
        self.calendar_hour_var = tk.StringVar(value="Todas")

        ttk.Label(filters, text="Año:").pack(side="left")
        self.calendar_year_combo = ttk.Combobox(
            filters, textvariable=self.calendar_year_var, state="readonly", width=8
        )
        self.calendar_year_combo.pack(side="left", padx=(4, 12))
        self.calendar_year_combo.bind("<<ComboboxSelected>>", self.on_calendar_filter_change)

        ttk.Label(filters, text="Mes:").pack(side="left")
        self.calendar_month_combo = ttk.Combobox(
            filters, textvariable=self.calendar_month_var, values=MONTHS,
            state="readonly", width=16,
        )
        self.calendar_month_combo.pack(side="left", padx=(4, 12))
        self.calendar_month_combo.bind("<<ComboboxSelected>>", self.on_calendar_filter_change)

        ttk.Label(filters, text="Día:").pack(side="left")
        self.calendar_day_combo = ttk.Combobox(
            filters, textvariable=self.calendar_day_var, state="readonly", width=6
        )
        self.calendar_day_combo.pack(side="left", padx=(4, 12))
        self.calendar_day_combo.bind("<<ComboboxSelected>>", self.on_calendar_filter_change)

        ttk.Label(filters, text="Hora:").pack(side="left")
        self.calendar_hour_combo = ttk.Combobox(
            filters,
            textvariable=self.calendar_hour_var,
            values=("Todas", *(f"{hour:02d}:00" for hour in range(24))),
            state="readonly",
            width=10,
        )
        self.calendar_hour_combo.pack(side="left", padx=4)
        self.calendar_hour_combo.bind("<<ComboboxSelected>>", self.refresh_calendar_sales)

        self.calendar_grid = ttk.Frame(container)
        self.calendar_grid.pack(fill="x", pady=(0, 10))
        self.calendar_summary_var = tk.StringVar(value="Selecciona un día para consultar sus ventas.")
        ttk.Label(
            container, textvariable=self.calendar_summary_var, font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self.calendar_sales_tree = ttk.Treeview(
            container,
            columns=("hora", "boleta", "unidades", "total", "estado"),
            show="headings",
            height=8,
        )
        for column, title, width in (
            ("hora", "Hora", 100),
            ("boleta", "Boleta", 150),
            ("unidades", "Unidades", 120),
            ("total", "Total", 150),
            ("estado", "Estado", 120),
        ):
            self.calendar_sales_tree.heading(column, text=title)
            self.calendar_sales_tree.column(column, width=width, anchor="e" if column in ("unidades", "total") else "w")
        self.calendar_sales_tree.pack(fill="both", expand=True)
        self.calendar_sales_tree.bind("<Double-Button-1>", self.show_calendar_sale)
        self.on_calendar_filter_change()

    def build_statistics(self):
        container = ttk.Frame(self.stats_tab, padding=12)
        container.pack(fill="both", expand=True)

        stats_notebook = ttk.Notebook(container)
        monthly_frame = ttk.LabelFrame(container, text="Resumen del mes", padding=8)
        monthly_frame.pack(fill="x", pady=(0, 10))
        self.monthly_summary_var = tk.StringVar()
        ttk.Label(
            monthly_frame,
            textvariable=self.monthly_summary_var,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        stats_notebook.pack(fill="both", expand=True)
        products_frame = ttk.Frame(stats_notebook, padding=8)
        categories_frame = ttk.Frame(stats_notebook, padding=8)
        prices_frame = ttk.Frame(stats_notebook, padding=8)
        sizes_frame = ttk.Frame(stats_notebook, padding=8)
        monthly_history_frame = ttk.Frame(stats_notebook, padding=8)
        stats_notebook.add(products_frame, text="Productos")
        stats_notebook.add(categories_frame, text="Categorías")
        stats_notebook.add(prices_frame, text="Precios más vendidos")
        stats_notebook.add(sizes_frame, text="Tallas por género")
        stats_notebook.add(monthly_history_frame, text="Ventas por mes")

        ttk.Label(
            products_frame,
            text="Productos con más unidades vendidas",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.stats_tree = ttk.Treeview(products_frame, columns=("codigo", "nombre", "unidades", "ingresos"), show="headings")
        for column, title, width in (
            ("codigo", "Código", 130),
            ("nombre", "Producto", 360),
            ("unidades", "Unidades vendidas", 160),
            ("ingresos", "Total vendido", 160),
        ):
            self.stats_tree.heading(column, text=title)
            self.stats_tree.column(column, width=width, anchor="w" if column in ("codigo", "nombre") else "e")
        self.stats_tree.pack(fill="both", expand=True)

        ttk.Label(
            categories_frame,
            text="Participación por unidades vendidas (solo ventas vigentes)",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.category_stats_tree = ttk.Treeview(
            categories_frame,
            columns=("categoria", "unidades", "porcentaje"),
            show="headings",
        )
        for column, title, width in (
            ("categoria", "Categoría", 240),
            ("unidades", "Unidades vendidas", 180),
            ("porcentaje", "Porcentaje del total", 180),
        ):
            self.category_stats_tree.heading(column, text=title)
            self.category_stats_tree.column(column, width=width, anchor="w" if column == "categoria" else "e")
        self.category_stats_tree.pack(fill="both", expand=True)

        ttk.Label(
            prices_frame,
            text="Precios unitarios ordenados por unidades vendidas",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.price_stats_tree = ttk.Treeview(
            prices_frame,
            columns=("precio", "unidades"),
            show="headings",
        )
        self.price_stats_tree.heading("precio", text="Precio unitario")
        self.price_stats_tree.heading("unidades", text="Unidades vendidas")
        self.price_stats_tree.column("precio", width=220, anchor="e")
        self.price_stats_tree.column("unidades", width=180, anchor="e")
        self.price_stats_tree.pack(fill="both", expand=True)

        ttk.Label(
            sizes_frame,
            text="Unidades vendidas por talla para cada producto (solo ventas vigentes)",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        size_tables = ttk.Frame(sizes_frame)
        size_tables.pack(fill="both", expand=True)
        women_sizes_frame = ttk.LabelFrame(size_tables, text="Mujer", padding=8)
        women_sizes_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        men_sizes_frame = ttk.LabelFrame(size_tables, text="Hombre", padding=8)
        men_sizes_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        def create_size_tree(parent):
            tree = ttk.Treeview(
                parent,
                columns=("producto", "talla", "unidades"),
                show="headings",
            )
            for column, title, width in (
                ("producto", "Producto", 230),
                ("talla", "Talla", 90),
                ("unidades", "Unidades", 90),
            ):
                tree.heading(column, text=title)
                tree.column(column, width=width, anchor="e" if column == "unidades" else "w")
            tree.pack(fill="both", expand=True)
            return tree

        self.women_size_stats_tree = create_size_tree(women_sizes_frame)
        self.men_size_stats_tree = create_size_tree(men_sizes_frame)

        ttk.Label(
            monthly_history_frame,
            text="Ventas e ingresos acumulados por mes (boletas anuladas excluidas)",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.monthly_history_tree = ttk.Treeview(
            monthly_history_frame,
            columns=("periodo", "ventas", "ingresos"),
            show="headings",
        )
        for column, title, width in (
            ("periodo", "Mes", 220),
            ("ventas", "Cantidad de ventas", 200),
            ("ingresos", "Ingresos generados", 220),
        ):
            self.monthly_history_tree.heading(column, text=title)
            self.monthly_history_tree.column(
                column, width=width, anchor="e" if column != "periodo" else "w"
            )
        self.monthly_history_tree.pack(fill="both", expand=True)

        ttk.Button(
            container, text="Actualizar estadísticas", command=self.refresh_sales_data
        ).pack(anchor="e", pady=(8, 0))

    def refresh_sale_products(self):
        if not hasattr(self, "sale_product_combo"):
            return
        self.sale_product_map = {}
        choices = []
        for product in self.service.list():
            if int(product.get("stock", 0)) <= 0:
                continue
            code = product_code(product["id"])
            label = (
                f"{code} | {product.get('nombre', '')} | "
                f"{product.get('material', 'Sin especificar')} | "
                f"Talla {product.get('talla', 'Única')} | "
                f"{format_clp(product.get('precio', 0))} | stock: {product.get('stock', 0)}"
            )
            choices.append(label)
            self.sale_product_map[label] = product
        self.sale_product_combo.configure(values=choices)
        if self.sale_product_var.get() not in self.sale_product_map:
            self.sale_product_var.set(choices[0] if choices else "")

    def add_sale_item(self):
        label = self.sale_product_var.get()
        product = self.sale_product_map.get(label)
        if product is None:
            messagebox.showwarning("Selecciona un producto", "Elige un producto con stock del inventario.")
            return
        try:
            quantity = int(self.sale_quantity_var.get())
            if quantity <= 0 or str(quantity) != self.sale_quantity_var.get().strip():
                raise ValueError
        except ValueError:
            messagebox.showerror("Cantidad inválida", "Ingresa una cantidad entera mayor que cero.")
            return

        recipient = self.sale_recipient_var.get()
        if recipient not in ("Hombre", "Mujer"):
            messagebox.showerror("Destinatario inválido", "Selecciona Hombre o Mujer.")
            return

        product_id = int(product["id"])
        cart_quantity = sum(
            entry["quantity"]
            for (cart_product_id, _), entry in self.sale_cart.items()
            if cart_product_id == product_id
        )
        cart_key = (product_id, recipient)
        current_quantity = self.sale_cart.get(cart_key, {}).get("quantity", 0)
        if cart_quantity + quantity > int(product.get("stock", 0)):
            messagebox.showerror(
                "Stock insuficiente",
                f"Solo hay {product.get('stock', 0)} unidades disponibles de {product.get('nombre', '')}.",
            )
            return

        self.sale_cart[cart_key] = {
            "product": product,
            "quantity": current_quantity + quantity,
            "genero_destino": recipient,
        }
        self.sale_quantity_var.set("1")
        self.refresh_sale_cart()

    def refresh_sale_cart(self):
        for row in self.sale_cart_tree.get_children():
            self.sale_cart_tree.delete(row)
        total = Decimal("0")
        for (product_id, recipient), entry in self.sale_cart.items():
            product = entry["product"]
            quantity = entry["quantity"]
            price = Decimal(str(product["precio"]))
            subtotal = price * quantity
            total += subtotal
            self.sale_cart_tree.insert(
                "",
                tk.END,
                values=(
                    product_code(product_id),
                    product.get("nombre", ""),
                    product.get("material", "Sin especificar"),
                    product.get("talla", "Única"),
                    recipient,
                    quantity,
                    format_clp(price),
                    format_clp(subtotal),
                ),
            )
        self.sale_total_var.set(f"Total: {format_clp(total)}")

    def clear_sale_cart(self):
        self.sale_cart.clear()
        self.refresh_sale_cart()

    def complete_sale(self):
        if not self.sale_cart:
            messagebox.showwarning("Carrito vacío", "Agrega al menos un producto antes de confirmar la venta.")
            return
        payment_plan = None
        if self.payment_type_var.get() == "En cuotas":
            payment_plan = {
                "cantidad_cuotas": self.installment_count_var.get(),
                "frecuencia": self.installment_frequency_var.get(),
                "primer_vencimiento": self.first_due_date_var.get(),
            }
        try:
            sale = self.sales_service.create_sale(
                [
                    {
                        "product_id": product_id,
                        "quantity": entry["quantity"],
                        "genero_destino": entry["genero_destino"],
                    }
                    for (product_id, _), entry in self.sale_cart.items()
                ],
                payment_plan,
            )
        except ValueError as exc:
            messagebox.showerror("No se pudo registrar la venta", str(exc))
            self.refresh_products()
            return
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("Error", f"No se pudo registrar la venta: {exc}")
            return

        self.clear_sale_cart()
        try:
            self.refresh_products()
            self.refresh_sales_data()
        except Exception as exc:  # pragma: no cover
            messagebox.showwarning(
                "Venta registrada",
                f"La venta {receipt_code(sale['id'])} fue guardada, "
                f"pero no se pudo actualizar la pantalla: {exc}",
            )
        self.show_sale_receipt(sale)

    def manage_selected_payments(self):
        selection = self.sales_list_box.curselection()
        if not selection:
            messagebox.showwarning("Selecciona una venta", "Selecciona una venta del historial.")
            return
        sale_ids = list(self.sales_history_map)
        if selection[0] >= len(sale_ids):
            messagebox.showerror("Venta no encontrada", "No se pudo cargar la venta seleccionada.")
            return
        sale = self.sales_history_map.get(sale_ids[selection[0]])
        if sale is None:
            messagebox.showerror("Venta no encontrada", "No se pudo cargar la venta seleccionada.")
            return
        if sale.get("payment_plan") is None:
            messagebox.showinfo(
                "Sin plan de cuotas",
                "La venta seleccionada fue registrada como pago completo.",
            )
            return
        if sale.get("anulada"):
            messagebox.showinfo("Venta anulada", "No se pueden registrar abonos para una venta anulada.")
            return

        window = tk.Toplevel(self.root)
        window.title(f"Pagos - {receipt_code(sale['id'])}")
        window.geometry("760x520")
        window.transient(self.root)
        window.grab_set()

        summary_var = tk.StringVar()
        ttk.Label(window, textvariable=summary_var, font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=12, pady=(12, 6)
        )
        installments_tree = ttk.Treeview(
            window,
            columns=("numero", "vence", "monto", "pagado", "saldo", "estado"),
            show="headings",
            height=8,
        )
        for column, title, width in (
            ("numero", "Cuota", 70),
            ("vence", "Vencimiento", 130),
            ("monto", "Monto", 120),
            ("pagado", "Pagado", 120),
            ("saldo", "Saldo", 120),
            ("estado", "Estado", 110),
        ):
            installments_tree.heading(column, text=title)
            installments_tree.column(column, width=width, anchor="w" if column in ("vence", "estado") else "e")
        installments_tree.pack(fill="x", padx=12, pady=6)

        ttk.Label(window, text="Abonos registrados para la cuota seleccionada:").pack(
            anchor="w", padx=12, pady=(6, 0)
        )
        payments_tree = ttk.Treeview(
            window,
            columns=("fecha", "monto"),
            show="headings",
            height=5,
        )
        payments_tree.heading("fecha", text="Fecha y hora")
        payments_tree.heading("monto", text="Monto")
        payments_tree.column("fecha", width=250, anchor="w")
        payments_tree.column("monto", width=160, anchor="e")
        payments_tree.pack(fill="x", padx=12, pady=6)

        payment_controls = ttk.Frame(window)
        payment_controls.pack(fill="x", padx=12, pady=8)
        amount_var = tk.StringVar()
        ttk.Label(payment_controls, text="Nuevo abono:").pack(side="left")
        ttk.Entry(payment_controls, textvariable=amount_var, width=16).pack(
            side="left", padx=6
        )

        current_plan = {"value": None}

        def refresh_payment_dialog():
            try:
                plan = self.sales_service.get_payment_plan(int(sale["id"]))
            except Exception as exc:
                messagebox.showerror("Error", f"No se pudo cargar el plan de pagos: {exc}", parent=window)
                return
            if plan is None:
                messagebox.showerror("Plan no encontrado", "La venta ya no tiene un plan de cuotas.", parent=window)
                window.destroy()
                return
            current_plan["value"] = plan
            summary_var.set(
                f"Total: {format_clp(plan['monto_total'])} | "
                f"Pagado: {format_clp(plan['total_pagado'])} | "
                f"Saldo: {format_clp(plan['saldo_pendiente'])} | "
                f"Frecuencia: {plan['frecuencia']}"
            )
            for row in installments_tree.get_children():
                installments_tree.delete(row)
            for installment in plan["cuotas"]:
                due_date = installment["fecha_vencimiento"]
                if hasattr(due_date, "strftime"):
                    due_date = due_date.strftime("%Y-%m-%d")
                installments_tree.insert(
                    "",
                    tk.END,
                    iid=str(installment["numero"]),
                    values=(
                        installment["numero"],
                        due_date,
                        format_clp(installment["monto"]),
                        format_clp(installment["pagado"]),
                        format_clp(installment["saldo"]),
                        installment["estado"],
                    ),
                )
            selected = installments_tree.selection()
            if selected:
                show_installment_payments()

        def show_installment_payments(event=None):
            for row in payments_tree.get_children():
                payments_tree.delete(row)
            selected = installments_tree.selection()
            plan = current_plan["value"]
            if not selected or plan is None:
                return
            number = int(selected[0])
            installment = next(
                (item for item in plan["cuotas"] if item["numero"] == number),
                None,
            )
            if installment is None:
                return
            for payment in installment["abonos"]:
                paid_at = payment["fecha_pago"]
                if hasattr(paid_at, "strftime"):
                    paid_at = paid_at.strftime("%Y-%m-%d %H:%M:%S")
                payments_tree.insert(
                    "",
                    tk.END,
                    values=(paid_at, format_clp(payment["monto"])),
                )
            amount_var.set(str(installment["saldo"]) if installment["saldo"] > 0 else "")

        def register_payment():
            selected = installments_tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Selecciona una cuota",
                    "Selecciona la cuota a la que aplicarás el abono.",
                    parent=window,
                )
                return
            try:
                self.sales_service.add_payment(
                    int(sale["id"]),
                    int(selected[0]),
                    amount_var.get(),
                )
                self.refresh_sales_data()
                refresh_payment_dialog()
            except ValueError as exc:
                messagebox.showerror("Abono inválido", str(exc), parent=window)
            except Exception as exc:  # pragma: no cover
                messagebox.showerror("Error", f"No se pudo registrar el abono: {exc}", parent=window)

        installments_tree.bind("<<TreeviewSelect>>", show_installment_payments)
        ttk.Button(payment_controls, text="Registrar abono", command=register_payment).pack(
            side="left", padx=6
        )
        ttk.Button(payment_controls, text="Cerrar", command=window.destroy).pack(side="right")
        refresh_payment_dialog()

    def handle_form_save(self):
        data = {
            "nombre": self.nombre_var.get(),
            "categoria": self.categoria_var.get(),
            "material": self.material_var.get(),
            "talla": self.talla_var.get(),
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
        self.material_var.set("Sin especificar")
        self.talla_var.set("Única")
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
        product = self.product_map.get(self.list_box.get(index))
        if product is not None:
            return product
        if len(self.product_map) == 1:
            return next(iter(self.product_map.values()))
        return None

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
        dialog.geometry("420x390")
        dialog.transient(self.root)
        dialog.grab_set()

        fields = ttk.Frame(dialog, padding=16)
        fields.pack(fill="both", expand=True)

        nombre_var = tk.StringVar(value=product.get("nombre", ""))
        categoria_var = tk.StringVar(value=product.get("categoria", ""))
        material_var = tk.StringVar(value=product.get("material", "Sin especificar"))
        talla_var = tk.StringVar(value=product.get("talla", "Única"))
        precio_var = tk.StringVar(value=str(product.get("precio", "")))
        stock_var = tk.StringVar(value=str(product.get("stock", "")))

        ttk.Label(fields, text="Nombre:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=nombre_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Categoría:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(
            fields, textvariable=categoria_var, values=CATEGORIES, state="readonly", width=27
        ).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Material:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=material_var, width=30).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Talla:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=talla_var, width=30).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Precio:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=precio_var, width=30).grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(fields, text="Stock:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(fields, textvariable=stock_var, width=30).grid(row=5, column=1, padx=5, pady=5)

        button_row = ttk.Frame(fields)
        button_row.grid(row=6, column=0, columnspan=2, sticky="e", padx=5, pady=(12, 0))

        def save_changes():
            data = {
                "nombre": nombre_var.get(),
                "categoria": categoria_var.get(),
                "material": material_var.get(),
                "talla": talla_var.get(),
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
        self.refresh_sale_products()
        if not products:
            self.list_box.insert(tk.END, "No hay productos registrados.")
            return

        for index, product in enumerate(products):
            label = (
                f"{product_code(product['id'])} | {build_inventory_label(product)} | "
                f"{product.get('categoria', '')} | "
                f"{product.get('material', 'Sin especificar')} | "
                f"Talla {product.get('talla', 'Única')} | "
                f"Precio: {format_clp(product.get('precio', 0))} | "
                f"Stock: {product.get('stock', 0)} | "
                f"Ingreso: {product.get('fecha_ultimo_ingreso', product.get('fecha_creacion', 'N/A'))}"
            )
            self.product_map[index] = product
            self.list_box.insert(tk.END, label)

    def refresh_sales_data(self):
        sales = self.sales_service.list_sales()
        stats = self.sales_service.product_stats()
        category_stats = self.sales_service.category_stats()
        price_stats = self.sales_service.price_stats()
        size_stats = self.sales_service.size_stats()
        monthly_history = self.sales_service.monthly_history_stats()
        now = datetime.now()
        monthly_stats = self.sales_service.monthly_stats(now.year, now.month)
        month_name = MONTHS[now.month - 1].split(" - ", 1)[1]
        if hasattr(self, "monthly_summary_var"):
            self.monthly_summary_var.set(
                f"{month_name} {now.year} | Ventas: "
                f"{monthly_stats['cantidad_ventas']} | Ingresos: "
                f"{format_clp(monthly_stats['ingresos'])}"
            )

        self.sales_history_map = {}
        if hasattr(self, "sales_list_box"):
            self.sales_list_box.delete(0, tk.END)
            for sale in sales:
                total_units = sum(item["cantidad"] for item in sale["items"])
                status = " | ANULADA" if sale.get("anulada") else ""
                payment_plan = sale.get("payment_plan")
                payment_status = ""
                if payment_plan:
                    payment_status = (
                        f" | {len(payment_plan['cuotas'])} cuotas {payment_plan['frecuencia']}"
                        f" | Pagado {format_clp(payment_plan['total_pagado'])}"
                        f" | Debe {format_clp(payment_plan['saldo_pendiente'])}"
                    )
                label = (
                    f"{receipt_code(sale['id'])} | {sale['fecha']} | "
                    f"{format_clp(sale['total'])} | {total_units} unidad(es)"
                    f"{payment_status}{status}"
                )
                self.sales_history_map[str(sale["id"])] = sale
                self.sales_list_box.insert(tk.END, label)

        if hasattr(self, "stats_tree"):
            for row in self.stats_tree.get_children():
                self.stats_tree.delete(row)
            for item in stats:
                self.stats_tree.insert(
                    "",
                    tk.END,
                    values=(
                        item["codigo_producto"],
                        item["nombre_producto"],
                        item["unidades_vendidas"],
                        format_clp(item["ingresos"]),
                    ),
                )

        if hasattr(self, "category_stats_tree"):
            for row in self.category_stats_tree.get_children():
                self.category_stats_tree.delete(row)
            for item in category_stats:
                self.category_stats_tree.insert(
                    "",
                    tk.END,
                    values=(
                        item["categoria"],
                        item["unidades_vendidas"],
                        f"{item['porcentaje']}%",
                    ),
                )

        if hasattr(self, "price_stats_tree"):
            for row in self.price_stats_tree.get_children():
                self.price_stats_tree.delete(row)
            for item in price_stats:
                self.price_stats_tree.insert(
                    "",
                    tk.END,
                    values=(format_clp(item["precio_unitario"]), item["unidades_vendidas"]),
                )

        for recipient, tree_attribute in (
            ("Mujer", "women_size_stats_tree"),
            ("Hombre", "men_size_stats_tree"),
        ):
            if hasattr(self, tree_attribute):
                tree = getattr(self, tree_attribute)
                for row in tree.get_children():
                    tree.delete(row)
                for item in size_stats:
                    if item["genero_destino"] != recipient:
                        continue
                    product_label = (
                        f"{item['nombre_producto']} "
                        f"({item['categoria_producto']}, {item['material_producto']})"
                    )
                    tree.insert(
                        "",
                        tk.END,
                        values=(
                            product_label,
                            item["talla_producto"],
                            item["unidades_vendidas"],
                        ),
                    )

        if hasattr(self, "monthly_history_tree"):
            for row in self.monthly_history_tree.get_children():
                self.monthly_history_tree.delete(row)
            for item in monthly_history:
                month_name = MONTHS[item["mes"] - 1].split(" - ", 1)[1]
                self.monthly_history_tree.insert(
                    "",
                    tk.END,
                    values=(
                        f"{month_name} {item['anio']}",
                        item["cantidad_ventas"],
                        format_clp(item["ingresos"]),
                    ),
                )

        if hasattr(self, "calendar_sales_tree"):
            self.update_calendar_years(sales)
            self.render_sales_calendar()
            self.refresh_calendar_sales()

    def show_selected_sale(self, event=None):
        selection = self.sales_list_box.curselection()
        if not selection:
            return
        sale = list(self.sales_history_map.values())[selection[0]]
        self.show_sale_receipt(sale)

    def cancel_selected_sale(self):
        selection = self.sales_list_box.curselection()
        if not selection:
            messagebox.showwarning("Selecciona una boleta", "Selecciona una venta del historial para anularla.")
            return

        sale = list(self.sales_history_map.values())[selection[0]]
        if sale.get("anulada"):
            messagebox.showinfo("Boleta anulada", "Esta boleta ya fue anulada.")
            return

        confirm = messagebox.askyesno(
            "Confirmar anulación",
            f"¿Anular la boleta {receipt_code(sale['id'])} completa y devolver "
            "todos sus productos al inventario?\n\n"
            "La boleta se conservará en el historial y dejará de contar en las estadísticas. "
            "Las ventas con abonos registrados no se pueden anular desde la aplicación.",
        )
        if not confirm:
            return

        try:
            self.sales_service.cancel_sale(int(sale["id"]))
        except ValueError as exc:
            messagebox.showerror("No se pudo anular la boleta", str(exc))
            return
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("Error", f"No se pudo anular la boleta: {exc}")
            return

        try:
            self.refresh_products()
            self.refresh_sales_data()
        except Exception as exc:  # pragma: no cover
            messagebox.showwarning(
                "Boleta anulada",
                f"La boleta {receipt_code(sale['id'])} fue anulada y el stock fue repuesto, "
                f"pero no se pudo actualizar la pantalla: {exc}",
            )
            return

        messagebox.showinfo(
            "Boleta anulada",
            f"La boleta {receipt_code(sale['id'])} fue anulada y el stock fue repuesto.",
        )

    def show_sale_receipt(self, sale):
        date = sale["fecha"]
        if hasattr(date, "strftime"):
            date = date.strftime("%d-%m-%Y %H:%M:%S")
        lines = [
            "GedeNaz - Boleta interna",
            f"Número: {receipt_code(sale['id'])}",
            f"Fecha: {date}",
            "ESTADO: ANULADA" if sale.get("anulada") else "ESTADO: VIGENTE",
            "",
        ]
        for item in sale["items"]:
            lines.append(
                f"{item['codigo_producto']} | {item['nombre_producto']} x{item['cantidad']} "
                f"| {item.get('material_producto', 'Sin especificar')} "
                f"| Talla {item.get('talla_producto', 'Única')} "
                f"| Para: {item.get('genero_destino', 'No especificado')} "
                f"| @ {format_clp(item['precio_unitario'])}: {format_clp(item['subtotal'])}"
            )
        lines.extend(
            [
                "",
                f"TOTAL: {format_clp(sale['total'])}",
                "Esta boleta fue anulada y sus productos fueron devueltos."
                if sale.get("anulada")
                else "",
                "",
                "Comprobante interno; no es una boleta tributaria.",
            ]
        )
        payment_plan = sale.get("payment_plan")
        if payment_plan:
            lines.extend(
                [
                    "",
                    "PLAN DE CUOTAS SIN INTERÉS",
                    f"Frecuencia: {payment_plan['frecuencia']}",
                    f"Pagado: {format_clp(payment_plan['total_pagado'])}",
                    f"Saldo pendiente: {format_clp(payment_plan['saldo_pendiente'])}",
                ]
            )
        else:
            lines.extend(["", f"Pago completo: {format_clp(sale['total'])}"])
        messagebox.showinfo("Boleta de venta", "\n".join(lines))

    @staticmethod
    def _sale_datetime(sale):
        sale_date = sale.get("fecha")
        if isinstance(sale_date, datetime):
            return sale_date
        if sale_date is None:
            return None
        try:
            return datetime.fromisoformat(str(sale_date))
        except ValueError:
            return None

    def update_calendar_years(self, sales):
        years = {datetime.now().year}
        for sale in sales:
            if sale.get("anulada"):
                continue
            sale_date = self._sale_datetime(sale)
            if sale_date is not None:
                years.add(sale_date.year)
        year_values = [str(year) for year in sorted(years, reverse=True)]
        self.calendar_year_combo.configure(values=year_values)
        if self.calendar_year_var.get() not in year_values:
            self.calendar_year_var.set(year_values[0])

    def _calendar_sales_for_month(self, year, month):
        matching = []
        for sale in self.sales_history_map.values():
            if sale.get("anulada"):
                continue
            sale_date = self._sale_datetime(sale)
            if sale_date is not None and sale_date.year == year and sale_date.month == month:
                matching.append((sale_date, sale))
        return matching

    def on_calendar_filter_change(self, event=None):
        try:
            year = int(self.calendar_year_var.get())
            month = int(self.calendar_month_var.get()[:2])
            day_values = ["Todos"] + [
                str(day) for day in range(1, calendar_module.monthrange(year, month)[1] + 1)
            ]
        except (ValueError, IndexError):
            return

        self.calendar_day_combo.configure(values=day_values)
        if self.calendar_day_var.get() not in day_values:
            self.calendar_day_var.set("Todos")
        self.render_sales_calendar()
        self.refresh_calendar_sales()

    def render_sales_calendar(self):
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()
        try:
            year = int(self.calendar_year_var.get())
            month = int(self.calendar_month_var.get()[:2])
        except (ValueError, IndexError):
            return

        for column, weekday in enumerate(("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")):
            ttk.Label(self.calendar_grid, text=weekday, anchor="center").grid(
                row=0, column=column, sticky="ew", padx=2, pady=2
            )
            self.calendar_grid.columnconfigure(column, weight=1)

        sales_by_day = {}
        for sale_date, _ in self._calendar_sales_for_month(year, month):
            sales_by_day[sale_date.day] = sales_by_day.get(sale_date.day, 0) + 1

        month_weeks = calendar_module.Calendar(firstweekday=0).monthdayscalendar(year, month)
        for row, week in enumerate(month_weeks, start=1):
            for column, day in enumerate(week):
                if not day:
                    ttk.Label(self.calendar_grid, text="").grid(row=row, column=column, sticky="nsew")
                    continue
                count = sales_by_day.get(day, 0)
                text = f"{day}\n{count} venta(s)" if count else str(day)
                button = tk.Button(
                    self.calendar_grid,
                    text=text,
                    command=lambda selected_day=day: self.select_calendar_day(selected_day),
                    bg="#ead9bd" if count else WHITE,
                    fg=TEXT,
                    relief="solid",
                    bd=1,
                    height=2,
                )
                button.grid(row=row, column=column, sticky="nsew", padx=2, pady=2)

    def select_calendar_day(self, day):
        self.calendar_day_var.set(str(day))
        self.calendar_day_combo.configure(
            values=["Todos"] + [
                str(value)
                for value in range(
                    1,
                    calendar_module.monthrange(
                        int(self.calendar_year_var.get()),
                        int(self.calendar_month_var.get()[:2]),
                    )[1] + 1,
                )
            ]
        )
        self.refresh_calendar_sales()

    def refresh_calendar_sales(self, event=None):
        if not hasattr(self, "calendar_sales_tree"):
            return
        for row in self.calendar_sales_tree.get_children():
            self.calendar_sales_tree.delete(row)
        self.calendar_sales_map = {}

        try:
            year = int(self.calendar_year_var.get())
            month = int(self.calendar_month_var.get()[:2])
        except (ValueError, IndexError):
            self.calendar_summary_var.set("Selecciona un año y un mes válidos.")
            return

        selected_day = self.calendar_day_var.get()
        selected_hour = self.calendar_hour_var.get()
        matching = []
        for sale_date, sale in self._calendar_sales_for_month(year, month):
            if selected_day != "Todos" and selected_day:
                if sale_date.day != int(selected_day):
                    continue
            if selected_hour != "Todas" and sale_date.strftime("%H:00") != selected_hour:
                continue
            matching.append((sale_date, sale))

        matching.sort(key=lambda entry: (entry[0], entry[1]["id"]), reverse=True)
        valid_total = Decimal("0")
        for sale_date, sale in matching:
            total_units = sum(int(item["cantidad"]) for item in sale["items"])
            is_cancelled = bool(sale.get("anulada"))
            if not is_cancelled:
                valid_total += Decimal(str(sale["total"]))
            row_id = self.calendar_sales_tree.insert(
                "",
                tk.END,
                values=(
                    sale_date.strftime("%H:%M:%S"),
                    receipt_code(sale["id"]),
                    total_units,
                    format_clp(sale["total"]),
                    "Anulada" if is_cancelled else "Vigente",
                ),
            )
            self.calendar_sales_map[row_id] = sale

        day_label = selected_day if selected_day and selected_day != "Todos" else "todos"
        self.calendar_summary_var.set(
            f"{len(matching)} venta(s) para {day_label}/{month:02d}/{year} "
            f"| Total vigente: {format_clp(valid_total)}"
        )

    def show_calendar_sale(self, event=None):
        selection = self.calendar_sales_tree.selection()
        if not selection:
            return
        sale = self.calendar_sales_map.get(selection[0])
        if sale is not None:
            self.show_sale_receipt(sale)
