import os
import shutil
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

    def test_set_pdf_comments(self):

        self.client.post(
            f"/api/doc/{self.pdf_sha}/comments",
            json="hello this is a comment.",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        assert response.json()["papers"][0]["comments"] == "hello this is a comment."

    def test_set_pdf_finished(self):

        self.client.post(
            f"/api/doc/{self.pdf_sha}/finished",
            json=True,
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        assert response.json()["papers"][0]["finished"] is True

    def test_set_pdf_junk(self):

        self.client.post(
            f"/api/doc/{self.pdf_sha}/junk",
            json=True,
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        assert response.json()["papers"][0]["junk"] is True

    def test_get_allocation_info(self):

        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )

        gold = {
            "papers": [
                {
                    "sha": "3febb2bed8865945e7fddc99efd791887bb7e14f",
                    "name": "3febb2bed8865945e7fddc99efd791887bb7e14f",
                    "annotations": 0,
                    "relations": 0,
                    "finished": False,
                    "junk": False,
                    "comments": "",
                    "completedAt": None,
                }
            ],
            "hasAllocatedPapers": True
        }
        assert response.json() == gold

        # Now check that authorized but un-allocated users see all pdfs,
        # but have hasAllocatedPapers set to false:
        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example2@gmail.com"},
        )

        assert response.json()["papers"] == gold["papers"]
        assert response.json()["hasAllocatedPapers"] == False

    def test_get_tokens(self):

        response = self.client.get(f"/api/doc/{self.pdf_sha}/tokens")

        data = response.json()
        assert len(data) == 11

        # Wrong pdf sha should return 404
        response = self.client.get(f"/api/doc/not_a_pdf_sha/tokens")
        assert response.status_code == 404

    def test_get_annotations(self):
        # All requests in this test are authenticated as this user.
        headers = {"X-Auth-Request-Email": "example@gmail.com"}

        # Initially there are no annotations
        response = self.client.get(
            f"/api/doc/{self.pdf_sha}/annotations", headers=headers
        )
        assert response.json() == {"annotations": [], "relations": []}

        # Now, post an annotation
        annotation = {
            "id": "this-is-an-id",
            "page": 1,
            "label": {"text": "label1", "color": "red"},
            "bounds": {"left": 1.0, "top": 4.3, "right": 5.1, "bottom": 2.5},
            "tokens": None,
        }
        self.client.post(
            f"/api/doc/{self.pdf_sha}/annotations",
            json={"annotations": [annotation], "relations": []},
            headers=headers,
        )

        # And now, the annotation should be there
        response = self.client.get(
            f"/api/doc/{self.pdf_sha}/annotations", headers=headers
        )
        assert response.json() == {"annotations": [annotation], "relations": []}

        # and the status should have been updated with the annotation count:
        response = self.client.get(
            "/api/annotation/allocation/info",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )

        assert response.json()["papers"][0]["annotations"] == 1
