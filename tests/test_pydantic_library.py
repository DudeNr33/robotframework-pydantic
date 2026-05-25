from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Callable

import pytest

from PydanticLibrary import PydanticLibrary


class TestInitialization:
    def test_dynamic_keywords_are_discovered(self, models_file: Path) -> None:
        lib = PydanticLibrary(str(models_file))

        names = lib.get_keyword_names()

        assert "Validate CartItem" in names
        assert "Validate ShoppingCart" in names
        assert "Create CartItem" in names
        assert "Create ShoppingCart" in names

    def test_library_supports_module_import_path(self, models_import_path: str) -> None:
        lib = PydanticLibrary(models_import_path)

        names = lib.get_keyword_names()
        obj = lib.run_keyword("Create ImportedModel", tuple(), {"value": "41"})

        assert names == ["Validate ImportedModel", "Create ImportedModel"]
        assert obj.value == 41

    def test_library_raises_when_module_has_no_pydantic_models(
        self, tmp_path: Path
    ) -> None:
        no_models_file = tmp_path / "no_models.py"
        no_models_file.write_text("class NotAModel:\n    pass\n")

        with pytest.raises(ValueError, match="No Pydantic BaseModel subclasses found"):
            PydanticLibrary(str(no_models_file))

    def test_library_raises_for_non_existent_module_import_path(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            PydanticLibrary("missing_package.missing_models")

    def test_library_rejects_missing_models_argument(self) -> None:
        with pytest.raises(ValueError, match="'models' argument is required"):
            PydanticLibrary("")


class TestKeywordExecution:
    def test_validate_keyword_returns_validated_model(self, models_file: Path) -> None:
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

    def test_create_dynamic_keyword_returns_model_instance(
        self, models_file: Path
    ) -> None:
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

    def test_validation_error_is_reported_as_assertion_error(
        self, models_file: Path
    ) -> None:
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

    def test_validate_keyword_rejects_kwargs(self, models_file: Path) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(TypeError, match="Unexpected keyword arguments"):
            lib.run_keyword(
                "Validate ShoppingCart",
                tuple(),
                {"cart_id": 1, "customer_name": "Alice"},
            )

    def test_validate_keyword_requires_exactly_one_positional_argument(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(TypeError, match="requires exactly one positional argument"):
            lib.run_keyword("Validate ShoppingCart", tuple(), {})

    def test_create_keyword_rejects_positional_arguments(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(TypeError, match="accepts only named arguments"):
            lib.run_keyword("Create CartItem", ({"product_id": 1},), {})

    def test_create_keyword_rejects_mixed_positional_and_named_arguments(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(TypeError, match="accepts only named arguments"):
            lib.run_keyword("Create CartItem", ({"product_id": 1},), {"name": "Apple"})

    def test_create_keyword_validation_error_is_reported_as_assertion_error(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(AssertionError, match="Creation failed"):
            lib.run_keyword(
                "Create CartItem",
                tuple(),
                {
                    "product_id": "not-an-int",
                    "name": "Apple",
                    "quantity": 1,
                    "unit_price": "1.2",
                },
            )

    def test_run_keyword_rejects_unknown_keyword(self, models_file: Path) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(AttributeError, match="Unknown keyword"):
            lib.run_keyword("Unknown Keyword", tuple(), {})


class TestKeywordMetadata:
    def test_create_keyword_documentation_is_concise(self, models_file: Path) -> None:
        lib = PydanticLibrary(str(models_file))

        doc = lib.get_keyword_documentation("Create CartItem")

        assert "Create and return an instance of ``CartItem``" in doc
        assert "Use named arguments matching the model field names." in doc
        assert "Fields for ``CartItem``:" not in doc

    def test_create_keyword_arguments_expose_model_fields(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        cart_item_args = lib.get_keyword_arguments("Create CartItem")
        shopping_cart_args = lib.get_keyword_arguments("Create ShoppingCart")

        assert cart_item_args[0] == "*"
        assert "product_id" in cart_item_args
        assert "unit_price" in cart_item_args
        discount_arg = next(
            arg
            for arg in cart_item_args
            if isinstance(arg, tuple) and arg[0] == "discount"
        )
        assert discount_arg[1] is not None
        assert cart_item_args[-1] == "**extra"

        assert "cart_id" in shopping_cart_args
        assert ("notes", None) in shopping_cart_args

    def test_keyword_types_include_model_fields_and_return_type(
        self, models_file: Path
    ) -> None:
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

    def test_unknown_keyword_metadata_returns_generic_fallbacks(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        assert lib.get_keyword_arguments("Unknown Keyword") == ["*args", "**kwargs"]
        assert lib.get_keyword_types("Unknown Keyword") == {}
        assert lib.get_keyword_documentation("Unknown Keyword") == ""

    def test_library_intro_documentation_is_available(self, models_file: Path) -> None:
        lib = PydanticLibrary(str(models_file))

        intro = lib.get_keyword_documentation("__intro__")

        assert "Library for validating and creating Pydantic models" in intro

    def test_create_keyword_argument_metadata_handles_default_factory(
        self, tmp_path: Path
    ) -> None:
        models_file = tmp_path / "factory_models.py"
        models_file.write_text(
            """
from pydantic import BaseModel, Field


class FactoryModel(BaseModel):
    tags: list[str] = Field(default_factory=list)
""".strip()
            + "\n"
        )
        lib = PydanticLibrary(str(models_file))

        args = lib.get_keyword_arguments("Create FactoryModel")

        assert ("tags", "<factory:list>") in args


class TestInternalHelpers:
    def test_validate_and_create_keyword_name_resolution_errors_are_clear(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        assert lib._extract_model_name_from_validate_keyword("Not Validate") is None
        assert lib._extract_model_name_from_validate_keyword("Validate ") is None
        with pytest.raises(AttributeError, match="Unknown model 'MissingModel'"):
            lib._extract_model_name_from_validate_keyword("Validate MissingModel")

        assert lib._extract_model_name_from_create_keyword("Not Create") is None
        assert lib._extract_model_name_from_create_keyword("Create ") is None
        with pytest.raises(AttributeError, match="Unknown model 'MissingModel'"):
            lib._extract_model_name_from_create_keyword("Create MissingModel")

    def test_get_model_raises_for_unknown_model_name(self, models_file: Path) -> None:
        lib = PydanticLibrary(str(models_file))

        with pytest.raises(ValueError, match="Unknown model 'MissingModel'"):
            lib._get_model("MissingModel")

    def test_annotation_formatting_covers_common_generic_shapes(
        self, models_file: Path
    ) -> None:
        lib = PydanticLibrary(str(models_file))

        assert lib._type_for_argument_conversion(Any) is Any
        assert lib._format_annotation(Any) == "Any"
        assert (
            lib._type_for_argument_conversion("typing.Optional[int]") == "Optional[int]"
        )
        assert lib._format_annotation("NoneType | str") == "None | str"
        assert lib._format_annotation(dict[str, int]) == "dict[str, int]"
        assert lib._format_annotation(tuple[int, str]) == "tuple[int, str]"
        assert lib._format_annotation(set[int]) == "set[int]"
        assert lib._format_annotation(Sequence[int]) == "Sequence[int]"
        assert lib._format_annotation(int | str) == "int | str"
        assert lib._format_annotation(Callable) == "Callable"
        assert lib._format_annotation(__import__("typing").Union) == "Union"
