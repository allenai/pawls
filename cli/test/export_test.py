import os
import unittest
import tempfile
import json

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


class TestExport(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.TEST_ANNO_DIR = "test/fixtures/pawls/"
        self.TEST_CONFIG_FILE = "test/fixtures/configuration.json"
        self.PDF_SHAS = [
            "3febb2bed8865945e7fddc99efd791887bb7e14f",
            "34f25a8704614163c4095b3ee2fc969b60de4698",
            "553c58a05e25f794d24e8db8c2b8fdb9603e6a29",
        ]
        self.USERS = ["markn", "shannons"]
        self.DEFAULT_USER = "development_user"

    def test_export_annotation_from_all_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export, [self.TEST_ANNO_DIR, self.TEST_CONFIG_FILE, tempdir]
            )
            assert result.exit_code == 0

            assert os.path.exists(os.path.join(tempdir, self.USERS[0]))
            assert os.path.exists(os.path.join(tempdir, self.USERS[1]))
            assert os.path.exists(os.path.join(tempdir, self.DEFAULT_USER))
            assert not os.path.exists(os.path.join(tempdir, "images"))
            assert not os.path.exists(os.path.join(tempdir, "annotations.json"))

    def test_export_annotation_from_multiple_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    tempdir,
                    "-u",
                    self.USERS[0],
                    "-u",
                    self.USERS[1],
                ],
            )
            assert result.exit_code == 0

            assert os.path.exists(os.path.join(tempdir, self.USERS[0]))
            assert os.path.exists(os.path.join(tempdir, self.USERS[1]))
            assert not os.path.exists(os.path.join(tempdir, self.DEFAULT_USER))
            assert not os.path.exists(os.path.join(tempdir, "images"))
            assert not os.path.exists(os.path.join(tempdir, "annotations.json"))

    def test_export_annotation_from_single_annotator(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    tempdir,
                    "-u",
                    self.USERS[0],
                ],
            )
            assert result.exit_code == 0

            assert not os.path.exists(os.path.join(tempdir, self.USERS[0]))
            assert not os.path.exists(os.path.join(tempdir, self.USERS[1]))
            assert not os.path.exists(os.path.join(tempdir, self.DEFAULT_USER))

            assert os.path.exists(os.path.join(tempdir, "images"))
            assert os.path.exists(os.path.join(tempdir, "annotations.json"))

            anno = _load_json(os.path.join(tempdir, "annotations.json"))
            paper_shas = [ele["paper_sha"] for ele in anno["papers"]]

            assert self.PDF_SHAS[1] in paper_shas
            assert self.PDF_SHAS[0] not in paper_shas

            all_img_shas = set(
                [
                    pth.split("_")[0]
                    for pth in os.listdir(os.path.join(tempdir, "images"))
                ]
            )
            assert all_img_shas == set(paper_shas)

    def test_export_annotation_with_all_annotators_annotations(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                export,
                [
                    self.TEST_ANNO_DIR,
                    self.TEST_CONFIG_FILE,
                    tempdir,
                    "-u",
                    self.USERS[0],
                    "--include-unfinished",
                ],
            )
            assert result.exit_code == 0

            anno = _load_json(os.path.join(tempdir, "annotations.json"))
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
                    "-u",
                    self.USERS[1],
                    "--include-unfinished",
                ],
            )
            assert result.exit_code == 0

            anno = _load_json(os.path.join(tempdir, "annotations.json"))
            paper_shas = [ele["paper_sha"] for ele in anno["papers"]]

            assert self.PDF_SHAS[2] in paper_shas
            assert self.PDF_SHAS[1] not in paper_shas


if __name__ == "__main__":
    unittest.main()
