from typing import List, Tuple, Dict
import csv
import io

import pandas as pd
import numpy as np
import cv2
import pytesseract
from pdf2image import convert_from_path
from google.oauth2 import service_account
from google.cloud import vision
from pathlib import Path

from pawls.preprocessors.model import Token, PageInfo, Page
from pawls.commands.utils import get_pdf_pages_and_sizes


def calculate_image_scale_factor(pdf_size, image_size):
    pdf_w, pdf_h = pdf_size
    img_w, img_h = image_size
    scale_w, scale_h = pdf_w / img_w, pdf_h / img_h
    return scale_w, scale_h


def extract_page_tokens(
    pdf_image: "PIL.Image", ocr_args: dict, pdf_size=Tuple[float, float]
) -> List[Dict]:

    if ocr_args["engine"] == "tesseract" or not ocr_args["engine"]:
        lang = ocr_args["lang"]
        psm = int(ocr_args["psm"])
        tokens = tesseract_extractor(pdf_image, lang, psm, pdf_size)
        
    elif ocr_args["engine"] == "cloud-vision":
        lang = ocr_args["lang"]
        if lang:
            lang = lang.split("+")
        tokens = gcv_extractor(pdf_image, lang, pdf_size)
    else:
        raise ValueError("The specified ocr engine was not found. Available options are tesseract or cloud-vision.")

    return tokens


def tesseract_extractor(pdf_image: "PIL.Image", lang: str, psm: str, pdf_size=Tuple[float, float]) -> List[Dict]:

    if not lang:
        lang = "eng"

    if not psm:
        psm = 3

    _data = pytesseract.image_to_data(pdf_image, lang=lang, config=f"--psm {psm}")
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

def gcv_extractor(pdf_image: "PIL.Image", lang: str, pdf_size=Tuple[float, float]) -> List[Dict]:

    cwd = Path.cwd()
    credential_path = list(Path(cwd).glob('*gcv-*.json'))[0]

    credentials = service_account.Credentials.from_service_account_file(filename=credential_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    client = vision.ImageAnnotatorClient(credentials=credentials)
    
    arr_img = np.asarray(pdf_image)
    byteImage = cv2.imencode('.jpg', arr_img)[1].tobytes()

    print("[INFO] making request to Google Cloud Vision API...")
    image = vision.Image(content=byteImage)
    response = client.document_text_detection(image=image, image_context={"language_hints": lang})
    if response.error.message:
        raise Exception(f"{response.error.message}\nFor more info on errors, check:\nhttps://cloud.google.com/apis/design/errors")
    print("[INFO] response from Google Cloud Vision API returned successfully.")

    tokens = []
    scale_w, scale_h = calculate_image_scale_factor(pdf_size, pdf_image.size)
    for text in response.text_annotations[1::]:
        ocr = text.description
        startX = text.bounding_poly.vertices[0].x
        startY = text.bounding_poly.vertices[0].y
        endX = text.bounding_poly.vertices[1].x
        endY = text.bounding_poly.vertices[2].y

        tokens.append({
            "x": startX * scale_w,
            "y": startY * scale_h,
            "width": (endX-startX) * scale_w,
            "height": (endY-startY) * scale_h,
            "text": ocr
        })
    return tokens

def parse_annotations(pdf_file: str, ocr_args: dict) -> List[Page]:

    pdf_images = convert_from_path(pdf_file)
    _, pdf_sizes = get_pdf_pages_and_sizes(pdf_file)
    pages = []
    for page_index, (pdf_image, pdf_size) in enumerate(zip(pdf_images, pdf_sizes)):
        tokens = extract_page_tokens(pdf_image, ocr_args, pdf_size)
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


def process_ocr(pdf_file: str, ocr_args: dict):
    """
    Integration for importing annotations from pdfplumber.
    pdf_file: str
        The path to the pdf file to process.
    """
    annotations = parse_annotations(pdf_file, ocr_args)

    return annotations
