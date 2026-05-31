from pathlib import Path
from textwrap import dedent

import pytest

from PydanticLibrary import PydanticLibrary


class _TestBase:
    """
    Base class for tests.
    Concrete test classes deriving from this class need to define the class
    attribute `model`, which is the source code for the pydantic model used
    in the test.
    The base class ensures that `self.library` is initialized with the correct
    models module content.
    """

    model: str
    library: PydanticLibrary

    @pytest.fixture(autouse=True)
    def create_library(self, tmp_path: Path) -> None:
        module_file = tmp_path / "model.py"
        module_file.write_text(dedent(self.model))
        self.library = PydanticLibrary(str(module_file))


class TestAliasSupport(_TestBase):
    model = """
    from uuid import UUID

    from pydantic import BaseModel, ConfigDict, Field

    class TestModel(BaseModel):
        model_config = ConfigDict(populate_by_name=True)
        order_id: UUID = Field(alias="orderId")
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate TestModel",
            ({"orderId": "00000000-0000-0000-0000-000000000001"},),
            {},
        )
        assert str(obj.order_id) == "00000000-0000-0000-0000-000000000001"

        obj = self.library.run_keyword(
            "Validate TestModel",
            ({"order_id": "00000000-0000-0000-0000-000000000002"},),
            {},
        )
        assert str(obj.order_id) == "00000000-0000-0000-0000-000000000002"

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create TestModel",
            tuple(),
            {"orderId": "00000000-0000-0000-0000-000000000003"},
        )
        assert str(obj.order_id) == "00000000-0000-0000-0000-000000000003"

        obj = self.library.run_keyword(
            "Create TestModel",
            tuple(),
            {"order_id": "00000000-0000-0000-0000-000000000004"},
        )
        assert str(obj.order_id) == "00000000-0000-0000-0000-000000000004"

    def test_create_keyword_types_include_domain_specific_field_type(self) -> None:
        types = self.library.get_keyword_types("Create TestModel")
        assert types["order_id"].__name__ == "UUID"


class TestValidationAliasPathSupport(_TestBase):
    model = """
    from pydantic import AliasPath, BaseModel, Field

    class AliasInputModel(BaseModel):
        user_id: int = Field(validation_alias=AliasPath("payload", "user", "id"))
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate AliasInputModel",
            ({"payload": {"user": {"id": "41"}}},),
            {},
        )
        assert obj.user_id == 41

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create AliasInputModel",
            tuple(),
            {"payload": {"user": {"id": "42"}}},
        )
        assert obj.user_id == 42


class TestDefaultFactorySupport(_TestBase):
    model = """
    from pydantic import BaseModel, Field

    class LabelledModel(BaseModel):
        notes: str | None = None
        labels: list[str] = Field(default_factory=list)
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword("Validate LabelledModel", ({},), {})
        assert obj.notes is None
        assert obj.labels == []

    def test_create(self) -> None:
        obj = self.library.run_keyword("Create LabelledModel", tuple(), {})
        assert obj.notes is None
        assert obj.labels == []

    def test_create_keyword_arguments_include_optional_and_factory_defaults(
        self,
    ) -> None:
        args = self.library.get_keyword_arguments("Create LabelledModel")

        assert ("notes", None) in args
        assert ("labels", "<factory:list>") in args


class TestExtraAllowSupport(_TestBase):
    model = """
    from pydantic import BaseModel, ConfigDict

    class ExtraAllowModel(BaseModel):
        model_config = ConfigDict(extra="allow")

        id: int
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate ExtraAllowModel",
            ({"id": 1, "customer_segment": "enterprise"},),
            {},
        )
        assert obj.id == 1
        assert obj.model_extra == {"customer_segment": "enterprise"}

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create ExtraAllowModel",
            tuple(),
            {"id": 2, "customer_segment": "startup"},
        )
        assert obj.id == 2
        assert obj.model_extra == {"customer_segment": "startup"}

    def test_create_keyword_arguments_include_extra_kwargs(self) -> None:
        args = self.library.get_keyword_arguments("Create ExtraAllowModel")

        assert args[-1] == "**extra"


class TestExtraForbidSupport(_TestBase):
    model = """
    from pydantic import BaseModel, ConfigDict

    class ExtraForbidModel(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: int
    """

    def test_validate(self) -> None:
        ok = self.library.run_keyword("Validate ExtraForbidModel", ({"id": 1},), {})
        assert ok.id == 1

        with pytest.raises(AssertionError, match="Extra inputs are not permitted"):
            self.library.run_keyword(
                "Validate ExtraForbidModel",
                ({"id": 1, "unexpected": "boom"},),
                {},
            )

    def test_create(self) -> None:
        ok = self.library.run_keyword("Create ExtraForbidModel", tuple(), {"id": 1})
        assert ok.id == 1

        with pytest.raises(AssertionError, match="Extra inputs are not permitted"):
            self.library.run_keyword(
                "Create ExtraForbidModel",
                tuple(),
                {"id": 1, "unexpected": "boom"},
            )


