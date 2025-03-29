from pydantic import BaseModel

class DictionaryBase(BaseModel):
    name: str

class DictionaryCreate(DictionaryBase):
    """Схема для створення довідника."""
    pass

class DictionaryRead(DictionaryBase):
    id: int

    class Config:
        orm_mode = True