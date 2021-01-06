import os
import sys
from typing import List, Callable, Set, Dict, Tuple, Optional

import click
import boto3
import botocore
import json
import requests


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=str, default="./")
@click.argument("shas", type=str, nargs=-1, required=True)
@click.option(
    "--sha-file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="A path to a file containing pdf shas.",
)
def fetch(path: click.Path, shas: Tuple[str], sha_file: click.Path = None):
    """
    Download pdfs from Semantic Scholar with metadata
    to a particular location.
    Pdfs can be specified by passing a list of pdf shas, or
    by passing a file containing pdf shas, one per id.

    Download a pdf and associated metadata to the current directory:

        `pawls fetch ./ 34f25a8704614163c4095b3ee2fc969b60de4698`

    """
    shas = list(shas)
    if sha_file is not None:
        extra_ids = [x.strip("\n") for x in open(sha_file, "r")]
        shas.extend(extra_ids)

    result = bulk_fetch_pdfs_for_s2_ids(
        shas, path, pdf_path_func=_per_dir_pdf_download,
    )

    metadata_failed = []
    name_mapping = {}
    for sha in result["success"]:
        title = get_paper_title(sha)
        if title is None:
            metadata_failed.append(sha)
        else:
            name_mapping[sha] = title

    with open(os.path.join(path, "pdf_metadata.json"), "w+") as f:
        json.dump(name_mapping, f)

    okay = True
    if metadata_failed:
        print(
            f"Successfully saved {len(metadata_failed)} pdfs, but failed to find metadata for:"
        )
        for sha in metadata_failed:
            print(sha)
        print()
        okay = False

    not_found = result["not_found"]
    if not_found:
        print(f"Failed to find pdfs for the following ({len(not_found)}) shas:")
        for sha in not_found:
            print(sha)
        print()
        okay = False

    error = result["error"]
    if error:
        print(f"Error fetching pdfs for the following ({len(error)}) shas:")
        for sha in error:
            print(sha)
        print()
        okay = False

    if not okay:
        sys.exit(1)

    print(
        f"Successfully saved {len(result['success']) - len(metadata_failed)} pdfs and metadata to {str(path)}"
    )


# settings for S3 buckets
S3_BUCKET_PDFS = {"default": "ai2-s2-pdfs", "private": "ai2-s2-pdfs-private"}


def _per_dir_pdf_download(target_dir: str, sha: str):
    os.makedirs(os.path.join(target_dir, sha), exist_ok=True)
    return os.path.join(target_dir, sha, f"{sha}.pdf")


def _default_pdf_path(target_dir: str, sha: str):
    return os.path.join(target_dir, f"{sha}.pdf")


def bulk_fetch_pdfs_for_s2_ids(
    s2_ids: List[str],
    target_dir: str,
    pdf_path_func: Callable[[str, str], str] = _default_pdf_path,
) -> Dict[str, Set[str]]:
    """
    s2_ids: List[str]
        A list of s2 pdf shas to download.

    target_dir: str,
        The directory to download them to.
    pdf_path_func: str, optional (default = None)
        A callable function taking 2 parameters: target_dir and sha,
        which returns a string used as the path to download an individual pdf.

    Note:
    User is responsible for figuring out whether the PDF already exists before
    calling this function.  By default, will perform overwriting.

    Returns
    A dict containing "error", "not_found" and "success" keys,
    listing pdf shas that were either not found or errored when fetching.
    """

    os.makedirs(target_dir, exist_ok=True)
    s3 = boto3.resource("s3")
    default_bucket = s3.Bucket(S3_BUCKET_PDFS["default"])
    private_bucket = s3.Bucket(S3_BUCKET_PDFS["private"])

    not_found = set()
    error = set()
    success = set()
    for s2_id in s2_ids:
        try:
            default_bucket.download_file(
                os.path.join(s2_id[:4], f"{s2_id[4:]}.pdf"),
                pdf_path_func(target_dir, s2_id),
            )
            success.add(s2_id)

        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                try:
                    private_bucket.download_file(
                        os.path.join(s2_id[:4], f"{s2_id[4:]}.pdf"),
                        pdf_path_func(target_dir, s2_id),
                    )
                    success.add(s2_id)

                except botocore.exceptions.ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        not_found.add(s2_id)
                    else:
                        error.add(s2_id)
            else:
                error.add(s2_id)

    return {"error": error, "not_found": not_found, "success": success}


S2_API = "https://www.semanticscholar.org/api/1/paper/"


def get_paper_title(paper_sha: str) -> Optional[str]:
    """
    Fetch a small metadata blob from S2.

    paper_sha: str, required
        The paper id to search for.

    returns:
        str if the paper is found, otherwise None.
    """

    response = requests.get(S2_API + paper_sha)
    if response.ok:
        data = response.json()
        return data["paper"]["title"]["text"]
    else:
        return None

if __name__ == "__main__":

    fetch()
