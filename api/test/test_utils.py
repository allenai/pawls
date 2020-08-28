import os
import unittest
import tempfile

from app.utils import bulk_fetch_pdfs_for_s2_ids


class TestUtils(unittest.TestCase):

    def test_bulk_fetch_pdfs(self):

        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:
            bulk_fetch_pdfs_for_s2_ids([sha], tempdir)
            assert os.path.exists(os.path.join(tempdir, sha + ".pdf"))

    def test_bulk_fetch_nonexistent_pdfs(self):

        shas = ["abc", "34f25a8704614163c4095b3ee2fc969b60de4698"]
        with tempfile.TemporaryDirectory() as tempdir:
            errors = bulk_fetch_pdfs_for_s2_ids(shas, tempdir)
            assert os.path.exists(os.path.join(tempdir, shas[1] + ".pdf"))

            assert errors["error"] == []
            assert errors["not_found"] == ["abc"]


if __name__ == "__main__":
    unittest.main()
