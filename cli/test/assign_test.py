import os
import unittest
import tempfile
import json
import shutil

from click.testing import CliRunner

from pawls.commands import assign


class TestAssign(unittest.TestCase):
    def test_assign_annotators(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark"])
            assert result.exit_code == 0
            os.listdir(tempdir)
            assert os.path.exists(os.path.join(tempdir, "status", "mark.json"))

    def test_assign_annotator(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark"])
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(tempdir, "status", "mark.json"))

    def test_assign_annotator_with_bad_name(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark!!!   ABC"])
            assert result.exit_code == 2
            assert "Annotator names should be alphanumeric" in result.output

    def test_assign_unfetched_pdfs(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark", sha])
            assert result.exit_code == 2
            assert "Found shas which are not present" in result.output

    def test_assign_pdfs(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:

            # Copy the fixture in, as though it was there already.
            sub_temp_dir = os.path.join(tempdir, "pdfs")
            shutil.copytree(f"test/fixtures/pawls/", sub_temp_dir)
            result = runner.invoke(assign, [sub_temp_dir, "mark", sha])
            assert result.exit_code == 0
            status_path = os.path.join(sub_temp_dir, "status", "mark.json")

            annotator_json = json.load(open(status_path))
            assert annotator_json == {
                sha: {
                    "sha": sha,
                    "name": sha,
                    "annotations": 0,
                    "relations": 0,
                    "finished": False,
                    "junk": False,
                    "comments": "",
                    "completedAt": None,
                }
            }

    def test_assign_pdfs_with_name_file(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:

            # Copy the fixture in, as though it was there already.
            sub_temp_dir = os.path.join(tempdir, "pdfs")
            shutil.copytree(f"test/fixtures/pawls/", sub_temp_dir)
            # This time we pass a file containing the name mapping,
            # so we should find the name in the resulting status.
            result = runner.invoke(assign, [sub_temp_dir, "mark", sha, "--name-file", "test/fixtures/pawls/name_mapping.json"])
            assert result.exit_code == 0
            status_path = os.path.join(sub_temp_dir, "status", "mark.json")

            annotator_json = json.load(open(status_path))
            assert annotator_json == {
                sha: {
                    "sha": sha,
                    "name": "Dropout: a simple way to prevent neural networks from overfitting",
                    "annotations": 0,
                    "relations": 0,
                    "finished": False,
                    "junk": False,
                    "comments": "",
                    "completedAt": None,
                }
            }
