# robotframework-pydantic

Robot Framework keyword library for validating data with Pydantic models and creating model objects dynamically.

## Usage

```robot
*** Settings ***
Library    PydanticLibrary    models=${CURDIR}/models.py

*** Test Cases ***
Validate Schema
    &{item}=    Create Dictionary    product_id=101    name=Apple    quantity=3    unit_price=0.50
    @{items}=    Create List    ${item}
    &{data}=    Create Dictionary    cart_id=1    customer_name=Alice    items=${items}
    Pydantic.Validate Schema    ${data}    schema=ShoppingCart

Create Object
    ${obj}=    Pydantic.Create ShoppingCart    cart_id=1    customer_name=Alice    items=${items}
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