class TestExtraIgnoreSupport(_TestBase):
    model = """
    from pydantic import BaseModel, ConfigDict

    class ExtraIgnoreModel(BaseModel):
        model_config = ConfigDict(extra="ignore")
        id: int
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate ExtraIgnoreModel",
            ({"id": 1, "unexpected": "ignored"},),
            {},
        )
        assert obj.id == 1
        assert not hasattr(obj, "unexpected")

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create ExtraIgnoreModel",
            tuple(),
            {"id": 1, "unexpected": "ignored"},
        )
        assert obj.id == 1
        assert not hasattr(obj, "unexpected")


class TestEnumSupport(_TestBase):
    model = """
    from enum import Enum

    from pydantic import BaseModel

    class Currency(str, Enum):
        USD = "USD"
        EUR = "EUR"

    class Payment(BaseModel):
        currency: Currency
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword("Validate Payment", ({"currency": "USD"},), {})
        assert obj.currency.value == "USD"

    def test_create(self) -> None:
        obj = self.library.run_keyword("Create Payment", tuple(), {"currency": "EUR"})
        assert obj.currency.value == "EUR"

    def test_create_keyword_types_include_enum_type(self) -> None:
        types = self.library.get_keyword_types("Create Payment")

        assert types["currency"].__name__ == "Currency"


class TestStrictTypeSupport(_TestBase):
    model = """
    from pydantic import BaseModel, StrictInt

    class StrictPayload(BaseModel):
        count: StrictInt
    """

    def test_validate(self) -> None:
        ok = self.library.run_keyword("Validate StrictPayload", ({"count": 2},), {})
        assert ok.count == 2

        with pytest.raises(AssertionError, match="Input should be a valid integer"):
            self.library.run_keyword("Validate StrictPayload", ({"count": "2"},), {})

    def test_create(self) -> None:
        ok = self.library.run_keyword("Create StrictPayload", tuple(), {"count": 2})
        assert ok.count == 2

        with pytest.raises(AssertionError, match="Input should be a valid integer"):
            self.library.run_keyword("Create StrictPayload", tuple(), {"count": "2"})


class TestDiscriminatedUnionSupport(_TestBase):
    model = """
    from typing import Literal

    from pydantic import BaseModel, Field

    class CardPayment(BaseModel):
        method: Literal["card"]
        token: str

    class WirePayment(BaseModel):
        method: Literal["wire"]
        iban: str

    class Checkout(BaseModel):
        payment: CardPayment | WirePayment = Field(discriminator="method")
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate Checkout",
            ({"payment": {"method": "card", "token": "tok_123"}},),
            {},
        )
        assert obj.payment.method == "card"

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create Checkout",
            tuple(),
            {"payment": {"method": "wire", "iban": "DE89370400440532013000"}},
        )
        assert obj.payment.method == "wire"

    def test_create_keyword_types_include_discriminated_union_members(self) -> None:
        types = self.library.get_keyword_types("Create Checkout")

        assert "CardPayment" in types["payment"]
        assert "WirePayment" in types["payment"]


class TestNestedModelTypingSupport(_TestBase):
    model = """
    from pydantic import BaseModel

    class LineItem(BaseModel):
        sku: str
        quantity: int

    class PurchaseOrder(BaseModel):
        items: list[LineItem]
    """

    def test_create_keyword_types_include_nested_collection_types(self) -> None:
        types = self.library.get_keyword_types("Create PurchaseOrder")

        assert types["items"] == "list[LineItem]"


class TestRecursiveForwardReferenceSupport(_TestBase):
    model = """
    from __future__ import annotations

    from pydantic import BaseModel, Field

    class TreeNode(BaseModel):
        name: str
        children: list[TreeNode] = Field(default_factory=list)
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate TreeNode",
            ({"name": "root", "children": [{"name": "child", "children": []}]},),
            {},
        )
        assert obj.name == "root"
        assert len(obj.children) == 1
        assert obj.children[0].name == "child"

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create TreeNode",
            tuple(),
            {"name": "root", "children": [{"name": "child", "children": []}]},
        )
        assert obj.name == "root"
        assert len(obj.children) == 1
        assert obj.children[0].name == "child"


