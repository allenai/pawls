from typing import NamedTuple, List, Dict

import json
import glob
import os

from app.metadata import get_paper_metadata
from app.utils import bulk_fetch_pdfs_for_s2_ids

from app.structure.grobid import process_grobid

IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev")


class Configuration(NamedTuple):
    """
    General configuration for the annotation tool.

    output_directory: str, required.
        The directory where the pdfs, metadata and
        annotation output will be stored.
    labels: List[Dict[str, str]], required.
        The labels in use for annotation.
    relations: List[Dict[str, str]], required.
        The relations in use for annotation.
    pdfs: List[str], required.
        The pdfs that you want to annotate. This can be updated,
        and new pdfs will be _added_ to the annotation set. Removing
        pdfs from this list once the app has been started with them
        will not remove them from the annotation.
    preprocessors: List[str], optional (default = None)
        Optional pre-processing steps to apply to pdfs. Currently,
        the only supported option is "grobid".
    """

    output_directory: str
    labels: List[Dict[str, str]]
    relations: List[Dict[str, str]]
    pdfs: List[str]
    preprocessors: List[str] = None


class Annotators(NamedTuple):
    """
    Configuration for Annotators.

    annotators: List[str], required.
        A list of gmail emails for annotators.
        Currently these must be ai2 emails.
    allocations: Dict[str, List[str]], required.
        A mapping from annotator emails to lists of pdf shas
        to which they are assigned.
    """

    annotators: List[str]
    allocations: Dict[str, List[str]]


def load_configuration(filepath: str) -> Configuration:

    blob = json.load(open(filepath))
    return Configuration(**blob)


def load_annotators(filepath) -> Annotators:

    blob = json.load(open(filepath))
    return Annotators(**blob)


def _per_dir_pdf_download(target_dir: str, sha: str):
    os.makedirs(os.path.join(target_dir, sha), exist_ok=True)
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
        json.dump(metadata._asdict(), open(metadata_path, "w+"))

        # Populate the pdf-structure-service with grobid
        # annotations for the pdf.
        if "grobid" in configuration.preprocessors:
            pdf_path = _per_dir_pdf_download(configuration.output_directory, sha)
            process_grobid(sha, pdf_path, env=IN_PRODUCTION)
