from pydantic import BaseModel


class FooBar(BaseModel):
    foo: int
    bar: str


class User(BaseModel):
    id: int
    name: str
