import os
import glob
import click
import shutil
import hashlib

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
def add(directory: click.Path) -> None:
    """
    Add a PDF or directory of PDFs to the pawls dataset (skiff_files/).
    """
    base_dir = Path('skiff_files/apps/pawls/papers')
    base_dir.mkdir(exist_ok=True, parents=True)

    if os.path.isdir(str(directory)):
        pdfs = glob.glob(os.path.join(str(directory), '*.pdf'))
    else:
        pdfs = [str(directory)]

    print(f'Found {len(pdfs)} total PDFs to add.')

    for pdf in tqdm(pdfs):
        sha = hash_pdf(pdf)

        output_dir = base_dir / sha
        output_dir.mkdir(exist_ok=True)

        copy(pdf, output_dir / (sha + '.pdf'))
