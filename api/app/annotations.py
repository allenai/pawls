from typing import Optional, List
from pydantic import BaseModel, Field, validator


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
    sourceIds: List[str]
    targetIds: List[str]
    label: Label


class PdfAnnotation(BaseModel):
    annotations: List[Annotation]
    relations: List[RelationGroup]


class PageSpec(BaseModel):
    width: int
    height: int
    index: int


class PageToken(BaseModel):
    text: str
    width: float
    height: float
    x: float
    y: float


class Page(BaseModel):
    page: PageSpec
    tokens: List[PageToken] = Field(default_factory=lambda: [])
