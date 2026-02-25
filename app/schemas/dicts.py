from pydantic import BaseModel


class DictItemOut(BaseModel):
    value: str
    label: str


class DictItemsData(BaseModel):
    dictType: str
    items: list[DictItemOut]
