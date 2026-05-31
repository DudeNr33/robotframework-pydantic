from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PydanticLibrary import PydanticLibrary


class TestKeywordMetadata:
    def test_create_keyword_documentation(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        doc = pydantic_library.get_keyword_documentation("Create CartItem")

        assert "Create and return an instance of ``CartItem``" in doc
        assert "Use named arguments matching the model field names." in doc

    def test_create_keyword_arguments_expose_model_fields(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        cart_item_args = pydantic_library.get_keyword_arguments("Create CartItem")
        shopping_cart_args = pydantic_library.get_keyword_arguments(
            "Create ShoppingCart"
        )

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
        self, pydantic_library: PydanticLibrary
    ) -> None:
        validate_types = pydantic_library.get_keyword_types("Validate ShoppingCart")
        create_types = pydantic_library.get_keyword_types("Create CartItem")
        shopping_cart_types = pydantic_library.get_keyword_types("Create ShoppingCart")

        assert validate_types["data"] is dict
        assert validate_types["return"].__name__ == "ShoppingCart"

        assert create_types["extra"] is Any
        assert create_types["product_id"] is int
        assert create_types["quantity"] is int
        assert create_types["unit_price"].__name__ == "Decimal"
        assert create_types["return"].__name__ == "CartItem"
        assert shopping_cart_types["items"] == "list[CartItem]"

    def test_unknown_keyword_metadata_returns_generic_fallbacks(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        assert pydantic_library.get_keyword_arguments("Unknown Keyword") == [
            "*args",
            "**kwargs",
        ]
        assert pydantic_library.get_keyword_types("Unknown Keyword") == {}
        assert pydantic_library.get_keyword_documentation("Unknown Keyword") == ""

    def test_library_intro_documentation_is_available(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        intro = pydantic_library.get_keyword_documentation("__intro__")

        assert "Library for validating and creating Pydantic models" in intro

    def test_create_keyword_argument_metadata_handles_default_factory(
        self, write_python_module: Callable[[str, str], Path]
    ) -> None:
        models_file = write_python_module(
            "factory_models.py",
            """
            from pydantic import BaseModel, Field


            class FactoryModel(BaseModel):
                tags: list[str] = Field(default_factory=list)
            """,
        )
        lib = PydanticLibrary(str(models_file))

        args = lib.get_keyword_arguments("Create FactoryModel")

        assert ("tags", "<factory:list>") in args

    def test_keyword_types_render_supported_annotation_shapes(
        self, write_python_module: Callable[[str, str], Path]
    ) -> None:
        models_file = write_python_module(
            "typed_models.py",
            """
            from collections.abc import Callable, Sequence
            from typing import Any

            from pydantic import BaseModel


            class TypedModel(BaseModel):
                any_value: Any
                mapping: dict[str, int]
                pair: tuple[int, str]
                tags: set[int]
                seq: Sequence[int]
                either: int | str
                callback: Callable
            """,
        )

        lib = PydanticLibrary(str(models_file))

        types = lib.get_keyword_types("Create TypedModel")

        assert types["any_value"] is Any
        assert types["mapping"] == "dict[str, int]"
        assert types["pair"] == "tuple[int, str]"
        assert types["tags"] == "set[int]"
        assert types["seq"] == "Sequence[int]"
        assert types["either"] == "int | str"
        assert types["callback"].__name__ == "Callable"
