import os
import unittest
import tempfile

from click.testing import CliRunner

from pawls.commands.fetch import fetch


class TestFetch(unittest.TestCase):
    def test_fetch_pdfs(self):
        runner = CliRunner()
        sha = "34f25a8704614163c4095b3ee2fc969b60de4698"
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(fetch, [sha, tempdir])
            assert result.exit_code == 0
            print(os.path.join(tempdir, sha + ".pdf"))
            print(os.path.exists(os.path.join(tempdir, sha, sha + ".pdf")))

    def test_fetch_nonexistent_pdfs(self):
        runner = CliRunner()
        shas = ["abc", "34f25a8704614163c4095b3ee2fc969b60de4698"]
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(fetch, [*shas, tempdir])
            assert result.exit_code == 0
            assert not os.path.exists(os.path.join(tempdir, shas[0], shas[0] + ".pdf"))
            assert os.path.exists(os.path.join(tempdir, shas[1], shas[1] + ".pdf"))


if __name__ == "__main__":
    unittest.main()
