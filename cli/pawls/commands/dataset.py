import os
import glob
import click
import shutil
import hashlib
import logging

from tqdm import tqdm
from pathlib import Path
from typing import Union


def hash_pdf(file: Union[str, Path]) -> str:
    block_size = 65536

    file_hash = hashlib.sha256()
    with open(str(file), 'rb') as fp:
        fb = fp.read(block_size)
        while len(fb) > 0:
            file_hash.update(fb)
            fb = fp.read(block_size)

    return str(file_hash.hexdigest())


def copy(source: Union[str, Path], destination: Union[str, Path]) -> None:
    shutil.copy(str(source), str(destination))


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("directory", type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.option("--no-hash", is_flag=True)
def add(directory: click.Path, no_hash: bool) -> None:
    """
    Add a PDF or directory of PDFs to the pawls dataset (skiff_files/).
    """
    base_dir = Path("skiff_files/apps/pawls/papers")
    base_dir.mkdir(exist_ok=True, parents=True)

    if os.path.isdir(str(directory)):
        pdfs = glob.glob(os.path.join(str(directory), "*.pdf"))
    else:
        pdfs = [str(directory)]

    logging.info(f"Found {len(pdfs)} total PDFs to add.")

    for pdf in tqdm(pdfs):
        pdf_name = Path(pdf).stem

        if not no_hash:
            pdf_name = hash_pdf(pdf)

        output_dir = base_dir / pdf_name

        if output_dir.exists() and no_hash:
            logging.warning(f"PDF with name {pdf_name}.pdf already added. Skipping...")
            continue
        elif output_dir.exists():
            logging.warning(f"{pdf} already added. Skipping...")
            continue

        output_dir.mkdir(exist_ok=True)

        copy(pdf, output_dir / (pdf_name + '.pdf'))
