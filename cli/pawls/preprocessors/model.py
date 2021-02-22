import json
from dataclasses import dataclass  # enables inheritance
from typing import NamedTuple, List, Tuple, Dict, Union


def union_boxes(boxes: List["Box"]) -> "Box":
    """Find the outside boundary of the given boxes.

    Args:
        boxes (List[Box]):
            A list of Box-like instances

    Returns:
        Box: the unioned box.
    """
    left, top, right, bottom = float("inf"), float("inf"), float("-inf"), float("-inf")
    for box in boxes:
        l, t, r, b = box.coordinates
        left = min(left, l)
        top = min(top, t)
        right = max(right, r)
        bottom = max(bottom, b)
    return Box(left, top, right - left, bottom - top)


@dataclass
class Box:

    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> Tuple[float, float]:
        """Return the center of the token box"""
        return self.x + self.width / 2, self.y + self.height / 2

    @property
    def coordinates(self) -> Tuple[float, float, float, float, float]:
        """Returns the left, top, right, bottom coordinates of the box"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def is_in(self, other: "Box", soft_margin: Dict = None) -> bool:
        """Determines whether the center of this box is contained
        inside another box with a soft margin.

        Args:
            other (Box):
                The other box object.
            soft_margin (Dict, optional):
                Alllowing soft margin of the box boundaries. If set, enlarge
                the outside box (other) by the coordinates.
                Defaults to {}.
        """
        other = other.copy()

        x, y = self.center
        if soft_margin is not None:
            other.pad(**soft_margin)
        xa, ya, xb, yb = other.coordinates

        return xa <= x <= xb and ya <= y <= yb

    def pad(self, left=0, top=0, bottom=0, right=0):
        """Change the boundary positions of the box"""

        self.x -= left
        self.y -= top
        self.width += left + right
        self.height += top + bottom

    def copy(self):
        """Create a copy of the box"""
        return self.__class__(**vars(self))

    def scale(self, scale_factor: Union[float, Tuple[float, float]]):
        """Scale the box according to the given scale factor.

        Args:
            scale_factor (Union[float, Tuple[float, float]]):
                it can be either a float, indicating the same scale factor
                for the two axes, or a two-element tuple for x and y axis
                scaling factor, respectively.

        """

        if isinstance(scale_factor, float):
            self.x *= scale_factor
            self.y *= scale_factor
            self.width *= scale_factor
            self.height *= scale_factor

        elif isinstance(scale_factor, tuple):
            scale_x, scale_y = scale_factor
            self.x *= scale_x
            self.y *= scale_y
            self.width *= scale_x
            self.height *= scale_y

    def as_bounds(self) -> Dict[str, float]:
        """Convert the box into a the bounds format."""
        return {
            "left": self.x,
            "top": self.y,
            "right": self.x + self.width,
            "bottom": self.y + self.height,
        }

    @classmethod
    def from_bounds(cls, bounds) -> "Box":
        """Create a box based on the given bounds."""
        return cls(
            x=bounds["left"],
            y=bounds["top"],
            width=bounds["right"] - bounds["left"],
            height=bounds["bottom"] - bounds["top"],
        )


@dataclass
class Token(Box):
    text: str


@dataclass
class Block(Box):
    label: str

    @classmethod
    def from_anno(cls, anno) -> "Box":
        """Create a box based on the given annotation."""
        bounds = anno["bounds"]
        return cls(
            x=bounds["left"],
            y=bounds["top"],
            width=bounds["right"] - bounds["left"],
            height=bounds["bottom"] - bounds["top"],
            label=anno["label"]["text"],
        )


@dataclass
class PageInfo:
    width: float
    height: float
    index: int

    def scale(self, scale_factor: Union[float, Tuple[float, float]]):
        """Scale the page box according to the given scale factor

        Args:
            scale_factor (Union[float, Tuple[float, float]]):
                it can be either a float, indicating the same scale factor
                for the two axes, or a two-element tuple for x and y axis
                scaling factor, respectively.
        """

        if isinstance(scale_factor, float):
            self.width *= scale_factor
            self.height *= scale_factor
        elif isinstance(scale_factor, tuple):
            scale_x, scale_y = scale_factor
            self.width *= scale_x
            self.height *= scale_y


@dataclass
class Page:
    page: PageInfo
    tokens: List[Union[Token, Block]]

    def scale(self, scale_factor: Union[float, Tuple[float, float]]):
        """Scale the page according to the given scale factor.

        Args:
            scale_factor (Union[float, Tuple[float, float]]):
                it can be either a float, indicating the same scale factor
                for the two axes, or a two-element tuple for x and y axis
                scaling factor, respectively.
        """
        self.page.scale(scale_factor)
        for token in self.tokens:
            token.scale(scale_factor)

    def scale_like(self, other: "Page"):
        """Scale the page based on the other page."""

        scale_x = other.page.width / self.page.width
        scale_y = other.page.height / self.page.height

        self.scale((scale_x, scale_y))

    def filter_tokens_by(self, box: Box, soft_margin: Dict = None) -> Dict[int, Token]:
        """Select tokens in the Page that inside the input box"""
        return {
            idx: token
            for idx, token in enumerate(self.tokens)
            if token.is_in(box, soft_margin)
        }


def load_tokens_from_file(filename: str) -> List[Page]:
    """Load tokens files into the data model

    Returns:
        List[Page]:
            A list of `Page` object for eac page.
    """

    with open(filename, "r") as fp:
        source_data = json.load(fp)

    return [
        Page(
            page=PageInfo(**page_data["page"]),
            tokens=[Token(**token) for token in page_data["tokens"]],
        )
        for page_data in source_data
    ]