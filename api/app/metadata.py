from typing import Optional

from pydantic import BaseModel


class PaperStatus(BaseModel):
    sha: str
    annotations: int
    relations: int
    finished: bool
    junk: bool
    comments: str
    completedAt: Optional[str]

    @staticmethod
    def empty(sha: str):
        return PaperStatus(
            sha=sha,
            annotations=0,
            relations=0,
            finished=False,
            junk=False,
            comments="",
            completedAt=None,
        )
