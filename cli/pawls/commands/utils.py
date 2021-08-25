import json
from typing import List, Dict, Iterable
from glob import glob
import os
import uuid

import click
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1

from pawls.preprocessors.model import load_tokens_from_file


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


def get_pdf_sha(pdf_file_name: str) -> str:
    return os.path.basename(pdf_file_name).replace(".pdf", "")


class LabelingConfiguration:
    def __init__(self, config: str):
        """LabelingConfiguration handles parsing the configuration file.

        Args:
            config (str): The config file path.
        """

        self.config = load_json(config)

    @property
    def categories(self) -> List[str]:
        """Returns all labeling category names in the config file."""
        return [l["text"] for l in self.config["labels"]]

    @property
    def relations(self):
        raise NotImplementedError

    def get_labels(self) -> Dict[str, Dict]:
        """Returns a dictionary for category name, label pairs in the config file."""
        return {l["text"]: l for l in self.config["labels"]}


class AnnotationFolder:
    DEFAULT_PDF_STRUCTURE_NAME = "pdf_structure.json"

    def __init__(self, path:str, pdf_structure_name:str=None, pdf_shas: List[str] = None):
        """
        Args:
            path (str): path to the annotation folder.
            pdf_structure_name (str, optional):
                The name of the pdf_token file name for each pdf file.
                Defaults to pdf_structure.json.
            pdf_shas (List[str], optional):
                Only find pdf annotation from the given list of pdf_shas.
                Defaults to None.
        """

        self.path = path
        self.pdf_structure_name = pdf_structure_name or self.DEFAULT_PDF_STRUCTURE_NAME

        self.all_pdf_paths = [pdf_path for pdf_path in glob(f"{self.path}/*/*.pdf")]
        if pdf_shas is not None:
            self.all_pdf_paths = [
                ele for ele in self.all_pdf_paths if ele.split("/")[-2] in pdf_shas
            ]
        self.all_pdfs = [os.path.basename(pdf_path) for pdf_path in self.all_pdf_paths]

    @property
    def all_annotators(self) -> List[str]:
        """Fetch all annotators in the labeling folder,
        including the default DEVELOPMENT_USER.
        """

        return set([DEVELOPMENT_USER] + [
            os.path.splitext(e)[0] for e in os.listdir(f"{self.path}/status")
        ]) # The DEVELOPMENT_USER annotator might be duplicated 

    def get_pdf_tokens(self, pdf_name: str) -> List["Page"]:
        """Get the pdf tokens for a pdf name by loading from the corresponding pdf_structure file.

        Args:
            pdf_name (str): the name of the pdf file, e.g., xxx.pdf

        Raises:
            FileNotFoundError:
                When the pdf_structure is not found for this pdf_name, raise a FileNotFoundError.

        Returns:
            str: the pdf_structure file path for this pdf file.
        """

        sha = get_pdf_sha(pdf_name)
        pdf_structure_path = f"{self.path}/{sha}/{self.pdf_structure_name}"

        if os.path.exists(pdf_structure_path):
            return load_tokens_from_file(pdf_structure_path)
        else:
            raise FileNotFoundError(
                f"pdf_structure is not found for {sha}.Did you forget run the following command?\n    pawls preprocess <processor-name> {self.path}/{sha}/{pdf_name}"
            )

    def create_annotation_file(self, pdf_name: str, annotator: str) -> "AnnotationFile":
        """Create an annotation file for the given pdf name and annotator.

        Returns:
            AnnotationFile:
                An AnnotationFile object that used for creating annotations.
        """
        sha = get_pdf_sha(pdf_name)
        annotation_file_path = f"{self.path}/{sha}/{annotator}_annotations.json"

        return AnnotationFile(annotation_file_path)


class AnnotationFile:
    def __init__(self, filepath: str):
        """Annotation file is used to help creating the annotation
        files manually.

        Args:
            filepath (str): the path to store the annotation file.
        """
        self.filepath = filepath
        self.data = {"annotations": [], "relations": []}

    def add_annotation(
        self,
        page_index: int,
        label: Dict[str, str],
        bounds: Dict[str, int],
        token_indices: List[int] = [],
    ):
        """Add an annotation to the given paper.

        Args:
            page_index (int):
                The page index of this annotation.
            label (Dict[str, str]):
                The label (text and color) of this annotation.
            bounds (Dict[str, int]):
                The bounding box coordinates of the block.
            token_indices (List[int], optional):
                A list of the indices of the contained tokens.
                Defaults to [].
        """
        annotation = {
            "id": str(uuid.uuid4()),
            "page": page_index,
            "label": label,
            "bounds": bounds,
            "tokens": [
                {"pageIndex": page_index, "tokenIndex": token_id}
                for token_id in token_indices
            ],
        }

        self.data["annotations"].append(annotation)

    def add_relations(self):
        raise NotImplementedError()

    def save(self):
        """Save the annotation file in the designated filepath"""
        if os.path.exists(self.filepath):
            while True:
                overwrite = input(
                    f"Overwrite existing annotations {self.filepath}? [Y/N]\n"
                ).lower()
                if overwrite in ["y", "n"]:
                    if overwrite == "n":
                        return None
                    break
                print("Please enter Y or N.")

        with open(self.filepath, "w") as fp:
            json.dump(self.data, fp)


class AnnotationFiles:
    def __init__(
        self,
        labeling_folder: str,
        annotator: str,
        include_unfinished: bool = True,
        pdf_shas: List[str] = None,
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
            pdf_shas (List[str], optional):
                Only find pdf annotation from the given list of pdf_shas.
                Defaults to None.
        """
        self.labeling_folder = labeling_folder

        self.annotator = annotator
        self.include_unfinished = include_unfinished

        if pdf_shas is not None:
            self._files = self.get_annotation_files_from_pdf_shas(pdf_shas)
        else:
            if self.include_unfinished:
                self._files = self.get_all_annotation_files()
            else:
                self._files = self.get_finished_annotation_files()

    def get_all_annotation_files(self) -> List[str]:
        return glob(
            os.path.join(f"{self.labeling_folder}/*/{self.annotator}_annotations.json")
        )

    def get_annotation_files_from_pdf_shas(self, pdf_shas: List) -> List[str]:
        return [
            file
            for file in self.get_all_annotation_files()
            if file.split("/")[-2] in pdf_shas
        ]

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
            pdf_sha = _file.split("/")[-2]
            pdf_path = f"{self.labeling_folder}/{pdf_sha}/{pdf_sha}.pdf"

            yield dict(
                paper_sha=pdf_sha,
                pdf_path=pdf_path,
                annotation_path=_file,
            )

    def __len__(self):

        return len(self._files)