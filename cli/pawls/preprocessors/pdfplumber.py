from typing import List, Union, Dict, Dict, Any, Tuple
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
import pdfplumber
import layoutparser as lp

from pdfstructure.client.v1.models import *
from pdfstructure.client.v1.api.default_api import DefaultApi
from pdfstructure.client.v1.configuration import Configuration
from pdfstructure.client.v1.api_client import ApiClient
from pdfstructure.client.v1.exceptions import ApiException

# Monkey dispatching for layoutparser
# Adding a conversion script for pagetokens
def to_pagetoken(self, pdf_page: PdfPage = None) -> PageToken:
    style_name = (self.style if hasattr(self, "style") else "",)
    if pdf_page is None:
        return PageToken(
            text=self.text,
            x=self.coordinates[0],
            y=self.coordinates[1],
            style_name=style_name,
            height=self.height,
            width=self.width,
        )
    else:
        x_1, y_1, x_2, y_2 = self.coordinates
        x_1s, x_2s = np.clip((x_1, x_2), 0, pdf_page.width)
        y_1s, y_2s = np.clip((y_1, y_2), 0, pdf_page.height)
        return PageToken(
            text=self.text,
            x=x_1s,
            y=y_1s,
            style_name=style_name,
            height=y_2s - y_1s,
            width=x_2s - x_1s,
        )


def to_dict(self) -> Dict[str, Any]:
    res = dict(
        x_1=self.coordinates[0],
        y_1=self.coordinates[1],
        x_2=self.coordinates[2],
        y_2=self.coordinates[3],
        text=self.text,
    )
    if hasattr(self, "style"):
        res["style"] = self.style
    return res


lp.Rectangle.to_pagetoken = to_pagetoken
lp.TextBlock.to_pagetoken = to_pagetoken
lp.TextBlock.to_dict = to_dict


class BasePDFTokenExtractor(ABC):
    """PDF token extractors will load all the *tokens* and save using pdfstructure service."""

    def __call__(self, pdf_path: str) -> PdfAnnotations:
        return self.extract(pdf_path)

    @abstractmethod
    def extract(self, pdf_path: str) -> PdfAnnotations:
        """Extract PDF Tokens from the input pdf_path

        Args:
            pdf_path (str):
                The path to a downloaded PDF file or a pdf SHA,
                e.g., sha://004cff2a0ed89f5f3855690f3fd2cc2778dc1a8e

        Returns:
            (PdfAnnotations):
                The PDF document structure are saved in the pdf-structure-service format
                https://github.com/allenai/s2-pdf-structure-service/tree/master/clients/python
        """

    @property
    @abstractmethod
    def NAME(self) -> str:
        """The name of the TokenExtractor"""


class PDFStyles:
    """Automatically storing and indexing the font styles in a PDF file"""

    DEFAULT = ("default", 0)

    def __init__(self):
        self._styles = {self.DEFAULT: "0"}

    def add(self, token_style: Any) -> str:
        """Add token_style and return the index of the style

        Args:
            token_style (Any):
                1. A Dict contains both the "fontname" and "size"
                2. A tuple for (<fontname>, "size")
                3. Something else -> it will be treated as a deault syle

        Returns:
            str:
                The id of the style.
        """
        if isinstance(token_style, dict):
            if "fontname" not in token_style:
                return self.add_non_token(token_style)

            prop = (token_style["fontname"], token_style["size"])
        elif isinstance(token_style, tuple):
            prop = token_style

        if prop in self._styles:
            return self._styles[prop]
        else:
            self._styles[prop] = style_id = str(len(self._styles))
            return style_id

    def add_non_token(self, token_style: Any) -> str:
        """It will return the index of the default style for some strange token styles"""
        return self._styles[self.DEFAULT]

    def export(self) -> Dict[str, Any]:
        """Generate a dictionary for <style_index>: (<fontname>, "size")"""
        return {
            val: {
                "color": 0,
                "family": key[0],
                "font_style": None,
                "font_type": None,
                "size": float(key[1]),
                "width": None,
            }
            for key, val in self._styles.items()
        }


