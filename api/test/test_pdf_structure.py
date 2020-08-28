
import unittest

from app.pdf_structure import get_annotations
from fastapi import HTTPException


class TestPdfStructure(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.sha = "34f25a8704614163c4095b3ee2fc969b60de4698"

    def test_get_annotations(self):
        annotations = get_annotations(self.sha, token_sources=["all"])
        assert annotations["tokens"]["sources"]["grobid"] is not None

    def test_get_annotations_bad_pdf(self):
        with self.assertRaises(HTTPException):
            _ = get_annotations("not a sha", token_sources=["all"])
