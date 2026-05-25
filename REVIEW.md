# Review: `robotframework-pydantic` Library

## 🔴 Category 1 — Compliance & Legal

### 1.1 No LICENSE file

There is no `LICENSE` file anywhere in the repository. Without one, the code is legally "all rights reserved" by default. No one can legally use, modify, or redistribute it. This is the single most blocking issue for any public or shared library.

---

## 🔴 Category 2 — Critical Documentation Issues

### 2.1 README uses the wrong library name

The README example shows:

```robot
Library    Pydantic    models=${CURDIR}/models.py
```

The actual importable name is `PydanticLibrary`. Using `Pydantic` would require a `WITH NAME` alias. The acceptance test in `test.robot` correctly uses `PydanticLibrary`, so the README is simply wrong. A new user copying from the README will get an import error immediately.

### 2.2 `pyproject.toml` still has a placeholder description

```toml
description = "Add your description here"
```

This is the scaffolding default and was never filled in. It would appear on PyPI exactly like this.

### 2.3 `__init__` has no docstring — libdoc shows Python's default

The `PydanticLibrary.__init__` has no docstring, so `libdoc`/IDE integrations display:
> *"Initialize self. See help(type(self)) for accurate signature."*

Users reading the generated library documentation get no guidance on the `models` argument, what values it accepts, or what errors to expect.

### 2.4 `Validate Schema` documentation omits the return value

The keyword silently returns the fully validated Pydantic model instance, which is actually very useful (callers can assign it and inspect fields). The documentation says nothing about this. Users will either miss the feature entirely or be confused when they get back an object.

### 2.5 `Create <Model>` keywords document nothing about the model's fields

The generated docstring is:
> *"Create and return an instance of `CartItem` from provided fields."*

There is no information about which fields are required, which are optional, their types, or their defaults. A user looking at this in their IDE or in the libdoc HTML page has no idea what to pass. Pydantic's own model schema (`model_fields`, `model_json_schema`) could be used to enrich these docs at library-init time.

---

## 🟠 Category 3 — User-Facing API & Usability Issues

### 3.1 `schema` argument falsely advertised as optional

`get_keyword_arguments` returns `['data', 'schema=None']`, making `schema` look optional in every IDE auto-complete and in libdoc. At runtime it is mandatory — omitting it raises a `TypeError`. The default of `None` exists to support passing it as a second positional argument, but that internal flexibility should not leak into the public API signature.

### 3.2 `Create <Model>` signature `(*data, **fields)` is misleading

The declared arguments `*data, **fields` suggest the keyword accepts any number of positional arguments, but the implementation rejects anything beyond one. The real contract is `[data] | **fields | (data, **fields)` — this is impossible to represent with a static signature, but the current signature actively misleads users and IDEs. At minimum the argument declaration should be `[data=None], **fields` and the documentation should clarify the accepted call patterns.

### 3.3 Misleading error message for a non-existent `.py` file path

If a user types a path that does not exist:

```
Library    PydanticLibrary    models=/typo/path/models.py
```

The code falls through (because `Path(...).exists()` is `False`) and tries `importlib.import_module('/typo/path/models')`, producing:

```
ModuleNotFoundError: No module named '/typo/path/models'
```

This is deeply confusing. The path looks like a file path but the error talks about a module. A simple check — *"this looks like a file path (absolute or ends in `.py`) but the file doesn't exist"* — would give a much clearer error.

### 3.4 Dynamic module hash name leaks into error messages and `repr`

When a model file is loaded from a path, the module is internally named `robotframework_pydantic_models_<hash>`. This name appears in:

- `type(result)` → `<class 'robotframework_pydantic_models_454954538087940414.ShoppingCart'>`
- `type(result).__module__`
- Pydantic `ValidationError` messages

This is confusing for users debugging failures. Using the original file's stem as the module name (e.g., `robotframework_pydantic_models__models`) would be far more readable.

### 3.5 No JSON string input support

`Validate Schema` only accepts a Python dict/mapping. There is no way to pass a JSON string directly, even though Pydantic's `model_validate_json()` supports this natively and it is a very common use case (e.g., validating an API response body received as a string).

### 3.6 Asymmetric keyword design: no per-model `Validate <ModelName>`

