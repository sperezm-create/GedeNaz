from decimal import Decimal
from datetime import datetime

import pytest

from gedenaz.data.product_repository import InMemoryProductRepository
from gedenaz.data.sales_repository import InMemorySalesRepository
from gedenaz.logic.product_service import ProductService
from gedenaz.logic.sales_service import SalesService


def make_services():
    products = InMemoryProductRepository()
    product_service = ProductService(products)
    sales_service = SalesService(InMemorySalesRepository(products))
    return product_service, sales_service


def test_calendar_datetime_parser_preserves_sale_hour_and_seconds():
    from gedenaz.ui.dashboard import DashboardView

    sale_time = DashboardView._sale_datetime({"fecha": "2026-11-15 14:32:45"})

    assert sale_time == datetime(2026, 11, 15, 14, 32, 45)


def test_calendar_excludes_cancelled_sales_but_keeps_current_sales():
    from gedenaz.ui.dashboard import DashboardView

    dashboard = DashboardView.__new__(DashboardView)
    vigente = {"id": 1, "fecha": datetime(2026, 11, 15, 14, 0), "anulada": False}
    anulada = {"id": 2, "fecha": datetime(2026, 11, 15, 15, 0), "anulada": True}
    otro_mes = {"id": 3, "fecha": datetime(2026, 12, 1, 10, 0), "anulada": False}
    dashboard.sales_history_map = {
        str(sale["id"]): sale for sale in (vigente, anulada, otro_mes)
    }

    assert dashboard._calendar_sales_for_month(2026, 11) == [
        (vigente["fecha"], vigente)
    ]


def test_sale_records_receipt_decreases_stock_and_updates_product_stats():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Anillo", "categoria": "Anillo", "precio": Decimal("12500"), "stock": 5}
    )

    receipt = sales.create_sale([{"product_id": product_id, "quantity": 2}])

    assert receipt["id"] == 1
    assert receipt["total"] == Decimal("25000")
    assert receipt["items"][0]["codigo_producto"] == "GN-000001"
    assert receipt["items"][0]["nombre_producto"] == "Anillo"
    assert receipt["items"][0]["categoria_producto"] == "anillo"
    assert receipt["items"][0]["material_producto"] == "Sin especificar"
    assert receipt["items"][0]["talla_producto"] == "Única"
    assert receipt["items"][0]["genero_destino"] == "No especificado"
    assert products.get(product_id)["stock"] == 3
    assert sales.list_sales()[0]["id"] == receipt["id"]
    assert sales.product_stats() == [
        {
            "product_id": product_id,
            "codigo_producto": "GN-000001",
            "nombre_producto": "Anillo",
            "unidades_vendidas": 2,
            "ingresos": Decimal("25000"),
        }
    ]


def test_category_stats_show_percentages_and_price_stats_rank_unit_prices():
    products, sales = make_services()
    ring_id = products.create(
        {"nombre": "Anillo", "categoria": "Anillo", "precio": Decimal("12500"), "stock": 8}
    )
    earrings_id = products.create(
        {"nombre": "Aros", "categoria": "Aros", "precio": Decimal("12500"), "stock": 8}
    )
    bracelet_id = products.create(
        {"nombre": "Pulsera", "categoria": "Pulsera", "precio": Decimal("5000"), "stock": 8}
    )

    sales.create_sale(
        [
            {"product_id": ring_id, "quantity": 2},
            {"product_id": earrings_id, "quantity": 1},
            {"product_id": bracelet_id, "quantity": 1},
        ]
    )

    assert sales.category_stats() == [
        {"categoria": "anillo", "unidades_vendidas": 2, "porcentaje": Decimal("50.00")},
        {"categoria": "aros", "unidades_vendidas": 1, "porcentaje": Decimal("25.00")},
        {"categoria": "pulsera", "unidades_vendidas": 1, "porcentaje": Decimal("25.00")},
    ]
    assert sales.price_stats() == [
        {"precio_unitario": Decimal("12500"), "unidades_vendidas": 3},
        {"precio_unitario": Decimal("5000"), "unidades_vendidas": 1},
    ]


