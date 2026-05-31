from pydantic import BaseModel


class ImportedModel(BaseModel):
    value: int
