import os
import unittest
import tempfile
import json

from click.testing import CliRunner

from pawls.commands import assign, fetch


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
            result = runner.invoke(fetch, [tempdir, sha])
            result = runner.invoke(assign, [tempdir, "mark", sha])
            assert result.exit_code == 0
            status_path = os.path.join(tempdir, "status", "mark.json")

            annotator_json = json.load(open(status_path))
            assert annotator_json == {
                sha: {
                    "annotations": 0,
                    "relations": 0,
                    "status": "INPROGRESS",
                    "comments": "",
                    "completed_at": None,
                }
            }