def test_size_stats_rank_sizes_per_product_and_recipient_and_ignore_cancelled_sales():
    products, sales = make_services()
    ring_id = products.create(
        {
            "nombre": "Anillo",
            "categoria": "Anillo",
            "material": "Plata",
            "talla": "7",
            "precio": "12000",
            "stock": 10,
        }
    )
    ring_size_8_id = products.create(
        {
            "nombre": "Anillo",
            "categoria": "Anillo",
            "material": "Plata",
            "talla": "8",
            "precio": "12000",
            "stock": 10,
        }
    )
    earrings_id = products.create(
        {
            "nombre": "Aros",
            "categoria": "Aros",
            "material": "Oro",
            "talla": "Única",
            "precio": "8000",
            "stock": 10,
        }
    )

    sales.create_sale(
        [
            {"product_id": ring_id, "quantity": 2, "genero_destino": "Mujer"},
            {"product_id": ring_id, "quantity": 1, "genero_destino": "Hombre"},
            {"product_id": ring_size_8_id, "quantity": 3, "genero_destino": "Mujer"},
            {"product_id": earrings_id, "quantity": 2, "genero_destino": "Mujer"},
        ]
    )
    cancelled_sale = sales.create_sale(
        [{"product_id": earrings_id, "quantity": 1, "genero_destino": "Mujer"}]
    )
    sales.cancel_sale(cancelled_sale["id"])

    assert sales.size_stats() == [
        {
            "nombre_producto": "Anillo",
            "categoria_producto": "anillo",
            "material_producto": "Plata",
            "talla_producto": "7",
            "genero_destino": "Hombre",
            "unidades_vendidas": 1,
        },
        {
            "nombre_producto": "Anillo",
            "categoria_producto": "anillo",
            "material_producto": "Plata",
            "talla_producto": "8",
            "genero_destino": "Mujer",
            "unidades_vendidas": 3,
        },
        {
            "nombre_producto": "Anillo",
            "categoria_producto": "anillo",
            "material_producto": "Plata",
            "talla_producto": "7",
            "genero_destino": "Mujer",
            "unidades_vendidas": 2,
        },
        {
            "nombre_producto": "Aros",
            "categoria_producto": "aros",
            "material_producto": "Oro",
            "talla_producto": "Única",
            "genero_destino": "Mujer",
            "unidades_vendidas": 2,
        },
    ]


def test_monthly_stats_count_sales_and_revenue_for_requested_month_excluding_cancelled():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Collar", "categoria": "Collar", "precio": "1000", "stock": 10}
    )
    first_sale = sales.create_sale([{"product_id": product_id, "quantity": 2}])
    cancelled_sale = sales.create_sale([{"product_id": product_id, "quantity": 3}])
    other_month_sale = sales.create_sale([{"product_id": product_id, "quantity": 1}])
    repository = sales.repository
    repository._sales[0]["fecha"] = datetime(2026, 5, 3, 10, 0)
    repository._sales[1]["fecha"] = datetime(2026, 5, 4, 10, 0)
    repository._sales[2]["fecha"] = datetime(2026, 6, 1, 0, 0)
    sales.cancel_sale(cancelled_sale["id"])

    assert sales.monthly_stats(2026, 5) == {
        "anio": 2026,
        "mes": 5,
        "cantidad_ventas": 1,
        "ingresos": Decimal("2000"),
    }
    assert sales.monthly_stats(2026, 6) == {
        "anio": 2026,
        "mes": 6,
        "cantidad_ventas": 1,
        "ingresos": Decimal("1000"),
    }


def test_monthly_history_stats_groups_sales_and_revenue_by_month_and_year():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Collar", "categoria": "Collar", "precio": "1000", "stock": 10}
    )
    sales.create_sale([{"product_id": product_id, "quantity": 2}])
    cancelled_sale = sales.create_sale([{"product_id": product_id, "quantity": 3}])
    sales.create_sale([{"product_id": product_id, "quantity": 1}])
    repository = sales.repository
    repository._sales[0]["fecha"] = datetime(2026, 5, 3, 10, 0)
    repository._sales[1]["fecha"] = datetime(2026, 5, 4, 10, 0)
    repository._sales[2]["fecha"] = datetime(2025, 12, 31, 23, 59)
    sales.cancel_sale(cancelled_sale["id"])

    assert sales.monthly_history_stats() == [
        {
            "anio": 2026,
            "mes": 5,
            "cantidad_ventas": 1,
            "ingresos": Decimal("2000"),
        },
        {
            "anio": 2025,
            "mes": 12,
            "cantidad_ventas": 1,
            "ingresos": Decimal("1000"),
        },
    ]


