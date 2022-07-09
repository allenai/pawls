from email.policy import default
import os
from pathlib import Path
import json
import re

from tqdm import tqdm
import click
import glob

from pawls.preprocessors.grobid import process_grobid
from pawls.preprocessors.pdfplumber import process_pdfplumber
from pawls.preprocessors.tesseract import process_ocr

@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("preprocessor", type=str)
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.argument("ocr-param", nargs=-1)

def preprocess(preprocessor: str, path: click.Path, ocr_param: tuple):
    """
    Run a pre-processor on a pdf/directory of pawls pdfs and
    write the resulting token information to the pdf location.

    Current preprocessor options are: "grobid".

    To send all pawls structured pdfs in the current directory for processing:

        `pawls preprocess grobid ./`
    """
    
    print(f"Processing using the {preprocessor} preprocessor...")

    ocr_args = {
        "engine": "",
        "lang": "",
        "psm": ""
    }

    if preprocessor == "ocr":
        print("The ocr preprocessor may take several minutes to process each PDF.")
        if len(ocr_param) > 1:
            for param in ocr_param[1:]:
                if not re.search("\w+=\w+", param) :
                    raise ValueError(f"There's an error in ocr_param option '{param}'. Parameters should be indicated as key=value.")
                key, value = param.split("=", 1)
                if key not in ocr_args.keys():
                    raise ValueError(f"There's an unknown option '{key}=' in ocr_param options. Available options are engine, lang, psm and gcv_credential.")
                ocr_args[key] = value
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
        if preprocessor == "grobid":
            data = process_grobid(str(path))
        elif preprocessor == "pdfplumber":
            data = process_pdfplumber(str(path))
        elif preprocessor == "ocr":
            data = process_ocr(str(path), ocr_args)
        with open(path.parent / "pdf_structure.json", "w+", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