class TestGenericModelSupport(_TestBase):
    model = """
    from typing import Generic, TypeVar

    from pydantic import BaseModel

    T = TypeVar("T")

    class Box(BaseModel, Generic[T]):
        value: T

    class IntBox(Box[int]):
        pass
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword("Validate IntBox", ({"value": "7"},), {})
        assert obj.value == 7

    def test_create(self) -> None:
        obj = self.library.run_keyword("Create IntBox", tuple(), {"value": "8"})
        assert obj.value == 8


class TestRootModelSupport(_TestBase):
    model = """
    from pydantic import RootModel

    class IntList(RootModel[list[int]]):
        pass
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword("Validate IntList", ([1, "2", 3],), {})
        assert obj.root == [1, 2, 3]

    def test_create(self) -> None:
        obj = self.library.run_keyword("Create IntList", tuple(), {"root": ["4", 5]})
        assert obj.root == [4, 5]


class TestFieldValidatorSupport(_TestBase):
    model = """
    from pydantic import BaseModel, field_validator

    class ProductCode(BaseModel):
        code: str

        @field_validator("code")
        @classmethod
        def normalize_and_validate(cls, value: str) -> str:
            normalized = value.upper()
            if not normalized.startswith("SKU-"):
                raise ValueError("code must start with 'SKU-'")
            return normalized
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate ProductCode", ({"code": "sku-123"},), {}
        )
        assert obj.code == "SKU-123"

        with pytest.raises(AssertionError, match="code must start with 'SKU-'"):
            self.library.run_keyword("Validate ProductCode", ({"code": "invalid"},), {})

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create ProductCode", tuple(), {"code": "sku-999"}
        )
        assert obj.code == "SKU-999"

        with pytest.raises(AssertionError, match="code must start with 'SKU-'"):
            self.library.run_keyword("Create ProductCode", tuple(), {"code": "invalid"})


class TestModelValidatorBeforeSupport(_TestBase):
    model = """
    from pydantic import BaseModel, model_validator

    class LegacyUser(BaseModel):
        first_name: str
        last_name: str

        @model_validator(mode="before")
        @classmethod
        def parse_legacy_input(cls, data: object) -> object:
            if isinstance(data, dict) and "full_name" in data:
                parts = data["full_name"].split()
                if len(parts) != 2:
                    raise ValueError("full_name must contain first and last name")
                return {"first_name": parts[0], "last_name": parts[1]}
            return data
    """

    def test_validate(self) -> None:
        obj = self.library.run_keyword(
            "Validate LegacyUser",
            ({"full_name": "Ada Lovelace"},),
            {},
        )
        assert obj.first_name == "Ada"
        assert obj.last_name == "Lovelace"

        with pytest.raises(
            AssertionError, match="full_name must contain first and last name"
        ):
            self.library.run_keyword("Validate LegacyUser", ({"full_name": "Ada"},), {})

    def test_create(self) -> None:
        obj = self.library.run_keyword(
            "Create LegacyUser",
            tuple(),
            {"full_name": "Grace Hopper"},
        )
        assert obj.first_name == "Grace"
        assert obj.last_name == "Hopper"

        with pytest.raises(
            AssertionError, match="full_name must contain first and last name"
        ):
            self.library.run_keyword(
                "Create LegacyUser", tuple(), {"full_name": "Grace"}
            )


class TestModelValidatorAfterSupport(_TestBase):
    model = """
    from datetime import datetime

    from pydantic import BaseModel, model_validator

    class DateWindow(BaseModel):
        start: datetime
        end: datetime

        @model_validator(mode="after")
        def validate_order(self) -> "DateWindow":
            if self.end <= self.start:
                raise ValueError("end must be after start")
            return self
    """

    def test_validate(self) -> None:
        ok = self.library.run_keyword(
            "Validate DateWindow",
            ({"start": "2026-02-01T00:00:00Z", "end": "2026-03-01T00:00:00Z"},),
            {},
        )
        assert ok.end > ok.start

        with pytest.raises(AssertionError, match="end must be after start"):
            self.library.run_keyword(
                "Validate DateWindow",
                ({"start": "2026-03-01T00:00:00Z", "end": "2026-02-01T00:00:00Z"},),
                {},
            )

    def test_create(self) -> None:
        ok = self.library.run_keyword(
            "Create DateWindow",
            tuple(),
            {"start": "2026-02-01T00:00:00Z", "end": "2026-03-01T00:00:00Z"},
        )
        assert ok.end > ok.start

        with pytest.raises(AssertionError, match="end must be after start"):
            self.library.run_keyword(
                "Create DateWindow",
                tuple(),
                {"start": "2026-03-01T00:00:00Z", "end": "2026-02-01T00:00:00Z"},
            )