@pytest.mark.parametrize(("year", "month"), [(0, 1), (2026, 0), (2026, 13)])
def test_monthly_stats_reject_invalid_year_or_month(year, month):
    _, sales = make_services()

    with pytest.raises(ValueError):
        sales.monthly_stats(year, month)


def test_sale_combines_duplicate_products_and_uses_price_at_sale_time():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Collar", "categoria": "Collar", "precio": Decimal("8000"), "stock": 5}
    )

    receipt = sales.create_sale(
        [
            {"product_id": product_id, "quantity": 1},
            {"product_id": product_id, "quantity": 2},
        ]
    )

    assert len(receipt["items"]) == 1
    assert receipt["items"][0]["cantidad"] == 3
    assert receipt["total"] == Decimal("24000")
    assert products.get(product_id)["stock"] == 2


def test_sale_keeps_recipient_and_product_variant_snapshot_per_line():
    products, sales = make_services()
    product_id = products.create(
        {
            "nombre": "Anillo",
            "categoria": "Anillo",
            "material": "Plata",
            "talla": "7",
            "precio": "12500",
            "stock": "3",
        }
    )

    receipt = sales.create_sale(
        [
            {"product_id": product_id, "quantity": 1, "genero_destino": "Hombre"},
            {"product_id": product_id, "quantity": 1, "genero_destino": "Mujer"},
        ]
    )

    assert len(receipt["items"]) == 2
    assert {item["genero_destino"] for item in receipt["items"]} == {"Hombre", "Mujer"}
    assert all(item["material_producto"] == "Plata" for item in receipt["items"])
    assert all(item["talla_producto"] == "7" for item in receipt["items"])
    assert products.get(product_id)["stock"] == 1


def test_stock_is_checked_across_recipient_lines_for_same_product():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Aros", "categoria": "Aros", "precio": "5000", "stock": "1"}
    )

    with pytest.raises(ValueError, match="Stock insuficiente"):
        sales.create_sale(
            [
                {"product_id": product_id, "quantity": 1, "genero_destino": "Hombre"},
                {"product_id": product_id, "quantity": 1, "genero_destino": "Mujer"},
            ]
        )

    assert products.get(product_id)["stock"] == 1
    assert sales.list_sales() == []


def test_insufficient_stock_does_not_record_sale_or_change_stock():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Aros", "categoria": "Aros", "precio": Decimal("5000"), "stock": 1}
    )

    with pytest.raises(ValueError, match="Stock insuficiente"):
        sales.create_sale([{"product_id": product_id, "quantity": 2}])

    assert products.get(product_id)["stock"] == 1
    assert sales.list_sales() == []
    assert sales.product_stats() == []


def test_sale_with_unavailable_second_product_does_not_partially_decrease_stock():
    products, sales = make_services()
    available_id = products.create(
        {"nombre": "Pulsera", "categoria": "Pulsera", "precio": Decimal("7000"), "stock": 3}
    )

    with pytest.raises(ValueError, match="no está disponible"):
        sales.create_sale(
            [
                {"product_id": available_id, "quantity": 1},
                {"product_id": 99, "quantity": 1},
            ]
        )

    assert products.get(available_id)["stock"] == 3
    assert sales.list_sales() == []


def test_cancel_sale_restores_stock_keeps_history_and_removes_units_from_stats():
    products, sales = make_services()
    ring_id = products.create(
        {"nombre": "Anillo", "categoria": "Anillo", "precio": Decimal("12500"), "stock": 5}
    )
    earrings_id = products.create(
        {"nombre": "Aros", "categoria": "Aros", "precio": Decimal("5000"), "stock": 8}
    )
    receipt = sales.create_sale(
        [
            {"product_id": ring_id, "quantity": 2},
            {"product_id": earrings_id, "quantity": 3},
        ]
    )

    sales.cancel_sale(receipt["id"])

    assert products.get(ring_id)["stock"] == 5
    assert products.get(earrings_id)["stock"] == 8
    history = sales.list_sales()
    assert len(history) == 1
    assert history[0]["anulada"] is True
    assert history[0]["items"] == receipt["items"]
    assert sales.product_stats() == []
    assert sales.category_stats() == []
    assert sales.price_stats() == []


