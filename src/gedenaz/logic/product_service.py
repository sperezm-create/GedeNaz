"""Casos de uso y reglas de negocio de productos."""

from typing import Any

from gedenaz.data.product_repository import InMemoryProductRepository, ProductRepository
from gedenaz.logic.validators import validate_product


class ProductService:
    def __init__(self, repository: ProductRepository | InMemoryProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()
        self._memory_repository = InMemoryProductRepository()

    def _run_with_fallback(self, operation, *args, **kwargs):
        try:
            return operation(self.repository, *args, **kwargs)
        except Exception:
            if self.repository is not self._memory_repository:
                self.repository = self._memory_repository
                return operation(self.repository, *args, **kwargs)
            raise

    def create(self, data: dict[str, Any]) -> int:
        product = validate_product(data)
        return self._run_with_fallback(
            lambda repo, *rest: (
                repo.add_stock_or_create(product)
                if hasattr(repo, "add_stock_or_create")
                else repo.create(product)
            )
        )

    def list(self, name: str = "", category: str = "") -> list[dict[str, Any]]:
        return self._run_with_fallback(lambda repo, *rest: repo.list_active(name, category))

    def get(self, product_id: int) -> dict[str, Any] | None:
        return self._run_with_fallback(lambda repo, *rest: repo.get(product_id))

    def update(self, product_id: int, data: dict[str, Any]) -> None:
        self._run_with_fallback(lambda repo, *rest: repo.update(product_id, validate_product(data)))

    def delete(self, product_id: int) -> None:
        self._run_with_fallback(lambda repo, *rest: repo.deactivate(product_id))
