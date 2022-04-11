import hashlib
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Union
import aiofiles

try:
    from pawls.preprocessors.grobid import process_grobid
except ImportError:
    process_grobid = None

try:
    from pawls.preprocessors.pdfplumber import process_pdfplumber
except ImportError:
    process_pdfplumber = None

BASE_DIR = Path("/skiff_files/apps/pawls/papers")

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


def add_pdf(file_path: Union[str, Path], pdf_name: Optional[str] = None) -> str:
    # make sure it's a Path object
    file_path = Path(file_path)

    pdf_name = pdf_name or file_path.name

    BASE_DIR.mkdir(exist_ok=True, parents=True)

    pdf_hash = hash_pdf(file_path)

    output_dir = BASE_DIR / pdf_hash

    if output_dir.exists():
        logging.warning(f"{file_path} already added. Skipping...")
    else:
        output_dir.mkdir(exist_ok=True)
        shutil.copy(str(file_path),
                    str(output_dir / f'{pdf_hash}.pdf'))
        PDFsMetadata().set_name(pdf_hash, pdf_name)

    return pdf_hash


class PDFsMetadata:
    def __init__(self):
        self.path = BASE_DIR / 'pdf_metadata.json'
        self.timestamp = None
        self.metadata = {}
        self._update()

    def _has_updated(self):
        return self.timestamp != os.path.getmtime(self.path)

    async def _update(self):
        if self.path.exists():
            async with aiofiles.open(self.path, mode='r', encoding='utf-8') as f:
                new_metadata = json.load(await f.read())
        else:
            new_metadata = {}

        self.metadata.update(new_metadata)

        async with aiofiles.open(self.path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(self.metadata))

    def get_name(self, hash):
        return self.metadata.get(hash, hash)

    def set_name(self, hash, name):
        self.metadata.setdefault(hash, name)
        self._update()


async def preprocess_pdf(pdf_hash: str, processor: str = 'pdfplumber', data: dict = None):
    """
    Run a pre-processor on a pdf/directory of pawls pdfs and
    write the resulting token information to the pdf location.
    """
    path = BASE_DIR / Path(f'{pdf_hash}/{pdf_hash}.pdf')

    if not path.exists():
        msg = f'Cannot find {pdf_hash}.pdf in {BASE_DIR}'
        raise ValueError(msg)

    structure_path = path.parent / "pdf_structure.json"

    if not structure_path.exists():

        logging.info(f"Processing {path} using {processor}...")

        if data is None:
            if processor == "grobid":
                data = process_grobid(str(path))
            elif processor == "pdfplumber":
                data = process_pdfplumber(str(path))

        # set the valid flag to -1 in case that's not info that
        # is from the parser
        [token.setdefault('valid', -1)
         for page in data for token in page['tokens']]

        with open(structure_path, mode="w+", encoding='utf-8') as f:
            json.dump(data, f)
    else:
        logging.warn(f"Parsed {structure_path} exists, skipping...")


def assign_pdf_to_user(annotator: str, pdf_hash: str):
    status_dir = BASE_DIR / 'status'
    os.makedirs(status_dir, exist_ok=True)

    status_path = status_dir / f"{annotator}.json"

    pdf_status = {}
    if status_path.exists():
        with open(status_path, mode='r', encoding='utf-8') as f:
            pdf_status = json.load(f)

    if pdf_hash not in pdf_status:
        pdf_status[pdf_hash] = {
            "sha": pdf_hash,
            "name": PDFsMetadata().get_name(pdf_hash),
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
