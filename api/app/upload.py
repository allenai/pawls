import hashlib
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Callable, Optional, Union

from .pdfplumber import process_pdfplumber


logger = logging.getLogger("uvicorn")

def hash_pdf(file: Union[str, Path]) -> str:
    block_size = 65536

    file_hash = hashlib.sha256()
    with open(str(file), 'rb') as fp:
        fb = fp.read(block_size)
        while len(fb) > 0:
            file_hash.update(fb)
            fb = fp.read(block_size)

    return str(file_hash.hexdigest())


def add_pdf(file_path: Union[str, Path],
            base_path: Union[str, Path],
            pdf_name: Optional[str] = None) -> str:

    # make sure it's a Path object
    file_path = Path(file_path)
    base_path = Path(base_path)

    pdf_name = pdf_name or file_path.name

    base_path.mkdir(exist_ok=True, parents=True)

    pdf_hash = hash_pdf(file_path)

    output_dir = base_path / pdf_hash

    if output_dir.exists():
        logging.warning(f"{file_path} already added. Skipping...")
    else:
        output_dir.mkdir(exist_ok=True)
        shutil.copy(str(file_path),
                    str(output_dir / f'{pdf_hash}.pdf'))
        PDFsMetadata(base_path).set_name(pdf_hash, pdf_name)

    return pdf_hash


class PDFsMetadata:
    def __init__(self, base_path: Union[str, Path]):
        self.path = Path(base_path) / 'pdf_metadata.json'
        self.timestamp = None
        self.metadata = {}
        self._update()

    def _has_updated(self):
        return self.timestamp != os.path.getmtime(self.path)

    def _update(self):
        if self.path.exists():
            with open(self.path, mode='r', encoding='utf-8') as f:
                new_metadata = json.load(f)
        else:
            new_metadata = {}

        self.metadata.update(new_metadata)

        with open(self.path, mode='w', encoding='utf-8') as f:
            json.dump(self.metadata, f)

    def get_name(self, hash):
        return self.metadata.get(hash, hash)

    def set_name(self, hash, name):
        self.metadata.setdefault(hash, name)
        self._update()


async def preprocess_pdf(pdf_hash: str, base_path: Union[str, Path]):
    """
    Run a pre-processor on a pdf/directory of pawls pdfs and
    write the resulting token information to the pdf location.
    """
    base_path = Path(base_path)

    path = base_path / Path(f'{pdf_hash}/{pdf_hash}.pdf')

    if not path.exists():
        msg = f'Cannot find {pdf_hash}.pdf in {base_path}'
        raise ValueError(msg)

    structure_path = path.parent / "pdf_structure.json"

    if not structure_path.exists():

        logging.info(f"Processing {path} using pdfplumber...")

        data = process_pdfplumber(str(path))

        with open(structure_path, mode="w+", encoding='utf-8') as f:
            json.dump(data, f)
    else:
        logging.warn(f"Parsed {structure_path} exists, skipping...")


def assign_pdf_to_user(annotator: str,
                       pdf_hash: str,
                       base_path: Union[str, Path]):

    status_dir = Path(base_path) / 'status'
    os.makedirs(status_dir, exist_ok=True)

    status_path = status_dir / f"{annotator}.json"

    pdf_status = {}
    if status_path.exists():
        with open(status_path, mode='r', encoding='utf-8') as f:
            pdf_status = json.load(f)

    if pdf_hash not in pdf_status:
        pdf_status[pdf_hash] = {
            "sha": pdf_hash,
            "name": PDFsMetadata(base_path).get_name(pdf_hash),
            "annotations": 0,
            "relations": 0,
            "finished": False,
            "junk": False,
            "comments": "",
            "completedAt": None,
        }

    with open(status_path, mode="w+", encoding='utf-8') as out:
        json.dump(pdf_status, out)

    return pdf_status
