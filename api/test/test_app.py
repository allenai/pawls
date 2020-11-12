import shutil
import os
from unittest import TestCase

from fastapi.testclient import TestClient

from main import app


def copy_and_overwrite(from_path: str, to_path: str):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)


class TestApp(TestCase):
    def setUp(self):
        super().setUp()

        self.client = TestClient(app)
        self.TEST_DIR = "test/fixtures/tmp/"
        copy_and_overwrite("test/fixtures/data/", self.TEST_DIR)
        copy_and_overwrite(
            "test/fixtures/status/", os.path.join(self.TEST_DIR, "status")
        )
        self.pdf_sha = "3febb2bed8865945e7fddc99efd791887bb7e14f"

    def tearDown(self):
        shutil.rmtree(self.TEST_DIR)

    def test_root(self):
        response = self.client.get("/")
        assert response.status_code == 204
        assert response.json() == {}

    def test_get_bad_pdf(self):

        response = self.client.get("/api/doc/not_a_pdf/pdf")
        assert response.status_code == 404

    def test_get_labels(self):
        response = self.client.get("/api/annotation/labels")
        assert response.json() == [
            {"text": "Figure Text", "color": "#70DDBA"},
            {"text": "Section Header", "color": "#FFD45D"},
        ]

    def test_get_relations(self):
        response = self.client.get("/api/annotation/relations")
        assert response.json() == [
            {"text": "Caption Of", "color": "#70DDBA"},
            {"text": "Definition", "color": "#FFD45D"},
        ]

    def test_set_pdf_status(self):

        status = {
            "annotations": 3,
            "relations": 2,
            "status": "DONE",
            "comments": "",
            "completedAt": None,
        }

        self.client.post(
            f"/api/doc/{self.pdf_sha}/status",
            json=status,
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        assert response.json()[0]["status"] == status

    def test_get_allocation_info(self):

        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )

        gold = [
            {
                "metadata": {
                    "sha": "3febb2bed8865945e7fddc99efd791887bb7e14f",
                    "title": "Deep contextualized word representations",
                    "venue": "NAACL-HLT",
                    "year": 2018,
                    "cited_by": 3723,
                    "authors": [
                        "Matthew E. Peters",
                        "Mark Neumann",
                        "Mohit Iyyer",
                        "Matt Gardner",
                        "Christopher Clark",
                        "Kenton Lee",
                        "Luke Zettlemoyer",
                    ],
                },
                "status": {
                    "annotations": 0,
                    "relations": 0,
                    "status": "INPROGRESS",
                    "comments": "",
                    "completedAt": None,
                },
                "sha": "3febb2bed8865945e7fddc99efd791887bb7e14f",
            }
        ]
        assert response.json() == gold

        # No header, should return all pdfs.
        response = self.client.get("/api/annotation/allocation/info")
        print(response.json())
        print(gold)
        assert response.json() == gold

    def test_get_annotations(self):
        # Empty
        response = self.client.get(f"/api/doc/{self.pdf_sha}/annotations")
        assert response.json() == {"annotations": [], "relations": []}
        annotation = {
            "id": "this-is-an-id",
            "page": 1,
            "label": {"text": "label1", "color": "red"},
            "bounds": {"left": 1.0, "top": 4.3, "right": 5.1, "bottom": 2.5},
            "tokens": None,
        }

        response = self.client.post(
            f"/api/doc/{self.pdf_sha}/annotations",
            json={"annotations": [annotation], "relations": []},
        )
        # Annotation should be there.
        response = self.client.get(f"/api/doc/{self.pdf_sha}/annotations")
        assert response.json() == {"annotations": [annotation], "relations": []}
