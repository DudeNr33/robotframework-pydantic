*** Settings ***
Documentation       Acceptance tests for PydanticLibrary.
Library     PydanticLibrary    models=${CURDIR}/models.py


*** Test Cases ***
Validate Schema With Dictionary
    [Documentation]    Validate that a dictionary conforms to a Pydantic schema.
    VAR    &{data}=    foo=1    bar=test
    Validate Schema    ${data}    schema=FooBar

Validation Failure Raises Error
    [Documentation]    Verify that schema validation raises an error on invalid data.
    VAR    &{data}=    foo=nope    bar=test
    Run Keyword And Expect Error
    ...    *Validation failed*
    ...    Validate Schema
    ...    ${data}
    ...    schema=FooBar

Create Object With Dynamic Keyword
    [Documentation]    Create a Pydantic model instance via a dynamic keyword.
    ${obj}=    Create FooBar    foo=2    bar=value
    Should Be Equal As Integers    ${obj.foo}    2
    Should Be Equal    ${obj.bar}    value
