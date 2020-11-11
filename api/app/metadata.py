from typing import NamedTuple, List


class PaperMetadata(NamedTuple):
    sha: str
    title: str
    venue: str
    year: int
    cited_by: int
    authors: List[str]


class PaperStatus(NamedTuple):
    annotations: int
    relations: int
    status: str
    comments: str
    completedAt: str

    @staticmethod
    def empty():
        return PaperStatus(
            0, 0, "BLANK", "", None
        )


class PaperInfo(NamedTuple):
    metadata: PaperMetadata
    status: PaperStatus
    sha: str
