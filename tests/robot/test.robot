*** Settings ***
Library     PydanticLibrary    models=${CURDIR}/models.py


*** Test Cases ***
Validate Schema With Dictionary
    VAR    &{data}=    foo=1    bar=test
    ${obj}=    PydanticLibrary.Validate Schema    ${data}    schema=FooBar
    Should Be Equal As Integers    ${obj.foo}    1
    Should Be Equal    ${obj.bar}    test

Validation Failure Raises Error
    Run Keyword And Expect Error
    ...    *Validation failed*
    ...    PydanticLibrary.Validate Schema
    ...    schema=FooBar
    ...    foo=nope
    ...    bar=x

Create Object With Dynamic Keyword
    ${obj}=    PydanticLibrary.Create FooBar    foo=2    bar=value
    Should Be Equal As Integers    ${obj.foo}    2
    Should Be Equal    ${obj.bar}    value
