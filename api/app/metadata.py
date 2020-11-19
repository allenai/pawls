from typing import List, Optional

from pydantic import BaseModel


class PaperMetadata(BaseModel):
    sha: str
    title: str
    venue: str
    year: int
    cited_by: int
    authors: List[str]


class PaperStatus(BaseModel):
    annotations: int
    relations: int
    finished: bool
    junk: bool
    comments: str
    completedAt: Optional[str]

    @staticmethod
    def empty():
        return PaperStatus(
            annotations=0,
            relations=0,
            finished=False,
            junk=False,
            comments="",
            completedAt=None,
        )


class PaperInfo(BaseModel):
    metadata: PaperMetadata
    status: PaperStatus
    sha: str
