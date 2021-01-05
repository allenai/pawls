import json
import click
from typing import List, Dict, Iterable
from glob import glob
import os
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1

DEVELOPMENT_USER = "development_user@example.com"


def load_json(filename: str):
    with open(filename, "r") as fp:
        return json.load(fp)


def get_pdf_pages_and_sizes(filename: str):
    """Ref https://stackoverflow.com/a/47686921"""
    with open(filename, "rb") as fp:
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        num_pages = resolve1(document.catalog["Pages"])["Count"]
        page_sizes = [
            (int(page.mediabox[2]), int(page.mediabox[3]))
            for page in PDFPage.create_pages(document)
        ]
        return num_pages, page_sizes


class LabelingConfiguration:
    def __init__(self, config: click.File):
        """LabelingConfiguration handles parsing the configuration file.

        Args:
            config (click.File): The config file handle.
        """
        self.config = json.load(config)

    @property
    def categories(self) -> List[str]:
        """Returns all labeling category names in the config file."""
        return [l["text"] for l in self.config["labels"]]

    @property
    def relations(self):
        raise NotImplementedError

    def get_labels(self) -> Dict[str, str]:
        """Returns a dictionary for category, color pairs in the config file."""
        return {l["text"]: l["color"] for l in self.config["labels"]}


class AnnotationFolder:
    DEFAULT_PDF_STRUCTURE_NAME = "pdf_structure.json"

    def __init__(self, path, pdf_structure_name=None):

        self.path = path
        self.pdf_structure_name = pdf_structure_name or self.DEFAULT_PDF_STRUCTURE_NAME

    def get_all_annotators(self) -> List[str]:
        """Fetch all annotators in the labeling folder,
        including the default DEVELOPMENT_USER.
        """

        return [DEVELOPMENT_USER] + [
            os.path.splitext(e)[0] for e in os.listdir(f"{self.path}/status")
        ]

    def get_all_pdf_names(self) -> List[str]:
        """Fetch all pdf names in the labeling folder,"""
        return [os.path.basename(pdf_path) for pdf_path in glob(f"{self.path}/*/*.pdf")]

    def get_pdf_structure_filename(self, pdf_name: str) -> str:
        """Get the pdf structure json file path for a pdf name

        Args:
            pdf_name (str): the name of the pdf file, e.g., xxx.pdf

        Raises:
            FileNotFoundError:
                When the pdf_structure is not found for this pdf_name, raise a FileNotFoundError.

        Returns:
            str: the pdf_structure file path for this pdf file.
        """

        sha = os.path.basename(pdf_name).replace(".pdf", "")

        pdf_structure_path = f"{self.path}/{sha}/{self.pdf_structure_name}"

        if os.path.exists(pdf_structure_path):
            return pdf_structure_path
        else:
            raise FileNotFoundError(
                f"pdf_structure is not found for {sha}.Did you forget run the following command?\n    pawls preprocess <processor-name> {self.path}/{sha}/{pdf_name}"
            )


class AnnotationFiles:
    def __init__(
        self, labeling_folder: str, annotator: str, include_unfinished: bool = True
    ):
        """AnnotationFiles is an iterator for selected annotation files
        given the selected annotators and configurations.

        Args:
            labeling_folder (str):
                The folder to save the pdf annotation files, e.g.,
                `./skiff_files/apps/pawls/papers`.
            annotator (str, optional):
                The name of the annotator.
                If not set, then changed to the default user
                `AnnotationFiles.DEVELOPMENT_USER`.
            include_unfinished (bool, optional):
                Whether output unfinished annotations of the given user.
                Defaults to True.
        """
        self.labeling_folder = labeling_folder

        self.annotator = annotator
        self.include_unfinished = include_unfinished

        if self.include_unfinished:
            self._files = self.get_all_annotation_files()
        else:
            self._files = self.get_finished_annotation_files()

    def get_all_annotation_files(self) -> List[str]:
        return glob(
            os.path.join(f"{self.labeling_folder}/*/{self.annotator}_annotations.json")
        )

    def get_finished_annotation_files(self) -> List[str]:

        user_assignment_file = f"{self.labeling_folder}/status/{self.annotator}.json"
        if not os.path.exists(user_assignment_file):
            print(
                "Warning:",
                f"The user annotation file does not exist: {user_assignment_file}",
            )
            return self.get_all_annotation_files()

        user_assignment = load_json(user_assignment_file)
        return [
            f"{self.labeling_folder}/{pdf_sha}/{self.annotator}_annotations.json"
            for pdf_sha, assignment in user_assignment.items()
            if (assignment["finished"] and not assignment["junk"])
        ]

    def __iter__(self) -> Iterable[Dict]:

        for _file in self._files:
            paper_sha = _file.split("/")[-2]
            pdf_path = f"{self.labeling_folder}/{paper_sha}/{paper_sha}.pdf"

            yield dict(
                paper_sha=paper_sha,
                pdf_path=pdf_path,
                annotation_path=_file,
            )

    def __len__(self):

        return len(self._files)