*** Settings ***
Documentation       Acceptance tests for PydanticLibrary.

Library             PydanticLibrary    models=${CURDIR}/models.py


*** Test Cases ***
Validate Schema With Nested Models
    [Documentation]    Validate that a dictionary with nested models conforms to a Pydantic schema.
    VAR    &{item}=    product_id=101    name=Apple    quantity=3    unit_price=0.50
    VAR    @{items}=    ${item}
    VAR    &{data}=    cart_id=1    customer_name=Alice    items=${items}
    Validate Schema    ${data}    schema=ShoppingCart

Validation Failure On Nested Field
    [Documentation]    Verify that schema validation raises an error when a nested field is invalid.
    VAR    &{item}=    product_id=101    name=Apple    quantity=not-a-number    unit_price=0.50
    VAR    @{items}=    ${item}
    VAR    &{data}=    cart_id=1    customer_name=Alice    items=${items}
    Run Keyword And Expect Error
    ...    *Validation failed*
    ...    Validate Schema
    ...    ${data}
    ...    schema=ShoppingCart

Create Object With Nested Models
    [Documentation]    Create a Pydantic model instance with nested models via a dynamic keyword.
    VAR    &{item}=    product_id=202    name=Banana    quantity=5    unit_price=1.20
    VAR    @{items}=    ${item}
    ${obj}=    Create ShoppingCart    cart_id=2    customer_name=Bob    items=${items}
    Should Be Equal As Integers    ${obj.cart_id}    2
    Should Be Equal    ${obj.customer_name}    Bob
    VAR    ${first_item}=    ${obj.items}[0]
    Should Be Equal As Integers    ${first_item.product_id}    202
    Should Be Equal    ${first_item.name}    Banana
    Should Be Equal As Integers    ${first_item.quantity}    5
    Should Be Equal As Numbers    ${first_item.unit_price}    1.2

Create Nested Model Directly
    [Documentation]    Create a nested model instance directly via its dynamic keyword.
    ${item}=    Create CartItem    product_id=303    name=Carrot    quantity=10    unit_price=0.30
    Should Be Equal As Integers    ${item.product_id}    303
    Should Be Equal    ${item.name}    Carrot
    Should Be Equal As Integers    ${item.quantity}    10
    Should Be Equal As Numbers    ${item.unit_price}    0.3
