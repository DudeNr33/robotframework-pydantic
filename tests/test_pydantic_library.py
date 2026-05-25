from __future__ import annotations

from pathlib import Path

import pytest

from PydanticLibrary import PydanticLibrary


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


class ShoppingCart(BaseModel):
    cart_id: int
    customer_name: str
    items: list[CartItem]


class NotAModel:
    pass
""".strip()
        + "\n"
    )
    return path


def test_dynamic_keywords_are_discovered(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    names = lib.get_keyword_names()

    assert "Validate CartItem" in names
    assert "Validate ShoppingCart" in names
    assert "Create CartItem" in names
    assert "Create ShoppingCart" in names


def test_validate_keyword_returns_validated_model(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    obj = lib.run_keyword(
        "Validate ShoppingCart",
        (
            {
                "cart_id": "1",
                "customer_name": "Alice",
                "items": [
                    {
                        "product_id": 101,
                        "name": "Apple",
                        "quantity": 3,
                        "unit_price": "0.50",
                    }
                ],
            },
        ),
        {},
    )

    assert obj.cart_id == 1
    assert obj.customer_name == "Alice"
    assert len(obj.items) == 1
    assert obj.items[0].name == "Apple"


def test_create_dynamic_keyword_returns_model_instance(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    obj = lib.run_keyword(
        "Create ShoppingCart",
        (
            {
                "cart_id": 2,
                "customer_name": "Bob",
                "items": [
                    {
                        "product_id": 202,
                        "name": "Banana",
                        "quantity": 5,
                        "unit_price": "1.20",
                    }
                ],
            },
        ),
        {},
    )

    assert obj.cart_id == 2
    assert obj.customer_name == "Bob"
    assert len(obj.items) == 1
    assert obj.items[0].name == "Banana"


def test_validation_error_is_reported_as_assertion_error(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    with pytest.raises(AssertionError, match="Validation failed"):
        lib.run_keyword(
            "Validate ShoppingCart",
            (
                {
                    "cart_id": "not-an-int",
                    "customer_name": "Alice",
                    "items": [],
                },
            ),
            {},
        )


def test_validate_keyword_rejects_kwargs(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    with pytest.raises(TypeError, match="Unexpected keyword arguments"):
        lib.run_keyword(
            "Validate ShoppingCart",
            tuple(),
            {"cart_id": 1, "customer_name": "Alice"},
        )
