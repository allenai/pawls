import os
from pathlib import Path

from tqdm import tqdm
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
    """
    Run a pre-processor on a pdf/directory of pawls pdfs and
    send the results to the S2 PDF Structure Service, so they
    can be used as a base for annotation.

    Current preprocessor options are: "grobid".

    To send all pawls structured pdfs in the current directory for processing:

        `pawls preprocess grobid ./`
    """
    which_pdf_service = "prod" if prod else "dev"
    if os.path.isdir(path):
        in_glob = os.path.join(path, "*/*.pdf")
        pdfs = glob.glob(in_glob)
    else:
        if not str(path).endswith(".pdf"):
            raise ValueError("Path is not a directory, but also not a pdf.")
        pdfs = [str(path)]

    pbar = tqdm(pdfs)
    status = []
    for p in pbar:
        path = Path(p)
        sha = path.name.strip(".pdf")
        pbar.set_description(f"Processing {sha[:10]}...")
        if preprocessor == "grobid":
            status.append(process_grobid(sha, str(path), env=which_pdf_service))

    print(
        f"Added {sum(status)}/{len(pdfs)} annotations from {preprocessor} to the {which_pdf_service} S2 PDF Structure Service."
    )
