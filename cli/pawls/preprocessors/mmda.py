import json
import logging
from pathlib import Path
from typing import List

from mmda.parsers.pdfplumber_parser import PDFPlumberParser


class MMDAExtractor:
    def extract(self, pdf_path: str) -> List[dict]:
        """Extracts token text, positions, and style information from a PDF file.
        This extractor has a side effect of saving the MMDA doc as well.

        Args:
            pdf_path (str): the path to the pdf file.

        Returns:
            list[dict]: A list of `dict` objects with token information
        """
        parser = PDFPlumberParser()
        doc = parser.parse(pdf_path)

        with open(Path(pdf_path).parent.joinpath("mmda.json"), "w") as mmda_out:
            mmda_out.write(json.dumps(doc.to_json()))

        pages = []

        for mmda_page_i, mmda_page in enumerate(doc.pages):
            tokens = []
            w = mmda_page.metadata.width
            h = mmda_page.metadata.height

            if mmda_page.metadata.user_unit != 1.0:
                logging.warning(
                    f"Page {mmda_page_i} in {pdf_path} has non-default UserUnit!"
                )

            for mmda_token in mmda_page.tokens:
                assert len(mmda_token.spans) == 1, "Unexpected span count"

                mmda_box = mmda_token.spans[0].box
                tokens.append(
                    dict(
                        x=mmda_box.l * w,
                        y=mmda_box.t * h,
                        width=mmda_box.w * w,
                        height=mmda_box.h * h,
                        text=mmda_token.text,
                    )
                )

            pages.append(
                dict(
                    page=dict(width=w, height=h, index=mmda_page_i),
                    tokens=tokens,
                )
            )

        return pages


def process_mmda(pdf_file: str):
    """
    Integration for importing annotations from MMDA's default PDFPlumberParser config.
    pdf_file: str
        The path to the pdf file to process.
    """
    pdf_extractors = MMDAExtractor()
    annotations = pdf_extractors.extract(pdf_file)

    return annotations
