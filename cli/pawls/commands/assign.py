import os
from typing import Tuple

import click
import json
import glob

@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("annotator", type=str)
@click.argument("shas", type=str, nargs=-1)
@click.option(
    "--sha-file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="A path to a file containing pdf shas.",
)
@click.option(
    "--all",
    "-a",
    type=bool,
    default=False,
    help="A flag to assign all current pdfs in a pawls project to an annotator.",
)
def assign(path: click.Path, annotator: str, shas: Tuple[str], sha_file: click.Path = None, all: bool = False):
    """
    Assign pdfs and annotators for a project.

    Use assign to assign annotators to a project, or assign them
    pdfs fetched using `pawls fetch <pdfs>`.

    Add an annotator called mark:

        `pawls assign <path to pawls directory> mark`

    To assign all current pdfs in the project to an annotator, use:

        `pawls assign <path to pawls directory> <annotator> --all`
    """
    shas = list(shas)
    if all:
        # If --all flag, we use all pdfs in the current project.
        pdfs = glob.glob(os.path.join(path, "*/*.pdf"))
        shas.extend([p.split("/")[-1].replace(".pdf", "") for p in pdfs])

    if sha_file is not None:
        extra_ids = [x.strip("\n") for x in open(sha_file, "r")]
        shas.extend(extra_ids)

    status_dir = os.path.join(path, "status")
    os.makedirs(status_dir, exist_ok=True)

    status_path = os.path.join(status_dir, f"{annotator}.json")

    pdf_status = {}
    if os.path.exists(status_path):
        pdf_status = json.load(open(status_path))

    for sha in shas:
        if sha in pdf_status:
            continue
        else:
            pdf_status[sha] = {
                "annotations": 0,
                "relations": 0,
                "status": "INPROGRESS",
                "comments": "",
                "completed_at": None
            }

    with open(status_path, "w+") as out:
        json.dump(pdf_status, out)
