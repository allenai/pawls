import os
import unittest
import tempfile

from click.testing import CliRunner

from pawls.commands import fetch


class TestFetch(unittest.TestCase):
    def test_fetch_pdfs(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(fetch, [tempdir, sha])
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(tempdir, sha, sha + ".pdf"))
            assert os.path.exists(os.path.join(tempdir, sha, "metadata.json"))

    def test_fetch_nonexistent_pdfs(self):
        runner = CliRunner()
        shas = ["abc", "34f25a8704614163c4095b3ee2fc969b60de4698"]
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(fetch, [tempdir, *shas])
            assert result.exit_code == 1
            assert not os.path.exists(os.path.join(tempdir, shas[0], shas[0] + ".pdf"))


if __name__ == "__main__":
    unittest.main()
