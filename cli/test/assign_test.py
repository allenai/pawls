import os
import unittest
import tempfile
import json

from click.testing import CliRunner

from pawls.commands import assign, fetch


class TestAssign(unittest.TestCase):
    def test_assign_annotator(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark@example.org"])
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(tempdir, "status", "mark@example.org.json"))

    def test_assign_annotator_with_bad_name(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark!!!   ABC"])
            assert result.exit_code == 2
            assert "Provided annotator was not a valid email." in result.output

    def test_assign_unfetched_pdfs(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(assign, [tempdir, "mark@example.org", sha])
            assert result.exit_code == 2
            assert "Found shas which are not present" in result.output

    def test_assign_pdfs(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(fetch, [tempdir, sha])
            assert result.exit_code == 0
            result = runner.invoke(assign, [tempdir, "mark@example.org", sha])
            assert result.exit_code == 0
            status_path = os.path.join(tempdir, "status", "mark@example.org.json")

            annotator_json = json.load(open(status_path))
            assert annotator_json == {
                sha: {
                    "annotations": 0,
                    "relations": 0,
                    "finished": False,
                    "junk": False,
                    "comments": "",
                    "completedAt": None,
                }
            }