The library exposes `Create CartItem` and `Create ShoppingCart` per model, but only one generic `Validate Schema` for all models. Users have to remember and type the model name as a string argument every time. A `Validate CartItem` / `Validate ShoppingCart` pattern — analogous to the `Create` keywords — would be more consistent, IDE-friendly, and self-documenting.

### 3.7 Silent collision on case-insensitive model name lookup

Both `_get_model` and `_extract_model_name_from_create_keyword` do case-insensitive matching using a linear scan over `dict.items()`. If a models file defines `User` and `USER`, both are registered as distinct keywords (`Create User`, `Create USER`), but `Validate Schema ... schema=user` silently resolves to whichever appears first in iteration order. This should either raise an error at init time or at lookup time.

### 3.8 No support for Pydantic v2 features

The library is Pydantic v2-only (which is fine) but exposes almost none of its power:

- No `strict` mode support
- No `context` passing for custom validators
- No `model_dump` / `model_dump_json` keywords for serialization
- No access to the JSON schema (`model_json_schema`)

Given the library's purpose is to bridge Pydantic and Robot Framework, these omissions make it feel incomplete for anything beyond basic validation.

---

## 🟡 Category 4 — Developer / Contributor Experience

### 4.1 `robot.toml` has `python-path` commented out

```toml
# python-path = ["src/"]
```

Running `robot tests/acceptance/` directly (without going through `pytest`) fails because `src/` is not on the Python path. New contributors will be confused. Either uncomment the line or add a note in the README.

### 4.2 Robot Framework output artifacts committed to the repository root

`log.html`, `output.xml`, and `report.html` are sitting in the repository root and are not covered by `.gitignore` (which only ignores `results/`). These should either be moved to `results/` (already gitignored) or the gitignore should be extended.

### 4.3 No CI configuration

Continuous Integration is now configured via GitHub Actions:

- `.github/workflows/test.yml` runs linting (`ruff check`, `ruff format --check`) and tests (`pytest`) using `uv`.
- Tests run on Python 3.11, 3.12, and 3.13.
- `.github/workflows/publish.yml` builds distributions and runs smoke tests against both wheel and source distribution before publishing.

### 4.4 `exclude-newer = "7 days"` is a floating dependency window

```toml
[tool.uv]
exclude-newer = "7 days"
```

This means "only consider packages published up to 7 days ago relative to *now*". Running `uv lock` on different days will produce different results. The `uv.lock` file is committed (good) so reproducibility is preserved for locked installs, but any `uv lock --upgrade` or fresh install on a new machine will resolve against a different package universe. A fixed ISO date (as uv normally uses) is the standard practice.

### 4.5 Dev environment pins Python 3.14 but declared support starts at 3.11

`.python-version` pins `3.14`, which is pre-release / very new. `pyproject.toml` declares `>=3.11`. Contributors running 3.11, 3.12 or 3.13 may hit unexpected issues, and there is no CI matrix to verify compatibility across the supported range.

### 4.6 `pydantic>=2.13.4` and `robotframework>=7.4.2` are very tight lower bounds

These pin to specific very recent patch releases. Users on e.g. `pydantic==2.10` or `robotframework==7.0` will be rejected by the dependency resolver, even though the library likely works fine with those versions. The bounds should be set at a meaningful compatibility boundary (e.g., `pydantic>=2.0`, `robotframework>=6.0`) unless there is a documented reason for the specific pins.

### 4.7 No CHANGELOG or CONTRIBUTING guide

There is no `CHANGELOG.md` to track what changed between versions and no `CONTRIBUTING.md` to tell contributors how to set up the environment, run tests, or submit changes.

---

## 🟡 Category 5 — Test Coverage Gaps

### 5.1 Acceptance tests cover only the happy path with one simple model

The acceptance suite uses a single `ShoppingCart` / `CartItem` model pair. There are no acceptance tests for: optional fields, fields with defaults, Pydantic validators/`@field_validator`, aliased fields, discriminated unions, or `model_config` customisations. Any of these could reveal edge cases in how the library feeds data to `model_validate`.

### 5.2 No test for the module-import-path form

Both test files use a `.py` file path. The `models = "my_project.models"` module-import form is completely untested.

### 5.3 Unit tests test only one call convention for `Create <Model>`

`test_create_dynamic_keyword_returns_model_instance` always passes a single dict. There is no unit test for the `**fields` (individual kwargs) calling convention, or for the mixed dict+kwargs case.

