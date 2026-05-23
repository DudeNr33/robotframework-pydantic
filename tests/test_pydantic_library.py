from __future__ import annotations

from pathlib import Path

import pytest

from robotframework_pydantic.pydanticlibrary import PydanticLibrary


@pytest.fixture
def models_file(tmp_path: Path) -> Path:
    path = tmp_path / "models.py"
    path.write_text(
        """
from pydantic import BaseModel


class FooBar(BaseModel):
    foo: int
    bar: str


class User(BaseModel):
    id: int
    name: str


class NotAModel:
    pass
""".strip()
        + "\n"
    )
    return path


def test_dynamic_keywords_are_discovered(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    names = lib.get_keyword_names()

    assert "Validate Schema" in names
    assert "Create FooBar" in names
    assert "Create User" in names


def test_validate_schema_keyword_returns_validated_model(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    obj = lib.run_keyword(
        "Validate Schema", tuple(), {"schema": "FooBar", "foo": "1", "bar": "test"}
    )

    assert obj.foo == 1
    assert obj.bar == "test"


def test_create_dynamic_keyword_returns_model_instance(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    obj = lib.run_keyword("Create FooBar", ({"foo": 2, "bar": "ok"},), {})

    assert obj.foo == 2
    assert obj.bar == "ok"


def test_validation_error_is_reported_as_assertion_error(models_file: Path) -> None:
    lib = PydanticLibrary(str(models_file))

    with pytest.raises(AssertionError, match="Validation failed"):
        lib.run_keyword(
            "Validate Schema",
            tuple(),
            {"schema": "FooBar", "foo": "not-an-int", "bar": "x"},
        )
