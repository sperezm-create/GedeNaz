from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from gedenaz.api import create_app


class ProductServiceStub:
    def __init__(self):
        self.products = [
            {
                "id": 7,
                "nombre": "Anillo",
                "categoria": "anillo",
                "material": "Plata",
                "talla": "16",
                "precio": Decimal("12500.00"),
                "stock": 4,
            }
        ]

    def list(self, name="", category=""):
        return self.products

    def get(self, product_id):
        return next((item for item in self.products if item["id"] == product_id), None)

    def create(self, data):
        return 8

    def update(self, product_id, data):
        return None

    def delete(self, product_id):
        return None


class SalesServiceStub:
    def __init__(self, fail_create=False):
        self.fail_create = fail_create
        self.created_sale = None

    def list_sales(self):
        return []

    def create_sale(self, items, payment_plan=None):
        if self.fail_create:
            raise ValueError("Stock insuficiente.")
        self.created_sale = {"items": items, "payment_plan": payment_plan}
        return {"id": 12, "total": Decimal("25000.00")}

    def cancel_sale(self, sale_id):
        return None

    def get_payment_plan(self, sale_id):
        return None

    def add_payment(self, sale_id, installment_number, amount):
        return {"saldo_pendiente": Decimal("10.00")}

    def product_stats(self):
        return []

    def category_stats(self):
        return []

    def price_stats(self):
        return []


def create_client(*, fail_create=False):
    sales = SalesServiceStub(fail_create=fail_create)
    app = create_app(
        product_service=ProductServiceStub(),
        sales_service=sales,
        credentials=("tablet-admin", "test-password"),
    )
    return TestClient(app), sales


def test_health_does_not_require_authentication():
    client, _ = create_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_endpoint_requires_valid_credentials():
    client, _ = create_client()

    response = client.get("/products")

    assert response.status_code == 401


def test_login_accepts_configured_credentials():
    client, _ = create_client()

    response = client.post(
        "/auth/login",
        auth=("tablet-admin", "test-password"),
    )

    assert response.status_code == 200
    assert response.json() == {"username": "tablet-admin"}


def test_products_are_returned_with_json_safe_decimal_values():
    client, _ = create_client()

    response = client.get("/products", auth=("tablet-admin", "test-password"))

    assert response.status_code == 200
    assert response.json()[0]["precio"] == "12500.00"


def test_sale_endpoint_normalizes_installment_date():
    client, sales = create_client()

    response = client.post(
        "/sales",
        auth=("tablet-admin", "test-password"),
        json={
            "items": [{"product_id": 7, "quantity": 2}],
            "payment_plan": {
                "cantidad_cuotas": 2,
                "frecuencia": "mensual",
                "primer_vencimiento": "2026-12-01",
            },
        },
    )

    assert response.status_code == 201
    assert sales.created_sale["payment_plan"]["primer_vencimiento"] == "2026-12-01"
    assert sales.created_sale["payment_plan"]["primer_vencimiento"] == date(2026, 12, 1).isoformat()


def test_business_validation_errors_are_returned_as_bad_request():
    client, _ = create_client(fail_create=True)

    response = client.post(
        "/sales",
        auth=("tablet-admin", "test-password"),
        json={"items": [{"product_id": 7, "quantity": 2}]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Stock insuficiente."
