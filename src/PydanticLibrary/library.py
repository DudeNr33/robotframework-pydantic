from __future__ import annotations

import importlib
import importlib.util
import inspect
import re
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_origin

from pydantic import BaseModel, ValidationError


class PydanticLibrary:
    """Robot Framework library for working with Pydantic models.

    Example:
        *** Settings ***
        Library    PydanticLibrary    models=${CURDIR}/models.py

        *** Test Cases ***
        Validate Model
            &{item}=    product_id=101    name=Apple    quantity=3    unit_price=0.50
            &{data}=    cart_id=1    customer_name=Alice    items=[${item}]
            Validate ShoppingCart    ${data}

        Create Object
            ${obj}=    Create ShoppingCart    cart_id=1    customer_name=Alice    items=[${item}]
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_VERSION = "0.1.0"

    def __init__(self, models: str) -> None:
        """Configure the library with the Pydantic models to expose.

        ``models`` can be either:
        - a path to a Python file (``/path/to/models.py``)
        - a Python module import path (``my_project.models``)

        All classes in the given module that inherit from ``pydantic.BaseModel``
        are discovered automatically and exposed as dynamic ``Validate <ModelName>``
        and ``Create <ModelName>`` keywords.

        Raises ``ValueError`` if no ``BaseModel`` subclasses are found.
        """
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
        keywords = []
        for name in sorted(self._models):
            keywords.append(f"Validate {name}")
            keywords.append(f"Create {name}")
        return keywords

    def run_keyword(
        self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any] | None = None
    ) -> Any:
        kwargs = kwargs or {}

        model_name = self._extract_model_name_from_validate_keyword(name)
        if model_name is not None:
            return self._validate_model(model_name, args, kwargs)

        model_name = self._extract_model_name_from_create_keyword(name)
        if model_name is not None:
            return self._create_model(model_name, args, kwargs)

        raise AttributeError(f"Unknown keyword: {name}")

    def get_keyword_arguments(self, name: str) -> list[Any]:
        model_name = self._extract_model_name_from_validate_keyword(name)
        if model_name is not None:
            return ["data"]

        model_name = self._extract_model_name_from_create_keyword(name)
        if model_name is not None:
            model_cls = self._get_model(model_name)
            return self._build_create_keyword_arguments(model_cls)

        return ["*args", "**kwargs"]

    def get_keyword_types(self, name: str) -> dict[str, Any]:
        model_name = self._extract_model_name_from_validate_keyword(name)
        if model_name is not None:
            model_cls = self._get_model(model_name)
            return {"data": dict, "return": model_cls}

        model_name = self._extract_model_name_from_create_keyword(name)
        if model_name is not None:
            model_cls = self._get_model(model_name)
            types: dict[str, Any] = {"extra": Any, "return": model_cls}
            for field_name, field_info in model_cls.model_fields.items():
                types[field_name] = self._type_for_argument_conversion(
                    field_info.annotation
                )
            return types

        return {}

    def get_keyword_documentation(self, name: str) -> str:
        if name == "__intro__":
            return (
                "Library for validating and creating Pydantic models from Robot Framework. "
                "Provide `models` as a Python module path or a path to a .py file. "
                "Each discovered model is exposed as a ``Validate <ModelName>`` and a "
                "``Create <ModelName>`` keyword."
            )

        model_name = self._extract_model_name_from_validate_keyword(name)
        if model_name is not None:
            return (
                f"Validate ``data`` against the ``{model_name}`` Pydantic model and "
                f"return the validated model instance.\n\n"
                f"``data`` must be a dictionary (or any mapping) whose keys match the "
                f"fields of ``{model_name}``. Raises ``AssertionError`` on validation "
                f"failure with a detailed Pydantic error message.\n\n"
                f"Example:\n"
                f"    ${{obj}}=    Validate {model_name}    ${{data}}"
            )

        model_name = self._extract_model_name_from_create_keyword(name)
        if model_name is not None:
            return (
                f"Create and return an instance of ``{model_name}`` from named fields.\n\n"
                f"Use named arguments matching the model field names."
            )

        return ""

    # -----------------------------
    # Keyword implementations
    # -----------------------------
    def _validate_model(
        self, model_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> BaseModel:
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(
                f"Validate {model_name} accepts only a single positional data argument. "
                f"Unexpected keyword arguments: {unexpected}"
            )

        if len(args) != 1:
            raise TypeError(
                f"Validate {model_name} requires exactly one positional argument."
            )

        model_cls = self._get_model(model_name)

        try:
            return model_cls.model_validate(args[0])
        except ValidationError as exc:
            raise AssertionError(
                f"Validation failed for model '{model_cls.__name__}':\n{exc}"
            ) from exc

    def _create_model(
        self, model_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> BaseModel:
        if args:
            raise TypeError(
                f"Create {model_name} accepts only named arguments matching model fields."
            )

        model_cls = self._get_model(model_name)

        try:
            return model_cls.model_validate(kwargs)
        except ValidationError as exc:
            raise AssertionError(
                f"Creation failed for model '{model_cls.__name__}':\n{exc}"
            ) from exc

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _build_create_keyword_arguments(self, model_cls: type[BaseModel]) -> list[Any]:
        arguments: list[Any] = ["*"]

        for field_name, field_info in model_cls.model_fields.items():
            if field_info.is_required():
                arguments.append(field_name)
                continue

            if field_info.default_factory is not None:
                factory_name = getattr(
                    field_info.default_factory,
                    "__name__",
                    repr(field_info.default_factory),
                )
                arguments.append((field_name, f"<factory:{factory_name}>"))
                continue

            arguments.append((field_name, field_info.default))

        # Keep support for models that allow extra fields.
        arguments.append("**extra")
        return arguments

    def _type_for_argument_conversion(self, annotation: Any) -> Any:
        if annotation is Any:
            return Any

        origin = get_origin(annotation)
        if origin is None:
            if isinstance(annotation, type):
                return annotation
            return self._format_annotation(annotation)

        # Keep full generic type information for Libdoc/IntelliSense.
        return self._format_annotation(annotation)

    def _format_annotation(self, annotation: Any) -> str:
        if annotation is Any:
            return "Any"

        origin = get_origin(annotation)
        if origin is None:
            if isinstance(annotation, type):
                return annotation.__name__

            text = str(annotation)
            if text.startswith("typing."):
                text = text.removeprefix("typing.")
            return text.replace("NoneType", "None")

        args = get_args(annotation)

        if origin is list:
            return f"list[{self._format_annotation(args[0])}]"
        if origin is dict:
            return (
                f"dict[{self._format_annotation(args[0])}, "
                f"{self._format_annotation(args[1])}]"
            )
        if origin is tuple:
            return f"tuple[{', '.join(self._format_annotation(arg) for arg in args)}]"
        if origin is set:
            return f"set[{self._format_annotation(args[0])}]"

        origin_name = getattr(origin, "__name__", str(origin).replace("typing.", ""))

        if origin_name in {"UnionType", "Union"}:
            return " | ".join(self._format_annotation(arg) for arg in args)

        if args:
            rendered_args = ", ".join(self._format_annotation(arg) for arg in args)
            return f"{origin_name}[{rendered_args}]"

        return origin_name

    def _extract_model_name_from_validate_keyword(
        self, keyword_name: str
    ) -> str | None:
        prefix = "validate "
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
            f"Unknown model '{model_name}'. Available models: {', '.join(sorted(self._models))}"
        )

    def _load_module(self, models: str) -> ModuleType:
        path = Path(models)
        if path.exists():
            if path.suffix != ".py":
                raise ValueError(f"Model file must be a .py file: {models}")
            return self._load_module_from_path(path)

        if path.is_absolute() or path.suffix == ".py":
            raise FileNotFoundError(
                f"Model file does not exist: {models}. "
                "Use a valid .py file path or a Python module import path."
            )

        return importlib.import_module(models)

    def _load_module_from_path(self, path: Path) -> ModuleType:
        resolved = path.resolve()
        safe_stem = self._sanitize_module_stem(resolved.stem)
        module_name = f"robotframework_pydantic_models__{safe_stem}"

        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec from path: {resolved}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _sanitize_module_stem(self, stem: str) -> str:
        sanitized = re.sub(r"\W", "_", stem).strip("_")
        if not sanitized:
            return "models"
        if sanitized[0].isdigit():
            return f"_{sanitized}"
        return sanitized

    def _discover_models(self, module: ModuleType) -> dict[str, type[BaseModel]]:
        models: dict[str, type[BaseModel]] = {}

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, BaseModel) or obj is BaseModel:
                continue

            if obj.__module__ != module.__name__:
                continue

            models[name] = obj

        return models
