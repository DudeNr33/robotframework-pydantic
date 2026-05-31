from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from PydanticLibrary import PydanticLibrary


class TestInitialization:
    def test_dynamic_keywords_are_discovered(
        self, pydantic_library: PydanticLibrary
    ) -> None:
        names = pydantic_library.get_keyword_names()

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
        self, write_python_module: Callable[[str, str], Path]
    ) -> None:
        no_models_file = write_python_module(
            "no_models.py",
            """
            class NotAModel:
                pass
            """,
        )

        with pytest.raises(ValueError, match="No Pydantic BaseModel subclasses found"):
            PydanticLibrary(str(no_models_file))

    def test_library_raises_for_non_existent_module_import_path(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            PydanticLibrary("missing_package.missing_models")

    def test_library_rejects_missing_models_argument(self) -> None:
        with pytest.raises(ValueError, match="'models' argument is required"):
            PydanticLibrary("")