def test_cannot_cancel_a_sale_more_than_once():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Pulsera", "categoria": "Pulsera", "precio": Decimal("7000"), "stock": 3}
    )
    receipt = sales.create_sale([{"product_id": product_id, "quantity": 1}])
    sales.cancel_sale(receipt["id"])

    with pytest.raises(ValueError, match="ya fue anulada"):
        sales.cancel_sale(receipt["id"])

    assert products.get(product_id)["stock"] == 3


def test_installment_sale_tracks_partial_payments_and_prevents_overpayment_and_cancellation():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Collar", "categoria": "Collar", "precio": "1000", "stock": 2}
    )

    receipt = sales.create_sale(
        [{"product_id": product_id, "quantity": 1}],
        {
            "cantidad_cuotas": "3",
            "frecuencia": "Mensual",
            "primer_vencimiento": "2026-11-30",
        },
    )

    plan = receipt["payment_plan"]
    assert [item["monto"] for item in plan["cuotas"]] == [
        Decimal("333"),
        Decimal("333"),
        Decimal("334"),
    ]
    assert [item["fecha_vencimiento"] for item in plan["cuotas"]] == [
        datetime(2026, 11, 30).date(),
        datetime(2026, 12, 30).date(),
        datetime(2027, 1, 30).date(),
    ]
    assert plan["saldo_pendiente"] == Decimal("1000")

    partial_plan = sales.add_payment(receipt["id"], 1, "100")
    assert partial_plan["cuotas"][0]["pagado"] == Decimal("100")
    assert partial_plan["cuotas"][0]["saldo"] == Decimal("233")
    assert partial_plan["cuotas"][0]["estado"] == "Parcial"
    assert partial_plan["total_pagado"] == Decimal("100")

    completed_plan = sales.add_payment(receipt["id"], 1, "233")
    assert completed_plan["cuotas"][0]["estado"] == "Pagada"
    assert completed_plan["saldo_pendiente"] == Decimal("667")
    assert len(completed_plan["cuotas"][0]["abonos"]) == 2
    assert sales.list_sales()[0]["payment_plan"]["total_pagado"] == Decimal("333")

    with pytest.raises(ValueError, match="supera el saldo"):
        sales.add_payment(receipt["id"], 1, "1")
    with pytest.raises(ValueError, match="abonos registrados"):
        sales.cancel_sale(receipt["id"])
    assert products.get(product_id)["stock"] == 1


def test_monthly_installments_clamp_end_of_month_due_dates():
    from gedenaz.installments import build_installment_schedule

    schedule = build_installment_schedule(
        Decimal("3000"),
        3,
        "Mensual",
        "2027-01-31",
    )

    assert [item["fecha_vencimiento"] for item in schedule] == [
        datetime(2027, 1, 31).date(),
        datetime(2027, 2, 28).date(),
        datetime(2027, 3, 31).date(),
    ]


def test_invalid_installment_plan_does_not_record_sale_or_decrease_stock():
    products, sales = make_services()
    product_id = products.create(
        {"nombre": "Aros", "categoria": "Aros", "precio": "1000", "stock": 1}
    )

    with pytest.raises(ValueError, match="entre 2 y 120 cuotas"):
        sales.create_sale(
            [{"product_id": product_id, "quantity": 1}],
            {
                "cantidad_cuotas": "1",
                "frecuencia": "Mensual",
                "primer_vencimiento": "2026-12-01",
            },
        )

    assert products.get(product_id)["stock"] == 1
    assert sales.list_sales() == []


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"product_id": 0, "quantity": 1}],
        [{"product_id": 1, "quantity": 0}],
        [{"product_id": 1, "quantity": 1.5}],
        [{"product_id": 1, "quantity": 1, "genero_destino": "Niño"}],
    ],
)
def test_invalid_sales_are_rejected(items):
    _, sales = make_services()

    with pytest.raises(ValueError):
        sales.create_sale(items)
