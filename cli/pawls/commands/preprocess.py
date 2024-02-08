import os
from pathlib import Path
import json

from tqdm import tqdm
import click
import glob

from pawls.preprocessors.grobid import process_grobid
from pawls.preprocessors.pdfplumber import process_pdfplumber
from pawls.preprocessors.tesseract import process_tesseract

@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("preprocessor", type=str)
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
def preprocess(preprocessor: str, path: click.Path):
    """
    Run a pre-processor on a pdf/directory of pawls pdfs and
    write the resulting token information to the pdf location.

    Current preprocessor options are: "grobid".

    To send all pawls structured pdfs in the current directory for processing:

        `pawls preprocess grobid ./`
    """
    print(f"Processing using the {preprocessor} preprocessor...")
    if preprocessor == "ocr":
        print("The ocr preprocessor may take several minutes to process each PDF.")
    if os.path.isdir(path):
        in_glob = os.path.join(path, "*/*.pdf")
        pdfs = glob.glob(in_glob)
    else:
        if not str(path).endswith(".pdf"):
            raise ValueError("Path is not a directory, but also not a pdf.")
        pdfs = [str(path)]

    pbar = tqdm(pdfs)

    for p in pbar:
        path = Path(p)
        sha = path.name.strip(".pdf")
        pbar.set_description(f"Processing {sha[:10]}...")
        try:
            if preprocessor == "grobid":
                data = process_grobid(str(path))
            elif preprocessor == "pdfplumber":
                data = process_pdfplumber(str(path))
            elif preprocessor == "ocr":
                # Currently there's only a OCR preprocessor. 
                data = process_tesseract(str(path))
        except Exception as e:
            tqdm.write(f"💥 Error while processing pdf with sha: {sha[:10]}...}")
        else:
            with open(path.parent / "pdf_structure.json", "w+") as f:
                json.dump(data, f)

