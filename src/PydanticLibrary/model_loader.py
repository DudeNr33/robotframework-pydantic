from __future__ import annotations

import importlib
import importlib.util
import inspect
import re
import sys
from pathlib import Path
from types import ModuleType

from pydantic import BaseModel


def load_models_module(models: str) -> ModuleType:
    path = Path(models)
    if path.exists():
        if path.suffix != ".py":
            raise ValueError(f"Model file must be a .py file: {models}")
        return load_module_from_path(path)

    if path.is_absolute() or path.suffix == ".py":
        raise FileNotFoundError(
            f"Model file does not exist: {models}. "
            "Use a valid .py file path or a Python module import path."
        )

    return importlib.import_module(models)


def load_module_from_path(path: Path) -> ModuleType:
    resolved = path.resolve()
    safe_stem = sanitize_module_stem(resolved.stem)
    module_name = f"robotframework_pydantic_models__{safe_stem}"

    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from path: {resolved}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def sanitize_module_stem(stem: str) -> str:
    sanitized = re.sub(r"\W", "_", stem).strip("_")
    if not sanitized:
        return "models"
    if sanitized[0].isdigit():
        return f"_{sanitized}"
    return sanitized


def discover_pydantic_models(module: ModuleType) -> dict[str, type[BaseModel]]:
    models: dict[str, type[BaseModel]] = {}

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if not issubclass(obj, BaseModel) or obj is BaseModel:
            continue

        if obj.__module__ != module.__name__:
            continue

        models[name] = obj

    return models
