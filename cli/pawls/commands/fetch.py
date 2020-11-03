from typing import List, Callable, Set, Dict, Tuple
import os

import click
import boto3
import botocore


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("shas", type=str, nargs=-1, help="A list of S2 pdf shas.")
@click.argument(
    "out_dir", type=click.Path(exists=False), help="The directory to save the pdfs to."
)
@click.option(
    "--sha-file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="A path to a file containing pdf shas.",
)
def fetch(shas: Tuple[str], out_dir: click.Path, sha_file: click.Path = None):

    shas = list(shas)
    if sha_file is not None:
        extra_ids = [x.strip("\n") for x in open(sha_file, "r")]
        shas.extend(extra_ids)

    result = bulk_fetch_pdfs_for_s2_ids(shas, out_dir)
    print(f"Successfully saved {len(result['success'])} pdfs to {str(out_dir)}")


# settings for S3 buckets
S3_BUCKET_PDFS = {"default": "ai2-s2-pdfs", "private": "ai2-s2-pdfs-private"}


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
