from __future__ import annotations

import sys
from pathlib import Path

import pytest

from PydanticLibrary.model_loader import discover_pydantic_models, load_models_module


class TestLoadModelsModule:
    def test_load_from_file_path(self, models_file: Path) -> None:
        module = load_models_module(str(models_file))

        assert module.__name__ == "robotframework_pydantic_models__models"

    def test_load_from_import_path(self, models_import_path: str) -> None:
        module = load_models_module(models_import_path)

        assert module.__name__ == models_import_path

    def test_non_existent_file_path_has_clear_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing_models.py"

        with pytest.raises(FileNotFoundError, match="Model file does not exist"):
            load_models_module(str(missing))

    def test_non_python_file_path_is_rejected(self, tmp_path: Path) -> None:
        invalid_file = tmp_path / "models.txt"
        invalid_file.write_text("x = 1\n")

        with pytest.raises(ValueError, match="Model file must be a .py file"):
            load_models_module(str(invalid_file))

    def test_non_existent_import_path_raises_import_error(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            load_models_module("does_not_exist.models")

    def test_reports_spec_loading_errors_when_loading_from_file_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        module_file = tmp_path / "models.py"
        module_file.write_text("\n")

        monkeypatch.setattr(
            "PydanticLibrary.model_loader.importlib.util.spec_from_file_location",
            lambda *args, **kwargs: None,
        )

        with pytest.raises(ImportError, match="Could not load module spec"):
            load_models_module(str(module_file))

    def test_file_name_sanitization_is_reflected_in_loaded_module_name(
        self, tmp_path: Path
    ) -> None:
        module_file = tmp_path / "123-model.py"
        module_file.write_text(
            """
from pydantic import BaseModel


class LocalModel(BaseModel):
    value: int
""".strip()
            + "\n"
        )

        module = load_models_module(str(module_file))

        assert module.__name__ == "robotframework_pydantic_models___123_model"


class TestDiscoverPydanticModels:
    def test_filters_non_models(self, models_file: Path) -> None:
        module = load_models_module(str(models_file))

        models = discover_pydantic_models(module)

        assert sorted(models) == ["CartItem", "ShoppingCart"]

    def test_excludes_imported_model_classes(self, tmp_path: Path) -> None:
        external_file = tmp_path / "external_models.py"
        external_file.write_text(
            """
from pydantic import BaseModel


class ExternalModel(BaseModel):
    value: int
""".strip()
            + "\n"
        )

        main_file = tmp_path / "main_models.py"
        main_file.write_text(
            """
from pydantic import BaseModel
from external_models import ExternalModel


class LocalModel(BaseModel):
    value: int
""".strip()
            + "\n"
        )

        sys.path.insert(0, str(tmp_path))
        try:
            module = load_models_module(str(main_file))
            models = discover_pydantic_models(module)
        finally:
            sys.path.pop(0)

        assert sorted(models) == ["LocalModel"]
