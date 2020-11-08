import os
from typing import Tuple

import click
import json


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
def assign(path: click.Path, annotator: str, shas: Tuple[str], sha_file: click.Path = None):

    shas = list(shas)
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
