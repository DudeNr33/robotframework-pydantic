from __future__ import annotations

from pathlib import Path

import pytest


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


@pytest.fixture
def models_import_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    package_dir = tmp_path / "sample_project"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("\n")
    (package_dir / "models.py").write_text(
        """
from pydantic import BaseModel


class ImportedModel(BaseModel):
    value: int
""".strip()
        + "\n"
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    return "sample_project.models"
