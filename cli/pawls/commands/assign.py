import os
from typing import Tuple

import click
from click import UsageError, BadArgumentUsage
import json
import glob
import re


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("annotator", type=str)
@click.argument("shas", type=str, nargs=-1)
@click.option(
    "--sha-file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="A path to a file containing shas.",
)
@click.option(
    "--name-file",
    "-f",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="A path to a json file mapping shas to file names.",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    type=bool,
    default=False,
    help="A flag to assign all current pdfs in a pawls project to an annotator.",
)
def assign(
    path: click.Path,
    annotator: str,
    shas: Tuple[str],
    sha_file: click.Path = None,
    name_file: click.Path = None,
    all: bool = False,
):
    """
    Assign pdfs and annotators for a project.

    Use assign to assign annotators to a project, or assign them
    pdfs in the specified directory.

    Annotators must be assigned a username corresponding
    to a gmail email address, such as `markn@gmail.com`.

    Add an annotator:

        `pawls assign <path to pawls directory> markn@gmail.com`

    To assign all current pdfs in the project to an annotator, use:

        `pawls assign <path to pawls directory> <annotator> --all`
    """
    shas = set(shas)

    pdfs = glob.glob(os.path.join(path, "*/*.pdf"))
    project_shas = {p.split("/")[-2] for p in pdfs}
    if all:
        # If --all flag, we use all pdfs in the current project.
        shas.update(project_shas)

    if sha_file is not None:
        extra_ids = [x.strip("\n") for x in open(sha_file, "r")]
        shas.extend(extra_ids)

    diff = shas.difference(project_shas)
    if diff:
        error = f"Found shas which are not present in path {path} .\n"
        error = (
            error
            + f"Add pdf files in the specified directory, one per sub-directory."
        )
        for sha in diff:
            error = error + f"{sha}\n"
        raise UsageError(error)

    if all:
        # If --all flag, we use all pdfs in the current project.
        shas.update(project_shas)

    if sha_file is not None:
        extra_ids = [x.strip("\n") for x in open(sha_file, "r")]
        shas.extend(extra_ids)

    result = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", annotator)

    if not result or result.group(0) != annotator:
        raise BadArgumentUsage("Provided annotator was not a valid email.")

    status_dir = os.path.join(path, "status")
    os.makedirs(status_dir, exist_ok=True)

    status_path = os.path.join(status_dir, f"{annotator}.json")

    pdf_status = {}
    if os.path.exists(status_path):
        pdf_status = json.load(open(status_path))

    name_mapping = {}
    if name_file is not None:
        name_mapping = json.load(open(name_file))
    else:
        print("Warning: --name-file was not provided, using shas as pdf names.")

    for sha in shas:
        if sha in pdf_status:
            continue
        else:

            name = name_mapping.get(sha, None)
            if name is None:
                name = sha

            pdf_status[sha] = {
                "sha": sha,
                "name": name,
                "annotations": 0,
                "relations": 0,
                "finished": False,
                "junk": False,
                "comments": "",
                "completedAt": None,
            }

    with open(status_path, "w+") as out:
        json.dump(pdf_status, out)
