# robotframework-pydantic

Robot Framework keyword library for validating data with Pydantic models and creating model objects dynamically.

## Usage

```robot
*** Settings ***
Library    Pydantic    models=${CURDIR}/models.py

*** Test Cases ***
Validate Schema
    &{data}=    Create Dictionary    foo=1    bar=test
    Pydantic.Validate Schema    ${data}    schema=FooBar

Create Object
    ${obj}=    Pydantic.Create FooBar    foo=1    bar=test
    Log    ${obj}
```

## Model source

`models` can be either:
- a path to a Python file (`/path/to/models.py`)
- a Python module import path (`my_project.models`)

All classes in that module inheriting from `pydantic.BaseModel` are exposed as dynamic `Create <ModelName>` keywords.

## Run tests

```bash
uv run pytest
```
