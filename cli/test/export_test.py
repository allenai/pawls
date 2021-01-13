import os
import unittest
import tempfile
import json

import pandas as pd
from click.testing import CliRunner

from pawls.commands import export

"""
Details of annotations in test/fixtures/pawls/

There are three task:
0. 3febb2bed8865945e7fddc99efd791887bb7e14f
1. 34f25a8704614163c4095b3ee2fc969b60de4698
2. 553c58a05e25f794d24e8db8c2b8fdb9603e6a29

* Development user has annotations for all images 
* markn is assigned to task 0 and task 1
* markn finishes task 1 but not task 0
* shannons is assigned to task 1 and task 2
* shannons finishes neither of the tasks 
* shannons does not have any annotations for task 1
"""


def _load_json(filename: str):
    with open(filename, "r") as fp:
        return json.load(fp)


class TestExportCOCO(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.TEST_ANNO_DIR = "test/fixtures/pawls/"
        self.TEST_CONFIG_FILE = "test/fixtures/configuration.json"
        self.PDF_SHAS = [
            "3febb2bed8865945e7fddc99efd791887bb7e14f",
            "34f25a8704614163c4095b3ee2fc969b60de4698",
            "553c58a05e25f794d24e8db8c2b8fdb9603e6a29",
        ]
        self.USERS = ["markn@example.com", "shannons@example.com"]
        self.DEFAULT_USER = "development_user@example.com"

    def test_export_annotation_from_all_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export, [self.TEST_ANNO_DIR, self.TEST_CONFIG_FILE, tempdir, "coco"]
            )
            assert result.exit_code == 0

            assert os.path.exists(os.path.join(tempdir, self.USERS[0] + ".json"))
            assert os.path.exists(os.path.join(tempdir, self.USERS[1] + ".json"))
            assert os.path.exists(os.path.join(tempdir, self.DEFAULT_USER + ".json"))
            assert os.path.exists(os.path.join(tempdir, "images"))

    def test_export_annotation_from_multiple_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    tempdir,
                    "coco",
                    "-u",
                    self.USERS[0],
                    "-u",
                    self.USERS[1],
                ],
            )
            assert result.exit_code == 0

            assert os.path.exists(os.path.join(tempdir, self.USERS[0] + ".json"))
            assert os.path.exists(os.path.join(tempdir, self.USERS[1] + ".json"))
            assert not os.path.exists(
                os.path.join(tempdir, self.DEFAULT_USER + ".json")
            )
            assert os.path.exists(os.path.join(tempdir, "images"))

    def test_export_annotation_with_all_annotators_annotations(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    tempdir,
                    "coco",
                    "-u",
                    self.USERS[0],
                    "--include-unfinished",
                ],
            )
            assert result.exit_code == 0

            anno = _load_json(os.path.join(tempdir, f"{self.USERS[0]}.json"))
            paper_shas = [ele["paper_sha"] for ele in anno["papers"]]

            assert self.PDF_SHAS[1] in paper_shas
            assert self.PDF_SHAS[0] in paper_shas

    def test_export_annotation_with_missing_annotation_file(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    tempdir,
                    "coco",
                    "-u",
                    self.USERS[1],
                    "--include-unfinished",
                ],
            )
            assert result.exit_code == 0

            anno_file = _load_json(os.path.join(tempdir, f"{self.USERS[1]}.json"))
            paper_sha_map = {ele["id"]: ele["paper_sha"] for ele in anno_file["papers"]}
            image_paper_map = {
                ele["id"]: ele["paper_id"] for ele in anno_file["images"]
            }
            all_paper_shas = [
                paper_sha_map[image_paper_map[anno["image_id"]]]
                for anno in anno_file["annotations"]
            ]

            assert self.PDF_SHAS[2] in all_paper_shas
            assert self.PDF_SHAS[1] not in all_paper_shas


class TestExportToken(TestExportCOCO):
    def test_export_annotation_from_all_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            saved_path = f"{tempdir}/annotations.csv"
            result = runner.invoke(
                export, [self.TEST_ANNO_DIR, self.TEST_CONFIG_FILE, saved_path, "token"]
            )
            assert result.exit_code == 0
            assert os.path.exists(saved_path)

            df = pd.read_csv(saved_path)
            for annotator in self.USERS + [self.DEFAULT_USER]:
                assert annotator in df.columns

    def test_export_annotation_from_multiple_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            saved_path = f"{tempdir}/annotations.csv"
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    saved_path,
                    "token",
                    "-u",
                    self.USERS[0],
                    "-u",
                    self.USERS[1],
                ],
            )
            assert result.exit_code == 0
            assert os.path.exists(saved_path)

            df = pd.read_csv(saved_path)
            for annotator in self.USERS:
                assert annotator in df.columns


if __name__ == "__main__":
    unittest.main()
