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
        os.makedirs(self.TEST_DIR, exist_ok=True)
        copy_and_overwrite(
            "test/fixtures/data/",
            os.path.join(self.TEST_DIR, "papers")
        )

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
        assert response.json() == ["test", "label"]

    def test_get_allocations(self):

        response = self.client.get(
            "/api/annotation/allocation",
            headers={"X-Auth-Request-Email": "example@gmail.com"},
        )
        assert response.json() == ["paper1", "paper2"]

        # No header, should return all pdfs.
        response = self.client.get("/api/annotation/allocation")
        assert response.json() == []

        # Header, no annotations
        response = self.client.get(
            "/api/annotation/allocation",
            headers={"X-Auth-Request-Email": "nonexistent@gmail.com"},
        )
        assert response.status_code == 404
