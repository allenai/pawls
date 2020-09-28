
from typing import Optional, List
from pydantic import BaseModel


class Bounds(BaseModel):
    left: float
    top: float
    right: float
    bottom: float


class Label(BaseModel):
    text: str
    color: str


class TokenId(BaseModel):
    pageIndex: int
    tokenIndex: int


class Annotation(BaseModel):
    page: int
    label: Label
    bounds: Bounds
    tokens: Optional[List[TokenId]] = None
