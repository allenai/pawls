from typing import List, Dict, Set, Callable
import os

import boto3
import botocore
from pythonjsonlogger import jsonlogger


class StackdriverJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom log JSON log formatter that adds the severity member, allowing
    end users to filter logs by the level of the log message emitted.

    TODO: Parse request logs and add fields for each request element (user-agent
    processing time, etc)

    TODO:Add a timestamp that's used in place of Stackdriver's records (which
    reflect the time the log was written to Stackdriver, I think).
    """

    def add_fields(self, log_record, record, message_dict):
        super(StackdriverJsonFormatter, self).add_fields(
            log_record, record, message_dict
        )
        log_record["severity"] = record.levelname


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
