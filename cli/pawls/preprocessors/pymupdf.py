from typing import List

import pandas as pd
import fitz as pymupdf

from pawls.preprocessors.model import Page, Token


class PymupdfTokenExtractor:
    @staticmethod
    def convert_to_pagetoken(row: pd.Series) -> Token:
        """Convert a row in a DataFrame to pagetoken"""
        return dict(
            text=row["text"],
            x=row["x0"],
            width=row["width"],
            y=row["top"],
            height=row["height"],
        )

    def extract(self, pdf_path: str) -> List[Page]:
        """Extracts token text, positions, and style information from a PDF file.

        Args:
            pdf_path (str): the path to the pdf file.
            include_lines (bool, optional): Whether to include line tokens. Defaults to False.

        Returns:
            PdfAnnotations: A `PdfAnnotations` containing all the paper token information.
        """
        with open(pdf_path, "rb") as fp:
            pdf_object = pymupdf.Document(stream=fp.read())
        if pdf_object.is_encrypted:
            print(f"Abandon encrypted file: {pdf_path}")
            return None

        pages = []
        for page_id, cur_page in enumerate(pdf_object.pages()):
            cur_page = cur_page.get_textpage()
            tokens = self.obtain_word_tokens(cur_page)
            cur_page_info = cur_page.extractDICT()

            page = dict(
                page=dict(
                    width=float(cur_page_info["width"]),
                    height=float(cur_page_info["height"]),
                    index=page_id,
                ),
                tokens=tokens,
            )
            pages.append(page)

        return pages

    def obtain_word_tokens(self, cur_page: pymupdf.fitz.TextPage) -> List[Token]:
        """Obtain all words from the current page.
        Args:
            cur_page (pdfplumber.page.Page):
                the pdfplumber.page.Page object with PDF token information

        Returns:
            List[PageToken]:
                A list of page tokens stored in PageToken format.
        """
        words = cur_page.extractWORDS()
        page_info = cur_page.extractDICT()

        if len(words) == 0:
            return []

        df = pd.DataFrame(words)
        df.rename(
            columns={0: "x0", 1: "top", 2: "x1", 3: "bottom", 4: "text"}, inplace=True
        )

        # Avoid boxes outside the page
        df[["x0", "x1"]] = (
            df[["x0", "x1"]]
            .clip(lower=0, upper=int(page_info["width"]))
            .astype("float")
        )
        df[["top", "bottom"]] = (
            df[["top", "bottom"]]
            .clip(lower=0, upper=int(page_info["height"]))
            .astype("float")
        )

        df["height"] = df["bottom"] - df["top"]
        df["width"] = df["x1"] - df["x0"]

        word_tokens = df.apply(self.convert_to_pagetoken, axis=1).tolist()
        return word_tokens


def process_pymupdf(pdf_file: str):
    """
    Integration for importing annotations from pymupdf.
    pdf_file: str
        The path to the pdf file to process.
    """
    pdf_extractors = PymupdfTokenExtractor()
    annotations = pdf_extractors.extract(pdf_file)

    return annotations
