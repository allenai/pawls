import os
import unittest
import json
from click.testing import CliRunner

from pawls.commands.metadata import metadata


class TestMetadata(unittest.TestCase):
    def tearDown(self):
        meta_path = (
            "test/fixtures/data/3febb2bed8865945e7fddc99efd791887bb7e14f/metadata.json"
        )
        os.remove(meta_path)
        super().tearDown()

    def test_fetch_metadata(self):

        correct_meta = {
            "sha": "3febb2bed8865945e7fddc99efd791887bb7e14f",
            "title": "Deep contextualized word representations",
            "venue": "NAACL-HLT",
            "year": 2018,
            "cited_by": 3723,
            "authors": [
                "Matthew E. Peters",
                "Mark Neumann",
                "Mohit Iyyer",
                "Matt Gardner",
                "Christopher Clark",
                "Kenton Lee",
                "Luke Zettlemoyer",
            ],
        }
        meta_path = (
            "test/fixtures/data/3febb2bed8865945e7fddc99efd791887bb7e14f/metadata.json"
        )
        runner = CliRunner()
        result = runner.invoke(metadata, ["test/fixtures/data"])
        assert result.exit_code == 0
        meta = json.load(open(meta_path, "r"))
        assert meta["sha"] == correct_meta["sha"]
        assert meta["title"] == correct_meta["title"]


if __name__ == "__main__":
    unittest.main()
