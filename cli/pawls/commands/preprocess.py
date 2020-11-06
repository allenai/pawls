import os
from pathlib import Path

import click
import glob

from pawls.preprocessors.grobid import process_grobid


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("preprocessor", type=str)
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.option(
    "--prod/--dev",
    type=bool,
    default=False,
    help="Whether to add preprocessor annotations to the dev or prod PDF Structure Service.",
)
def preprocess(preprocessor: str, path: click.Path, prod: bool):

    which_pdf_service = "prod" if prod else "dev"
    if os.path.isdir(path):
        in_glob = os.path.join(path, "*/*.pdf")
        pdfs = glob.glob(in_glob)
    else:
        if not str(path).endswith(".pdf"):
            raise ValueError("Path is not a directory, but also not a pdf.")
        pdfs = [str(path)]
    for p in pdfs:
        path = Path(p)
        sha = path.name.strip(".pdf")
        if preprocessor == "grobid":
            process_grobid(sha, str(path), env=which_pdf_service)

    print(
        f"Added {len(pdfs)} annotations for {preprocessor} to the {which_pdf_service} S2 PDF Structure Service."
    )