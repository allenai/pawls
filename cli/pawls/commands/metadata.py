import os
from typing import List, NamedTuple, Optional
from pathlib import Path
import json

import click
import requests
import glob


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
def metadata(path: click.Path):

    if os.path.isdir(path):
        in_glob = os.path.join(path, "*/*.pdf")
        pdfs = glob.glob(in_glob)
    else:
        if not str(path).endswith(".pdf"):
            raise ValueError("Path is not a directory, but also not a pdf.")
        pdfs = [str(path)]

    success = 0
    failed = []
    for p in pdfs:
        path = Path(p)
        metadata_path = path.parent / "metadata.json"

        sha = path.name.strip(".pdf")
        metadata = get_paper_metadata(sha)

        if metadata is None:
            failed.append(sha)
            continue
        else:
            success += 1

        with open(metadata_path, "w+") as out:
            json.dump(metadata, out)

    print(f"Added metadata for {success} pdfs in {path}.")
    if failed:
        print(f"Failed to find metadata for {len(failed)} pdfs with shas:")
        for sha in failed:
            print(sha)


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
            authors=[author[0]["name"] for author in data["paper"]["authors"]],
        )

    else:
        return None
