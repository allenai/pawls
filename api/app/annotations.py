
from typing import NamedTuple, Optional, List


class Bounds(NamedTuple):
    left: float
    top: float
    right: float
    bottom: float


class Label(NamedTuple):
    text: str
    color: str


class TokenId(NamedTuple):
    pageIndex: int
    tokenIndex: int


class Annotation(NamedTuple):
    page: int
    label: Label
    bounds: Bounds
    tokens: Optional[List[TokenId]] = None
