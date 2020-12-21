from typing import Optional

from pydantic import BaseModel


class PaperStatus(BaseModel):
    sha: str
    name: str
    annotations: int
    relations: int
    finished: bool
    junk: bool
    comments: str
    completedAt: Optional[str]

    @staticmethod
    def empty(sha: str, name: str):
        return PaperStatus(
            sha=sha,
            name=name,
            annotations=0,
            relations=0,
            finished=False,
            junk=False,
            comments="",
            completedAt=None,
        )
