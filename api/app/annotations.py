
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
    id: str
    page: int
    label: Label
    bounds: Bounds
    tokens: Optional[List[TokenId]] = None


class RelationGroup(BaseModel):
    source: List[str]
    target: List[str]
    label: Label


class PdfAnnotation(BaseModel):
    annotations: List[Annotation]