### 5.4 Error paths in the test suite are under-represented

There are no tests for: non-existent file path, non-`.py` file, a module that contains no Pydantic models, or a module path that doesn't exist. These are all branches that exist in the implementation but are not tested.

---

## ⚪ Category 6 — Minor / Naming

### 6.1 `Validate Schema` keyword name is Pydantic-agnostic but the library isn't

"Schema" is a generic term. Since the library is specifically about Pydantic, `Validate Model` or even per-model `Validate <ModelName>` (see 3.6) would be more precise and consistent with Pydantic's own vocabulary (`BaseModel`, `model_validate`).

### 6.2 The `schema` parameter would be better named `model`

Pydantic uses "model" consistently (`BaseModel`, `model_validate`, `model_fields`). The `schema` argument name in `Validate Schema    ${data}    schema=ShoppingCart` mixes Pydantic's "model" concept with JSON Schema terminology.

### 6.3 `ROBOT_LIBRARY_VERSION` is hardcoded and will drift

`ROBOT_LIBRARY_VERSION = "0.1.0"` is a hardcoded string that must be kept in sync with `pyproject.toml` manually. This commonly drifts. The standard pattern is to read it from the package metadata at import time:

```python
from importlib.metadata import version
ROBOT_LIBRARY_VERSION = version("robotframework-pydantic")
```

---

### Summary Table

| # | Area | Severity | State |
| - | ---- | -------- | ----- |
| 1.1 | No LICENSE file | 🔴 Critical | ✅ Fixed |
| 2.1 | Wrong library name in README | 🔴 Critical | ✅ Fixed |
| 2.2 | Placeholder description in `pyproject.toml` | 🔴 Critical | ✅ Fixed |
| 2.3 | No `__init__` docstring | 🟠 High | ✅ Fixed |
| 2.4 | `Validate Schema` return value undocumented | 🟠 High | ✅ Fixed |
| 2.5 | `Create <Model>` docs missing field info | 🟠 High | ✅ Fixed |
| 3.1 | `schema` falsely optional in signature | 🟠 High | 🚫 Obsolete |
| 3.2 | `*data, **fields` signature misleads IDEs | 🟠 High | 🚫 Obsolete |
| 3.3 | Misleading error for non-existent file path | 🟠 High | ✅ Fixed |
| 3.4 | Hash module name leaks into errors/repr | 🟡 Medium | ✅ Fixed |
| 3.5 | No JSON string input support | 🟡 Medium | 🔓 Open |
| 3.6 | No per-model `Validate <ModelName>` | 🟡 Medium | ✅ Fixed |
| 3.7 | Silent collision on case-insensitive name clash | 🟡 Medium | 🔓 Open |
| 3.8 | Pydantic v2 features largely unexposed | 🟡 Medium | 🔓 Open |
| 4.1 | `robot.toml` python-path commented out | 🟡 Medium | ✅ Fixed |
| 4.2 | Artifact HTML/XML files committed to root | 🟡 Medium | 🚫 False positive |
| 4.3 | No CI configuration | 🟡 Medium | ✅ Fixed |
| 4.4 | Floating `exclude-newer = "7 days"` | 🟡 Medium | 🚫 False positive |
| 4.5 | Dev pins Python 3.14, supports 3.11+ | 🟡 Medium | 🔓 Open |
| 4.6 | Over-tight minimum dependency versions | 🟡 Medium | 🔓 Open |
| 4.7 | No CHANGELOG or CONTRIBUTING guide | 🟡 Medium | 🔓 Open |
| 5.1 | Acceptance tests cover only one simple happy-path model | 🟡 Medium | 🔓 Open |
| 5.2 | No test for the module-import-path form | 🟡 Medium | ✅ Fixed |
| 5.3 | Unit tests cover only one `Create <Model>` call convention | 🟡 Medium | ✅ Fixed |
| 5.4 | Error paths under-represented in tests | 🟡 Medium | ✅ Fixed |
| 6.1 | `Validate Schema` name is Pydantic-agnostic | ⚪ Low | 🚫 Obsolete |
| 6.2 | `schema` parameter would be better named `model` | ⚪ Low | 🚫 Obsolete |
| 6.3 | `ROBOT_LIBRARY_VERSION` hardcoded, will drift | ⚪ Low | ✅ Fixed |
