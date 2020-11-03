import os
import tempfile
from unittest import TestCase

from app.pre_serve import maybe_download_pdfs, Configuration


class TestPreServe(TestCase):
    def test_maybe_download_pdfs(self):
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as temp_dir:

            config = Configuration(
                output_directory=temp_dir,
                labels=[],
                relations=[],
                pdfs=[sha],
                preprocessors=[]
            )

            maybe_download_pdfs(config)
            assert os.path.exists(os.path.join(temp_dir, sha, f"{sha}.pdf"))
            assert os.path.exists(os.path.join(temp_dir, sha, "metadata.json"))

    def test_maybe_download_pdfs_skips_existing(self):
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = os.path.join(temp_dir, sha)
            os.makedirs(existing_dir)
            with open(os.path.join(existing_dir, "abc.pdf"), "w") as f:
                f.write("No PDF")

            config = Configuration(
                output_directory=temp_dir,
                labels=[],
                relations=[],
                pdfs=[sha],
                preprocessors=[]
            )

            maybe_download_pdfs(config)
            with open(os.path.join(existing_dir, "abc.pdf")) as f:
                assert f.read() == "No PDF"
            assert not os.path.exists(os.path.join(temp_dir, sha, "metadata.json"))
