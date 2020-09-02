from typing import NamedTuple, List

import json
import glob
import os

from app.metadata import get_paper_metadata
from app.utils import bulk_fetch_pdfs_for_s2_ids
from app.structure import process_grobid

class Configuration(NamedTuple):

    output_directory: str
    labels: List[str]
    pdfs: List[str]
    preprocessors: List[str] = None


class Annotators(NamedTuple):

    annotators: List[str]
    allocations: List[str]


def load_configuration(filepath: str) -> Configuration:

    blob = json.load(open(filepath))
    return Configuration(**blob)


def load_annotators(filepath) -> Annotators:

    blob = json.load(open(filepath))
    return Annotators(**blob)


def _per_dir_pdf_download(target_dir: str, sha: str):
    os.makedirs(os.path.join(target_dir, sha))
    return os.path.join(target_dir, sha, f"{sha}.pdf")


def maybe_download_pdfs(configuration: Configuration):

    pdfs = set(glob.glob(f"{configuration.output_directory}/*/*.pdf"))
    existing = {p.split("/")[-2] for p in pdfs}

    specified = set(configuration.pdfs)
    diff = specified.difference(existing)

    # TODO(MarkN): Write the failed pdf downloads somewhere
    # and surface in an admin ui.
    result = bulk_fetch_pdfs_for_s2_ids(
        list(diff), configuration.output_directory, pdf_path_func=_per_dir_pdf_download
    )

    # Find the metadata for the pdf.
    for sha in result["success"]:
        metadata_path = os.path.join(
            configuration.output_directory, sha, "metadata.json"
        )
        metadata = get_paper_metadata(sha)
        if metadata is None:
            metadata = get_paper_metadata(sha, use_prod=True)

        json.dump(metadata._asdict(), open(metadata_path, "w+"))


def run_preprocessors(configuration: Configuration):

    if "grobid" in configuration.preprocessors:

        process_grobid()