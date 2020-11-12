import os
from typing import Tuple

import click
from click import UsageError, BadArgumentUsage
import json
import glob
import re
from loguru import logger
from glob import glob


class LabelingConfiguration:

    def __init__(self, config):
        self.config = json.load(config)

    @property
    def categories(self):
        return [l['text'] for l in self.config['labels']]


class AnnotationFiles:

    DEVELOPMENT_USER = "development_user"

    def __init__(self, labeling_folder: str, annotator: str = None, enforce_all: bool = True):

        self.labeling_folder = labeling_folder

        if annotator is None:
            self.annotator = self.DEVELOPMENT_USER
            self.enforce_all = True
        else:
            self.annotator = annotator
            self.enforce_all = enforce_all

        if self.enforce_all:
            self._files = self.get_all_annotation_files()
        else:
            self._files = self.get_finished_annotation_files()

    def get_all_annotation_files(self):
        return glob(os.path.join(f"{self.labeling_folder}/*/{self.annotator}_annotations.json"))

    def get_finished_annotation_files(self):

        user_assignment_file = f"{self.labeling_folder}/status/{self.annotator}.json"
        if not os.path.exists(user_assignment_file):
            logger.warning(
                f"The user annotation file does not exist: {user_assignment_file}")
            return self.get_all_annotation_files()

        user_assignment = _load_json(user_assignment_file)
        return [
            f"{self.labeling_folder}/{pdf_sha}/{self.annotator}_annotations.json"
            for pdf_sha, assignment in user_assignment.items()
            if assignment['status'] == LabelingStatus.FINISHED
        ]

    def __iter__(self):

        for _file in self._files:
            paper_sha = _file.split('/')[-2]
            pdf_path = f"{self.labeling_folder}/{paper_sha}/{paper_sha}.pdf"
            metadata_path = f"{self.labeling_folder}/{paper_sha}/metadata.json"

            yield dict(
                paper_sha=paper_sha,
                pdf_path=pdf_path,
                metadata_path=metadata_path,
                annotation_path=_file
            )

    def __len__(self):

        return len(self._files)


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=click.File('r'))
@click.argument("output", type=click.Path(file_okay=False))
@click.option(
    "--annotator",
    "-u",
    type=str,
    help="Export annotations of the specified annotator.",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="A flag to export all annotation by the specified annotator.",
)
def export(
    path: click.Path,
    config: click.File,
    output: click.Path,
    annotator: str = None,
    all: bool = False,
):
    """
    Export the annotations for a project.

    To export all annotations of a project of the default annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path>`

    To export only finished annotations of from a given annotator, e.g. markn, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn`.

    To export all annotations of from a given annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn --all`.
    """


    pass