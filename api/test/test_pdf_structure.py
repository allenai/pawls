import unittest

from app import pdf_structure
from fastapi import HTTPException


class TestPdfStructure(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.sha = "34f25a8704614163c4095b3ee2fc969b60de4698"

    def test_get_annotations(self):
        annotations = pdf_structure.get_annotations(self.sha, token_sources=["all"])
        assert annotations["tokens"]["sources"]["grobid"] is not None

    def test_get_annotations_bad_pdf(self):
        with self.assertRaises(HTTPException):
            _ = pdf_structure.get_annotations("not a sha", token_sources=["all"])

    def test_filter_token_source_pages(self):
        annotations = pdf_structure.get_annotations(self.sha, token_sources=["all"])
        filtered = pdf_structure.filter_token_source_for_pages(
            annotations, pages=[2, 3]
        )

        assert len(filtered["tokens"]["sources"]["grobid"]["pages"]) == 2
        assert filtered["tokens"]["sources"]["grobid"]["pages"][0]["page"]["index"] == 2
        assert filtered["tokens"]["sources"]["grobid"]["pages"][1]["page"]["index"] == 3

    def test_filter_text_element_pages(self):
        annotations = pdf_structure.get_annotations(
            self.sha, text_element_sources=["all"]
        )
        filtered = pdf_structure.filter_text_elements_for_pages(
            annotations, pages=[2, 3]
        )

        pages = {2, 3}
        for source, data in filtered["text_elements"]["sources"].items():
            for element_type, element_data in data["types"].items():
                for item in element_data:
                    assert item["start"]["page"] in pages

    def test_filter_regions_pages(self):
        annotations = pdf_structure.get_annotations(self.sha, region_sources=["all"])
        filtered = pdf_structure.filter_regions_for_pages(annotations, pages=[2, 3])

        pages = {2, 3}
        for source, data in filtered["regions"]["sources"].items():
            for element_type, element_data in data["types"].items():
                for item in element_data:
                    assert item["page"]["index"] in pages
