from __future__ import annotations

import pytest

from PydanticLibrary import PydanticLibrary


class TestKeywordExecution:
    def test_validate_keyword_returns_validated_model(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        obj = pydantic_library.run_keyword(
            name="Validate ShoppingCart",
            args=(
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
            kwargs={},
        )

        assert obj.cart_id == 1
        assert obj.customer_name == "Alice"
        assert len(obj.items) == 1
        assert obj.items[0].name == "Apple"

    def test_create_dynamic_keyword_returns_model_instance(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        obj = pydantic_library.run_keyword(
            name="Create ShoppingCart",
            args=(),
            kwargs={
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

    def test_validation_error_is_reported_as_assertion_error(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(AssertionError, match="Validation failed"):
            pydantic_library.run_keyword(
                name="Validate ShoppingCart",
                args=(
                    {
                        "cart_id": "not-an-int",
                        "customer_name": "Alice",
                        "items": [],
                    },
                ),
                kwargs={},
            )

    def test_validate_keyword_rejects_kwargs(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(TypeError, match="Unexpected keyword arguments"):
            pydantic_library.run_keyword(
                name="Validate ShoppingCart",
                args=(),
                kwargs={"cart_id": 1, "customer_name": "Alice"},
            )

    def test_validate_keyword_requires_exactly_one_positional_argument(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(TypeError, match="requires exactly one positional argument"):
            pydantic_library.run_keyword("Validate ShoppingCart", (), {})

    def test_create_keyword_rejects_positional_arguments(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(TypeError, match="accepts only named arguments"):
            pydantic_library.run_keyword("Create CartItem", ({"product_id": 1},), {})

    def test_create_keyword_rejects_mixed_positional_and_named_arguments(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(TypeError, match="accepts only named arguments"):
            pydantic_library.run_keyword(
                "Create CartItem", ({"product_id": 1},), {"name": "Apple"}
            )

    def test_create_keyword_validation_error_is_reported_as_assertion_error(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(AssertionError, match="Creation failed"):
            pydantic_library.run_keyword(
                name="Create CartItem",
                args=(),
                kwargs={
                    "product_id": "not-an-int",
                    "name": "Apple",
                    "quantity": 1,
                    "unit_price": "1.2",
                },
            )

    def test_run_keyword_rejects_unknown_keyword(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(AttributeError, match="Unknown keyword"):
            pydantic_library.run_keyword("Unknown Keyword", (), {})

    def test_unknown_model_name_is_reported_for_validate_keyword(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(AttributeError, match="Unknown model 'MissingModel'"):
            pydantic_library.run_keyword("Validate MissingModel", ({},), {})

    def test_unknown_model_name_is_reported_for_create_keyword(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(AttributeError, match="Unknown model 'MissingModel'"):
            pydantic_library.run_keyword("Create MissingModel", (), {})

    def test_empty_model_name_keywords_are_rejected_as_unknown_keyword(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        with pytest.raises(AttributeError, match="Unknown keyword"):
            pydantic_library.run_keyword("Validate ", ({},), {})

        with pytest.raises(AttributeError, match="Unknown keyword"):
            pydantic_library.run_keyword("Create ", (), {})
