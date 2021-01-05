from typing import NamedTuple, List


class Token(NamedTuple):
    text: str
    x: float
    y: float
    width: float
    height: float


class PageInfo(NamedTuple):
    width: float
    height: float
    index: int


class Page(NamedTuple):
    page: PageInfo
    tokens: List[Token]