class PDFPlumberTokenExtractor(BasePDFTokenExtractor):

    NAME = "pdfplumber"
    IMAGE_TOKEN_TEXT = "##LTFigure##"

    @staticmethod
    def convert_to_pagetoken(row: pd.Series) -> PageToken:
        """Convert a row in a DataFrame to pagetoken"""
        return PageToken(
            text=row["text"],
            x=row["x0"],
            width=row["width"],
            y=row["top"],
            height=row["height"],
            style_name=row["style_id"],
        )

    @staticmethod
    def is_scanned_page_image(
        image_box: lp.elements.BaseCoordElement, pdf_page: PdfPage
    ) -> bool:
        """Determine whether the whole page is a scanned image"""
        if image_box.area > 0.95 * pdf_page.height * pdf_page.width:
            if image_box.x_1 <= pdf_page.width * 0.02:
                if image_box.y_1 <= pdf_page.height * 0.02:
                    return True

        return False

    def extract(self, pdf_path: str) -> PdfAnnotations:
        """Extracts token text, positions, and style information from a PDF file.

        Args:
            pdf_path (str): the path to the pdf file.
            include_lines (bool, optional): Whether to include line tokens. Defaults to False.

        Returns:
            PdfAnnotations: A `PdfAnnotations` containing all the paper token information.
        """
        plumber_pdf_object = pdfplumber.open(pdf_path)

        all_image_regions = []
        all_page_tokens = []

        styles = PDFStyles()
        for page_id in range(len(plumber_pdf_object.pages)):
            cur_page = plumber_pdf_object.pages[page_id]
            pdf_page = PdfPage(
                page_id, width=int(cur_page.width), height=int(cur_page.height)
            )

            word_tokens = self.obtain_word_tokens(cur_page, pdf_page, styles)
            image_tokens, image_regions = self.obtain_images(cur_page, pdf_page, styles)

            all_image_regions.append(PageRegions(pdf_page, image_regions))
            all_page_tokens.append(
                PageTokens(page=pdf_page, tokens=word_tokens + image_tokens)
            )

        all_annotation = PdfAnnotations(
            tokens=TokenSources(
                sources={
                    self.NAME: PdfTokens(pages=all_page_tokens, styles=styles.export())
                }
            ),
            regions=RegionSources(
                sources={self.NAME: RegionTypes({"image": all_image_regions})}
            ),
        )

        return all_annotation

    def obtain_word_tokens(
        self, cur_page: pdfplumber.page.Page, pdf_page: PdfPage, styles: PDFStyles
    ) -> List[PageToken]:
        """Obtain all words from the current page.
        Args:
            cur_page (pdfplumber.page.Page):
                the pdfplumber.page.Page object with PDF token information
            pdf_page (PdfPage):
                the PdfPage object from pdfstructure service
            styles (PDFStyles):
                the PDFStyles object containing all styles in the given PDF.

        Returns:
            List[PageToken]:
                A list of page tokens stored in PageToken format.
        """
        words = cur_page.extract_words(
            x_tolerance=1.5,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=False,
            horizontal_ltr=True,
            vertical_ttb=True,
            extra_attrs=["fontname", "size"],
        )

        df = pd.DataFrame(words)

        # Avoid boxes outside the page
        df[["x0", "x1"]] = (
            df[["x0", "x1"]].clip(lower=0, upper=pdf_page.width).astype("float")
        )
        df[["top", "bottom"]] = (
            df[["top", "bottom"]].clip(lower=0, upper=pdf_page.height).astype("float")
        )

        df["height"] = df["bottom"] - df["top"]
        df["width"] = df["x1"] - df["x0"]

        df["style_id"] = df.apply(
            lambda row: styles.add((row["fontname"], row["size"])), axis=1
        )

        word_tokens = df.apply(self.convert_to_pagetoken, axis=1).tolist()
        return word_tokens

    def obtain_images(
        self, cur_page: pdfplumber.page.Page, pdf_page: PdfPage, styles: PDFStyles
    ) -> Tuple[List[PageToken], List[Region]]:
        """Extract images from the given page.

        Args:
            cur_page (pdfplumber.page.Page):
                the pdfplumber.page.Page object with PDF token information
            pdf_page (PdfPage):
                the PdfPage object from pdfstructure service
            styles (PDFStyles):
                the PDFStyles object containing all styles in the given PDF.

        Returns:
            Tuple[List[PageToken], List[Region]]:
                For non-whole-page scans, it will store them as PageTokens.
                For whole-page scans, it will store them as regions.
        """
        image_tokens = []
        image_regions = []

        for im in cur_page.images:
            image_box = lp.Rectangle(
                float(im["x0"]), float(im["y0"]), float(im["x1"]), float(im["y1"])
            )
            if not self.is_scanned_page_image(image_box, pdf_page):
                image_box.style = styles.add(im)
                image_box.text = self.IMAGE_TOKEN_TEXT
                image_tokens.append(image_box.to_pagetoken(pdf_page))
            else:
                image_regions.append(
                    Region(
                        x=image_box.x_1,
                        y=image_box.y_1,
                        width=image_box.width,
                        height=image_box.height,
                    )
                )
        return image_tokens, image_regions


def process_pdfplumber(
    sha: str,
    pdf_file: str,
    source: str = "pdfplumber",
    env: str = "dev",
):
    """
    Integration for importing annotations from grobid.
    Depends on a grobid API built from our fork https://github.com/allenai/grobid.
    Fetches a PDF by sha, sends it to the Grobid API and inserts the resulting annotations
    Does nothing if Grobid annotations already exist for that PDF.

    sha: str
        The s2 sha for a pdf.
    pdf_file: str
        The path to the pdf file to process.
    grobid_host: str (optional, default = http://s2-grobid-tokens.us-west-2.elasticbeanstalk.com)
        The forked grobid API which we use to produce the annotations.
    source: str (optional, default = "grobid")
        The source name to use for inserting into the pdf structure service.
    env: str (optional, default = "dev")
        Whether to insert pdfs into the development
        or production version of the pdf structure service.
    """
    client = DefaultApi(
        ApiClient(
            Configuration(
                host=f"http://pdf-structure-{env}.us-west-2.elasticbeanstalk.com"
            )
        )
    )

    pdf_extractors = PDFPlumberTokenExtractor()
    annotations = pdf_extractors.extract(pdf_file)

    existing_annotations = client.get_annotations(
        sha, text_element_data="none", token_data="none"
    )

    if existing_annotations.tokens and source in existing_annotations.tokens.sources:
        return True

    try:
        client.add_annotations(sha, annotations)
        return True
    except ApiException as e:
        print(f"{sha} could not be downloaded due to {e}")
        return False