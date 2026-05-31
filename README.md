# robotframework-pydantic

Robot Framework keyword library for validating data with Pydantic models and creating model objects dynamically.

## Usage

```robot
*** Settings ***
Library    PydanticLibrary    models=${CURDIR}/models.py

*** Test Cases ***
Validate Model
    &{item}=    Create Dictionary    product_id=101    name=Apple    quantity=3    unit_price=0.50
    @{items}=    Create List    ${item}
    &{data}=    Create Dictionary    cart_id=1    customer_name=Alice    items=${items}
    ${cart}=    Validate ShoppingCart    ${data}

Create Object
    ${obj}=    Create ShoppingCart    cart_id=1    customer_name=Alice    items=${items}
    Log    ${obj}
```

## Model source

`models` can be either:

- a path to a Python file (`/path/to/models.py`)
- a Python module import path (`my_project.models`)

All classes in that module inheriting from `pydantic.BaseModel` are exposed as dynamic `Validate <ModelName>` and `Create <ModelName>` keywords.

## Run tests

```bash
# Unit/integration tests
uv run pytest

# Robot acceptance tests
uv run robot --pythonpath src tests/acceptance
```
