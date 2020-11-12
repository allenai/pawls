import os
from typing import Tuple

import click
from click import UsageError, BadArgumentUsage
import json
import glob
import re


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=click.File('r'))
@click.argument("output", type=click.Path(file_okay=False))
@click.option(
    "--annotator",
    "-u",
    type=str,
    help="Export annotations of the specified annotator.",
)
@click.option(
    "--all",
    "-a",
    type=bool,
    default=False,
    help="A flag to assign all current pdfs in a pawls project to an annotator.",
)
def export(
    path: click.Path,
    config: click.File,
    output: click.Path,
    annotator: str = None,
    all: bool = False,
):
    """
    Export the annotations for a project.

    To export all annotations of a project of the default annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path>`

    To export only finished annotations of from a given annotator, e.g. markn, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn`.

    To export all annotations of from a given annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn --all`.
    """


    pass