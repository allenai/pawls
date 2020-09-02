from unittest import TestCase
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

        # No header
        response = self.client.get("/api/annotation/allocation")
        assert response.status_code == 401

        # Header, no annotations
        response = self.client.get(
            "/api/annotation/allocation",
            headers={"X-Auth-Request-Email": "nonexistent@gmail.com"},
        )
        assert response.status_code == 404
