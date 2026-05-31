from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from textwrap import dedent

import pytest

from PydanticLibrary import PydanticLibrary

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
MODELS_DIR = FIXTURES_DIR / "models"


@pytest.fixture
def write_python_module(tmp_path: Path) -> Callable[[str, str], Path]:
    def _write_python_module(filename: str, source: str) -> Path:
        path = tmp_path / filename
        path.write_text(dedent(source).strip() + "\n")
        return path

    return _write_python_module


@pytest.fixture
def models_file() -> Path:
    return MODELS_DIR / "models.py"


@pytest.fixture
def pydantic_library(models_file: Path) -> PydanticLibrary:
    return PydanticLibrary(str(models_file))


@pytest.fixture
def models_import_path(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.syspath_prepend(str(FIXTURES_DIR))
    return "sample_project.models"
