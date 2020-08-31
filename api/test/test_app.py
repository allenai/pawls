from unittest import TestCase
from unittest import mock
import tempfile
from fastapi.testclient import TestClient

from main import app


class TestApp(TestCase):
    def setUp(self):
        super().setUp()

        self.client = TestClient(app)

    def test_root(self):
        response = self.client.get("/")
        assert response.status_code == 204
        assert response.json() == {}

    def test_get_bad_pdf(self):

        response = self.client.get("/api/pdf/not_a_pdf")
        assert response.status_code == 404

    def test_get_pdf_and_download(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch("app.pdf_structure.Config.PDF_STORE_PATH", temp_dir):
                sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
                response = self.client.get(f"/api/pdf/{sha}?download=true")

                assert response.status_code == 200
