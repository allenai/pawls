from typing import NamedTuple, List, Optional
import requests


S2_API = "https://www.semanticscholar.org/api/1/paper/"


class PaperMetadata(NamedTuple):
    sha: str
    title: str
    venue: str
    year: int
    cited_by: int
    authors: List[str]


def get_paper_metadata(paper_sha: str) -> Optional[PaperMetadata]:
    """
    Fetch a small metadata blob from S2.

    paper_sha: str, required
        The paper id to search for.

    returns:
        PaperMetadata if the paper is found, otherwise None.
    """

    response = requests.get(S2_API + paper_sha)
    if response.ok:
        data = response.json()

        return PaperMetadata(
            sha=paper_sha,
            title=data["paper"]["title"]["text"],
            venue=data["paper"]["venue"]["text"],
            year=int(data["paper"]["year"]["text"]),
            cited_by=int(data["paper"]["citationStats"]["numCitations"]),
            authors=[author[0]["name"] for author in data["paper"]["authors"]]
        )

    else:
        return None
