from typing import List, Tuple, Dict
import csv
import io

import pytesseract
import pandas as pd
from pdf2image import convert_from_path

from pawls.preprocessors.model import Token, PageInfo, Page
from pawls.commands.utils import get_pdf_pages_and_sizes


def calculate_image_scale_factor(pdf_size, image_size):
    pdf_w, pdf_h = pdf_size
    img_w, img_h = image_size
    scale_w, scale_h = pdf_w / img_w, pdf_h / img_h
    return scale_w, scale_h


def extract_page_tokens(
    pdf_image: "PIL.Image", pdf_size=Tuple[float, float], language="eng"
) -> List[Dict]:

    _data = pytesseract.image_to_data(pdf_image, lang=language)

    scale_w, scale_h = calculate_image_scale_factor(pdf_size, pdf_image.size)

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
        .assign(
            x=lambda df: df.x * scale_w,
            y=lambda df: df.y * scale_h,
            width=lambda df: df.width * scale_w,
            height=lambda df: df.height * scale_h,
        )
        .apply(lambda row: row.to_dict(), axis=1)
        .tolist()
    )

    return tokens


def parse_annotations(pdf_file: str) -> List[Page]:

    pdf_images = convert_from_path(pdf_file)
    _, pdf_sizes = get_pdf_pages_and_sizes(pdf_file)
    pages = []
    for page_index, (pdf_image, pdf_size) in enumerate(zip(pdf_images, pdf_sizes)):
        tokens = extract_page_tokens(pdf_image, pdf_size)
        w, h = pdf_size
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
