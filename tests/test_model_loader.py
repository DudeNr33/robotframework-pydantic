from __future__ import annotations

from pathlib import Path

import pytest

from PydanticLibrary.model_loader import discover_pydantic_models, load_models_module


def test_load_models_module_from_file_path(models_file: Path) -> None:
    module = load_models_module(str(models_file))

    assert module.__name__ == "robotframework_pydantic_models__models"


def test_discover_pydantic_models_filters_non_models(models_file: Path) -> None:
    module = load_models_module(str(models_file))

    models = discover_pydantic_models(module)

    assert sorted(models) == ["CartItem", "ShoppingCart"]


def test_non_existent_model_file_path_has_clear_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing_models.py"

    with pytest.raises(FileNotFoundError, match="Model file does not exist"):
        load_models_module(str(missing))
