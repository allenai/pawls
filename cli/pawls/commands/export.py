import os
from typing import Tuple

import click
from click import UsageError, BadArgumentUsage
import json
import glob
import re
from loguru import logger
from glob import glob
from tqdm import tqdm
from collections import OrderedDict
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1
from pdf2image import convert_from_path

from pawls.commands.assign import LabelingStatus


def _load_json(filename):
    with open(filename, 'r') as fp:
        return json.load(fp)


def _convert_bounds_to_coco_bbox(bounds):
    x1, y1, x2, y2 = bounds["left"], bounds["top"], bounds["right"], bounds["bottom"]
    return x1, y1, x2-x1, y2-y1


def _get_pdf_pages_and_sizes(filename):
    """Ref https://stackoverflow.com/a/47686921
    """
    with open(filename, 'rb') as fp:
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        num_pages = resolve1(document.catalog['Pages'])['Count']
        page_sizes = [(int(page.mediabox[2]), int(page.mediabox[3]))
                      for page in PDFPage.create_pages(document)]
        return num_pages, page_sizes


class COCOBuilder:

    CATEGORY_TEMPLATE = staticmethod(lambda id, category, supercategory=None: {
        "supercategory": supercategory, "id": id, "name": category
    })
    PAPER_TEMPLATE = staticmethod(lambda id, paper_sha, year=None, title=None, pages=None: {
        "id": id, "paper_sha": paper_sha, "year": year, "title": title, "pages": pages
    })
    IMAGE_TEMPLATE = staticmethod(lambda id, file_name, height, width, paper_id, page_number: {
        "id": id, "file_name": file_name, "height": height, "width": width, "paper_id": paper_id, "page_number": page_number
    })
    ANNO_TEMPLATE = staticmethod(lambda id, bbox, category_id, image_id, area: {
        "id": id, "bbox": bbox, "category_id": category_id, "image_id": image_id, "area": area
    })

    def __init__(self, categories, save_path):

        # Create Paths
        self.save_path = save_path
        self.save_path_image = f"{self.save_path}/images"
        os.makedirs(self.save_path, exist_ok=True)
        os.makedirs(self.save_path_image, exist_ok=True)

        # Internal COCO information storage
        self._categories = self._create_coco_categories(categories)
        self._name2catid = {ele["name"]: ele["id"] for ele in self._categories}
        self._images = []
        self._papers = []
        self._annotations = []

    def _create_pdf_page_image_filename(self, paper_sha, page_id):
        return f"{paper_sha}_{page_id}.jpg"

    def _create_coco_categories(self, categories):
        return [
            self.CATEGORY_TEMPLATE(idx, category)
            for idx, category in enumerate(categories)
        ]

    def add_paper(self, paper_sha, pdf_path, metadata_path, annotation_path):

        paper_metadata = _load_json(metadata_path)
        assert paper_metadata["sha"] == paper_sha

        num_pages, page_sizes = _get_pdf_pages_and_sizes(pdf_path)

        # Add paper information
        paper_id = len(self._papers)  # Start from zero
        paper_info = self.PAPER_TEMPLATE(
            paper_id,
            paper_sha,
            paper_metadata.get("year"),
            paper_metadata.get("title"),
            pages=num_pages
        )

        # Add individual page images and annotations
        current_images = OrderedDict()
        current_annotations = []
        previous_image_id = len(self._images)  # Start from zero
        previous_anno_id = len(self._annotations)  # Start from zero

        pdf_page_images = convert_from_path(pdf_path)
        pawls_annotations = _load_json(annotation_path)
        pawls_annotations = pawls_annotations['annotations']
        for anno in pawls_annotations:
            page_id = anno['page']

            image_filename = self._create_pdf_page_image_filename(
                paper_sha, page_id)
            width, height = page_sizes[anno['page']]

            if page_id not in current_images:
                current_images[anno['page']] = \
                    self.IMAGE_TEMPLATE(
                        id=previous_image_id + len(current_images),
                        file_name=image_filename,
                        height=height,
                        width=width,
                        paper_id=paper_id,
                        page_number=anno['page'],
                )

            if not os.path.exists(f"{self.save_path_image}/{image_filename}"):
                pdf_page_images[anno['page']].resize((width, height)).save(
                    f"{self.save_path_image}/{image_filename}")

            page_image_id = current_images[anno['page']]['id']
            x, y, w, h = _convert_bounds_to_coco_bbox(anno['bounds'])

            current_annotations.append(
                self.ANNO_TEMPLATE(
                    id=previous_anno_id + len(current_annotations),
                    bbox=[x, y, w, h],
                    category_id=self._name2catid[anno['label']['text']],
                    image_id=page_image_id,
                    area=w*h,
                )
            )

        # After all information collection finishes,
        # add the data to the object storage
        self._papers.append(paper_info)
        self._images.extend(list(current_images.values()))
        self._annotations.extend(current_annotations)

    def create_combined_json(self):
        return {
            "papers": self._papers,
            "images": self._images,
            "annotations": self._annotations,
            "categories": self._categories,
        }

    def build_annotations(self, anno_files):

        pbar = tqdm(anno_files)
        for anno_file in pbar:
            pbar.set_description(
                f"Working on {anno_file['paper_sha'][:10]}...")
            self.add_paper(**anno_file)

    def export(self, annotation_name="annotations.json"):

        with open(f"{self.save_path}/{annotation_name}", "w") as fp:

            json.dump(self.create_combined_json(), fp)


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
    Export the COCO annotations for a project.

    To export all annotations of a project of the default annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path>`

    To export only finished annotations of from a given annotator, e.g. markn, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn`.

    To export all annotations of from a given annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn --all`.
    """

    config = LabelingConfiguration(config)
    anno_files = AnnotationFiles(path, annotator, all)
    coco_builder = COCOBuilder(config.categories, output)

    coco_builder.build_annotations(anno_files)
    coco_builder.export()

    logger.info(
        f"Successfully exported {len(anno_files)} annotations to {output}.")
