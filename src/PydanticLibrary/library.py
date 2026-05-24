from __future__ import annotations

import importlib
import importlib.util
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from pydantic import BaseModel, ValidationError


class PydanticLibrary:
    """Robot Framework library for working with Pydantic models.

    Example:
        *** Settings ***
        Library    PydanticLibrary    models=${CURDIR}/models.py

        *** Test Cases ***
        Validate Schema
            &{data}=    foo=1    bar=test
            Validate Schema    ${data}    schema=FooBar

        Create Object
            ${obj}=    Create FooBar    foo=1    bar=test
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "0.1.0"

    def __init__(self, models: str) -> None:
        if not models:
            raise ValueError(
                "'models' argument is required (module path or .py file path)."
            )

        self._models_source = models
        self._module = self._load_module(models)
        self._models = self._discover_models(self._module)

        if not self._models:
            raise ValueError(f"No Pydantic BaseModel subclasses found in '{models}'.")

    # -----------------------------
    # Dynamic library API
    # -----------------------------
    def get_keyword_names(self) -> list[str]:
        return ["Validate Schema", *[f"Create {name}" for name in sorted(self._models)]]

    def run_keyword(
        self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any] | None = None
    ) -> Any:
        kwargs = kwargs or {}

        if name.lower() == "validate schema":
            return self._validate_schema(args, kwargs)

        model_name = self._extract_model_name_from_create_keyword(name)
        if model_name is not None:
            return self._create_model(model_name, args, kwargs)

        raise AttributeError(f"Unknown keyword: {name}")

    def get_keyword_arguments(self, name: str) -> list[str]:
        if name.lower() == "validate schema":
            return ["data", "schema=None"]

        if self._extract_model_name_from_create_keyword(name) is not None:
            return ["*data", "**fields"]

        return ["*args", "**kwargs"]

    def get_keyword_documentation(self, name: str) -> str:
        if name == "__intro__":
            return (
                "Library for validating and creating Pydantic models from Robot Framework. "
                "Provide `models` as a Python module path or a path to a .py file."
            )

        if name.lower() == "validate schema":
            return (
                "Validate an input object against a schema.\n\n"
                "Examples:\n"
                "- Validate Schema    ${data}    schema=FooBar\n"
                "- Validate Schema    ${data}    FooBar"
            )

        model_name = self._extract_model_name_from_create_keyword(name)
        if model_name is not None:
            return (
                f"Create and return an instance of `{model_name}` from provided fields."
            )

        return ""

    # -----------------------------
    # Keyword implementations
    # -----------------------------
    def _validate_schema(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> BaseModel:
        schema_name = kwargs.pop("schema", None)
        payload_args = args

        if schema_name is None and len(args) >= 2:
            schema_name = args[1]
            payload_args = (args[0],)

        if schema_name is None:
            raise TypeError(
                "'schema' is required. Example: Validate Schema    ${data}    schema=FooBar"
            )

        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(
                "Validate Schema accepts only the input object plus schema. "
                f"Unexpected keyword arguments: {unexpected}"
            )

        if len(payload_args) != 1:
            raise TypeError(
                "Validate Schema requires exactly one input object as positional argument."
            )

        model_cls = self._get_model(str(schema_name))
        payload = payload_args[0]

        try:
            return model_cls.model_validate(payload)
        except ValidationError as exc:
            raise AssertionError(
                f"Validation failed for schema '{model_cls.__name__}':\n{exc}"
            ) from exc

    def _create_model(
        self, model_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> BaseModel:
        model_cls = self._get_model(model_name)
        payload = self._extract_payload(args=args, kwargs=kwargs)

        try:
            return model_cls.model_validate(payload)
        except ValidationError as exc:
            raise AssertionError(
                f"Creation failed for model '{model_cls.__name__}':\n{exc}"
            ) from exc

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _extract_payload(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        # Accept one positional mapping/object, or field kwargs, or a merge of both.
        if len(args) > 0:
            first = args[0]

            if len(args) > 1:
                raise TypeError("Too many positional arguments provided.")

            if isinstance(first, Mapping):
                data = dict(first)
                if kwargs:
                    data.update(kwargs)
                return data

            if kwargs:
                raise TypeError(
                    "Cannot combine non-mapping positional data with keyword fields."
                )

            return first

        return kwargs

    def _extract_model_name_from_create_keyword(self, keyword_name: str) -> str | None:
        prefix = "create "
        if not keyword_name.lower().startswith(prefix):
            return None

        requested = keyword_name[len(prefix) :].strip()
        if not requested:
            return None

        for existing_name in self._models:
            if existing_name.lower() == requested.lower():
                return existing_name

        raise AttributeError(
            f"Unknown model '{requested}' in keyword '{keyword_name}'. "
            f"Available models: {', '.join(sorted(self._models))}"
        )

    def _get_model(self, model_name: str) -> type[BaseModel]:
        for existing_name, model_cls in self._models.items():
            if existing_name.lower() == model_name.lower():
                return model_cls

        raise ValueError(
            f"Unknown schema/model '{model_name}'. Available models: {', '.join(sorted(self._models))}"
        )

    def _load_module(self, models: str) -> ModuleType:
        path = Path(models)
        if path.exists():
            if path.suffix != ".py":
                raise ValueError(f"Model file must be a .py file: {models}")
            return self._load_module_from_path(path)

        return importlib.import_module(models)

    def _load_module_from_path(self, path: Path) -> ModuleType:
        resolved = path.resolve()
        module_name = f"robotframework_pydantic_models_{abs(hash(str(resolved)))}"

        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec from path: {resolved}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _discover_models(self, module: ModuleType) -> dict[str, type[BaseModel]]:
        models: dict[str, type[BaseModel]] = {}

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, BaseModel) or obj is BaseModel:
                continue

            if obj.__module__ != module.__name__:
                continue

            models[name] = obj

        return models
