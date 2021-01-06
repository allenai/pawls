import os
import shutil
import unittest
import tempfile
import json

from click.testing import CliRunner

from pawls.commands import preannotate
from pawls.commands import preprocess


def _load_json(filename: str):
    with open(filename, "r") as fp:
        return json.load(fp)


class TestPreannotate(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.TEST_ANNO_DIR = "test/fixtures/pawls/"
        self.TEST_CONFIG_FILE = "test/fixtures/configuration.json"
        self.TEST_ANNO_FILE = "test/fixtures/anno.json"

        self.PDF_SHAS = [
            "3febb2bed8865945e7fddc99efd791887bb7e14f",
            "34f25a8704614163c4095b3ee2fc969b60de4698",
            "553c58a05e25f794d24e8db8c2b8fdb9603e6a29",
        ]
        self.USERS = ["markn@example.com", "shannons@example.com"]
        self.DEFAULT_USER = "development_user@example.com"

    def test_add_annotation(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:

            sub_temp_dir = os.path.join(tempdir, "pawls")
            shutil.copytree(self.TEST_ANNO_DIR, sub_temp_dir)

            result = runner.invoke(preprocess, ["grobid", sub_temp_dir])

            result = runner.invoke(
                preannotate,
                [sub_temp_dir, self.TEST_CONFIG_FILE, self.TEST_ANNO_FILE]
                + sum([["-u", user] for user in self.USERS], []),
            )

            assert result.exit_code == 0

            for pdf_sha in self.PDF_SHAS:
                for user in self.USERS:
                    assert os.path.exists(
                        os.path.join(sub_temp_dir, pdf_sha, f"{user}_annotations.json")
                    )

    def test_add_annotation_without_preprocess(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:

            sub_temp_dir = os.path.join(tempdir, "pawls")
            shutil.copytree(self.TEST_ANNO_DIR, sub_temp_dir)

            result = runner.invoke(
                preannotate,
                [
                    sub_temp_dir,
                    self.TEST_CONFIG_FILE,
                    self.TEST_ANNO_FILE,
                    "-u",
                    self.USERS[0],
                ],
            )

            assert result.exit_code == 1 # It should raise an exception
