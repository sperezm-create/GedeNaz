"""API HTTP para clientes móviles y otros consumidores de GedeNaz."""

import secrets
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from gedenaz.config import get_api_credentials
from gedenaz.data.product_repository import ProductRepository
from gedenaz.data.sales_repository import SalesRepository
from gedenaz.logic.product_service import ProductService
from gedenaz.logic.sales_service import SalesService

basic_auth = HTTPBasic()


class ProductPayload(BaseModel):
    nombre: str
    categoria: str
    material: str = "Sin especificar"
    talla: str = "Única"
    precio: Decimal = Field(gt=0)
    stock: int = Field(ge=0)


class SaleItemPayload(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    genero_destino: str = "No especificado"


class PaymentPlanPayload(BaseModel):
    cantidad_cuotas: int = Field(ge=2, le=120)
    frecuencia: str
    primer_vencimiento: date


class SalePayload(BaseModel):
    items: list[SaleItemPayload] = Field(min_length=1)
    payment_plan: PaymentPlanPayload | None = None


class PaymentPayload(BaseModel):
    installment_number: int = Field(gt=0)
    amount: Decimal = Field(gt=0)


def _bad_request(error: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def create_app(
    product_service: ProductService | None = None,
    sales_service: SalesService | None = None,
    credentials: tuple[str, str] | None = None,
) -> FastAPI:
    products = product_service or ProductService(
        ProductRepository(), fallback_on_error=False
    )
    sales = sales_service or SalesService(SalesRepository())
    application = FastAPI(title="GedeNaz API", version="1.0.0")

    def authenticate(
        supplied: Annotated[HTTPBasicCredentials, Depends(basic_auth)],
    ) -> str:
        expected_username, expected_password = credentials or get_api_credentials()
        username_valid = secrets.compare_digest(
            supplied.username.encode("utf-8"), expected_username.encode("utf-8")
        )
        password_valid = secrets.compare_digest(
            supplied.password.encode("utf-8"), expected_password.encode("utf-8")
        )
        if not (username_valid and password_valid):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos.",
                headers={"WWW-Authenticate": "Basic"},
            )
        return supplied.username

    AuthenticatedUser = Annotated[str, Depends(authenticate)]

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/auth/login")
    def login(username: AuthenticatedUser) -> dict[str, str]:
        return {"username": username}

    @application.get("/products")
    def list_products(
        username: AuthenticatedUser,
        name: str = Query(default=""),
        category: str = Query(default=""),
    ) -> list[dict[str, Any]]:
        return products.list(name=name, category=category)

    @application.post("/products", status_code=status.HTTP_201_CREATED)
    def create_product(
        payload: ProductPayload, username: AuthenticatedUser
    ) -> dict[str, int]:
        try:
            product_id = products.create(payload.model_dump())
        except ValueError as error:
            raise _bad_request(error) from error
        return {"id": product_id}

    @application.put("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    def update_product(
        product_id: int, payload: ProductPayload, username: AuthenticatedUser
    ) -> Response:
        if products.get(product_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
        try:
            products.update(product_id, payload.model_dump())
        except ValueError as error:
            raise _bad_request(error) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_product(product_id: int, username: AuthenticatedUser) -> Response:
        if products.get(product_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
        try:
            products.delete(product_id)
        except ValueError as error:
            raise _bad_request(error) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.get("/sales")
    def list_sales(username: AuthenticatedUser) -> list[dict[str, Any]]:
        return sales.list_sales()

    @application.post("/sales", status_code=status.HTTP_201_CREATED)
    def create_sale(payload: SalePayload, username: AuthenticatedUser) -> dict[str, Any]:
        plan = payload.payment_plan
        try:
            return sales.create_sale(
                [item.model_dump() for item in payload.items],
                payment_plan=(
                    {
                        "cantidad_cuotas": plan.cantidad_cuotas,
                        "frecuencia": plan.frecuencia,
                        "primer_vencimiento": plan.primer_vencimiento.isoformat(),
                    }
                    if plan is not None
                    else None
                ),
            )
        except ValueError as error:
            raise _bad_request(error) from error

    @application.post("/sales/{sale_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
    def cancel_sale(sale_id: int, username: AuthenticatedUser) -> Response:
        try:
            sales.cancel_sale(sale_id)
        except ValueError as error:
            raise _bad_request(error) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.get("/sales/{sale_id}/payment-plan")
    def get_payment_plan(
        sale_id: int, username: AuthenticatedUser
    ) -> dict[str, Any] | None:
        return sales.get_payment_plan(sale_id)

    @application.post("/sales/{sale_id}/payments")
    def add_payment(
        sale_id: int, payload: PaymentPayload, username: AuthenticatedUser
    ) -> dict[str, Any]:
        try:
            return sales.add_payment(
                sale_id, payload.installment_number, payload.amount
            )
        except ValueError as error:
            raise _bad_request(error) from error

    @application.get("/stats/products")
    def product_stats(username: AuthenticatedUser) -> list[dict[str, Any]]:
        return sales.product_stats()

    @application.get("/stats/categories")
    def category_stats(username: AuthenticatedUser) -> list[dict[str, Any]]:
        return sales.category_stats()

    @application.get("/stats/prices")
    def price_stats(username: AuthenticatedUser) -> list[dict[str, Any]]:
        return sales.price_stats()

    @application.get("/stats/sizes")
    def size_stats(username: AuthenticatedUser) -> list[dict[str, Any]]:
        return sales.size_stats()

    @application.get("/stats/monthly")
    def monthly_stats(
        username: AuthenticatedUser,
        year: int = Query(ge=1, le=9998),
        month: int = Query(ge=1, le=12),
    ) -> dict[str, Any]:
        try:
            return sales.monthly_stats(year, month)
        except ValueError as error:
            raise _bad_request(error) from error

    @application.get("/stats/monthly/history")
    def monthly_history_stats(username: AuthenticatedUser) -> list[dict[str, Any]]:
        return sales.monthly_history_stats()

    return application


app = create_app()


if __name__ == "__main__":
    uvicorn.run("gedenaz.api:app", host="0.0.0.0", port=8000)
