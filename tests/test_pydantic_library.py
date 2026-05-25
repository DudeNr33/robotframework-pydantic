from __future__ import annotations

from pathlib import Path
from typing import Any

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
    assert type(obj).__module__ == "robotframework_pydantic_models__models"


def test_create_dynamic_keyword_returns_model_instance(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    obj = lib.run_keyword(
        "Create ShoppingCart",
        tuple(),
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


def test_non_existent_model_file_path_has_clear_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing_models.py"

    with pytest.raises(FileNotFoundError, match="Model file does not exist"):
        PydanticLibrary(str(missing))


def test_validate_keyword_rejects_kwargs(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    with pytest.raises(TypeError, match="Unexpected keyword arguments"):
        lib.run_keyword(
            "Validate ShoppingCart",
            tuple(),
            {"cart_id": 1, "customer_name": "Alice"},
        )


def test_create_keyword_documentation_is_concise(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    doc = lib.get_keyword_documentation("Create CartItem")

    assert "Create and return an instance of ``CartItem``" in doc
    assert "Use named arguments matching the model field names." in doc
    assert "Fields for ``CartItem``:" not in doc


def test_create_keyword_rejects_positional_arguments(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    with pytest.raises(TypeError, match="accepts only named arguments"):
        lib.run_keyword("Create CartItem", ({"product_id": 1},), {})


def test_create_keyword_arguments_expose_model_fields(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    cart_item_args = lib.get_keyword_arguments("Create CartItem")
    shopping_cart_args = lib.get_keyword_arguments("Create ShoppingCart")

    assert cart_item_args[0] == "*"
    assert "product_id" in cart_item_args
    assert "unit_price" in cart_item_args
    discount_arg = next(
        arg for arg in cart_item_args if isinstance(arg, tuple) and arg[0] == "discount"
    )
    assert discount_arg[1] is not None
    assert cart_item_args[-1] == "**extra"

    assert "cart_id" in shopping_cart_args
    assert ("notes", None) in shopping_cart_args


def test_keyword_types_include_model_fields_and_return_type(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    validate_types = lib.get_keyword_types("Validate ShoppingCart")
    create_types = lib.get_keyword_types("Create CartItem")
    shopping_cart_types = lib.get_keyword_types("Create ShoppingCart")

    assert validate_types["data"] is dict
    assert validate_types["return"].__name__ == "ShoppingCart"

    assert create_types["extra"] is Any
    assert create_types["product_id"] is int
    assert create_types["quantity"] is int
    assert create_types["unit_price"].__name__ == "Decimal"
    assert create_types["return"].__name__ == "CartItem"
    assert shopping_cart_types["items"] == "list[CartItem]"
