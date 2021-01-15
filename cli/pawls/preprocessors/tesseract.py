from typing import List
import csv
import io

import pytesseract
import pandas as pd
from pdf2image import convert_from_path
from PIL import Image

from pawls.preprocessors.model import Token, PageInfo, Page


def extract_page_tokens(pdf_image: Image, language="eng") -> List[Token]:

    _data = pytesseract.image_to_data(pdf_image, lang=language)

    res = pd.read_csv(
        io.StringIO(_data), quoting=csv.QUOTE_NONE, encoding="utf-8", sep="\t"
    )
    # An implementation adopted from https://github.com/Layout-Parser/layout-parser/blob/20de8e7adb0a7d7740aed23484fa8b943126f881/src/layoutparser/ocr.py#L475
    tokens = (
        res[~res.text.isna()]
        .groupby(["page_num", "block_num", "par_num", "line_num", "word_num"])
        .apply(
            lambda gp: pd.Series(
                [
                    gp["left"].min(),
                    gp["top"].min(),
                    gp["width"].max(),
                    gp["height"].max(),
                    gp["conf"].mean(),
                    gp["text"].str.cat(sep=" "),
                ]
            )
        )
        .reset_index(drop=True)
        .reset_index()
        .rename(
            columns={
                0: "x",
                1: "y",
                2: "width",
                3: "height",
                4: "score",
                5: "text",
                "index": "id",
            }
        )
        .drop(columns=["score", "id"])
        .apply(lambda row: row.to_dict(), axis=1)
        .tolist()
    )

    return tokens


def parse_annotations(pdf_file: str) -> List[Page]:

    pdf_images = convert_from_path(pdf_file)

    pages = []
    for page_index, pdf_image in enumerate(pdf_images):
        tokens = extract_page_tokens(pdf_image)
        w, h = pdf_image.size
        page = dict(
            page=dict(
                width=w,
                height=h,
                index=page_index,
            ),
            tokens=tokens,
        )
        pages.append(page)

    return pages


def process_tesseract(pdf_file: str):
    """
    Integration for importing annotations from pdfplumber.
    pdf_file: str
        The path to the pdf file to process.
    """
    annotations = parse_annotations(pdf_file)

    return annotations
