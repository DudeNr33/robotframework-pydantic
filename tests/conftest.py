from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def models_file(tmp_path: Path) -> Path:
    path = tmp_path / "models.py"
    path.write_text(
        """
from decimal import Decimal

from pydantic import BaseModel


class CartItem(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: Decimal
    discount: Decimal = Decimal("0.00")


class ShoppingCart(BaseModel):
    cart_id: int
    customer_name: str
    items: list[CartItem]
    notes: str | None = None


class NotAModel:
    pass
""".strip()
        + "\n"
    )
    return path
