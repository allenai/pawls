import os
import unittest
import tempfile
import json

from click.testing import CliRunner

from pawls.commands import status

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
    with open(filename, 'r') as fp:
        return json.load(fp)


class TestStatus(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.TEST_ANNO_DIR = "test/fixtures/pawls/"
        self.TEST_CONFIG_FILE = 'test/fixtures/configuration.json'
        self.PDF_SHAS = [
            "3febb2bed8865945e7fddc99efd791887bb7e14f",
            "34f25a8704614163c4095b3ee2fc969b60de4698",
            "553c58a05e25f794d24e8db8c2b8fdb9603e6a29",
        ]
        self.USERS = ["markn", "shannons"]
        self.DEFAULT_USER = "development_user"

    def test_status(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tempdir:
            result = runner.invoke(
                status, [self.TEST_ANNO_DIR])
            assert result.exit_code == 0

if __name__ == "__main__":
    unittest.main()
