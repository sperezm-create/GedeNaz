from decimal import Decimal

import pytest

from gedenaz.logic.product_service import ProductService


class FakeRepository:
    def __init__(self):
        self.created = []

    def create(self, product):
        self.created.append(product)
        return 7

    def list_active(self, name="", category=""):
        return []

    def get(self, product_id):
        return None

    def update(self, product_id, product):
        pass

    def deactivate(self, product_id):
        pass


def test_create_validates_and_normalizes_product():
    repository = FakeRepository()
    service = ProductService(repository)

    product_id = service.create(
        {"nombre": "  Anillo  ", "categoria": "  anillo", "precio": "12500", "stock": "3"}
    )

    assert product_id == 7
    assert repository.created == [
        {"nombre": "Anillo", "categoria": "anillo", "precio": Decimal("12500"), "stock": 3}
    ]


def test_create_adds_stock_to_existing_product():
    from gedenaz.data.product_repository import InMemoryProductRepository

    service = ProductService(InMemoryProductRepository())

    service.create({"nombre": "Anillo", "categoria": "anillo", "precio": "12500", "stock": "3"})
    product_id = service.create(
        {"nombre": " anillo ", "categoria": "ANILLO", "precio": "12500", "stock": "2"}
    )

    products = service.list()
    assert product_id == products[0]["id"]
    assert len(products) == 1
    assert products[0]["stock"] == 5
    assert products[0]["fecha_ultimo_ingreso"] is not None


def test_service_falls_back_to_memory_repository_when_db_fails():
    service = ProductService()

    def fail_repository(*args, **kwargs):
        raise RuntimeError("DB offline")

    service.repository = type("BrokenRepository", (), {"create": fail_repository, "list_active": fail_repository, "get": fail_repository, "update": fail_repository, "deactivate": fail_repository})()

    product_id = service.create({"nombre": "Pulsera", "categoria": "oro", "precio": "50000", "stock": "4"})

    assert product_id == 1
    assert service.list()[0]["nombre"] == "Pulsera"


def test_inventory_label_and_details_uses_product_name_only():
    from gedenaz.ui.dashboard import build_inventory_label, build_product_details

    product = {"id": 3, "nombre": "Collar", "categoria": "oro", "precio": "120000", "stock": 8}

    assert build_inventory_label(product) == "Collar"
    detail_text = build_product_details(product)
    assert "Collar" in detail_text
    assert "Stock: 8" in detail_text


def test_dashboard_exposes_edit_and_delete_actions():
    import tkinter as tk

    from gedenaz.ui.dashboard import DashboardView

    class DummyService:
        def list(self):
            return []

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter no está disponible en este entorno de pruebas.")
    try:
        view = DashboardView(root, DummyService())
        assert hasattr(view, "edit_button")
        assert hasattr(view, "delete_button")
    finally:
        root.destroy()


def test_dashboard_edit_window_has_save_and_cancel_buttons():
    import tkinter as tk

    from gedenaz.ui.dashboard import DashboardView

    class DummyService:
        def list(self):
            return [{"id": 1, "nombre": "Anillo", "categoria": "oro", "precio": "120000", "stock": 5}]

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter no está disponible en este entorno de pruebas.")

    try:
        view = DashboardView(root, DummyService())
        view.product_map = {"Anillo": {"id": 1, "nombre": "Anillo", "categoria": "oro", "precio": "120000", "stock": 5}}
        view.list_box.insert(tk.END, "Anillo")
        view.list_box.select_set(0)
        dialog = view.open_edit_dialog()
        assert hasattr(dialog, "save_button")
        assert hasattr(dialog, "cancel_button")
        dialog.destroy()
    finally:
        root.destroy()


@pytest.mark.parametrize(
    ("field", "value"),
    [("nombre", ""), ("categoria", ""), ("precio", "0"), ("stock", "-1"), ("stock", "1.5")],
)
def test_create_rejects_invalid_product(field, value):
    repository = FakeRepository()
    service = ProductService(repository)
    product = {"nombre": "Producto", "categoria": "otro", "precio": "1000", "stock": "1"}
    product[field] = value

    with pytest.raises(ValueError):
        service.create(product)

    assert repository.created == []