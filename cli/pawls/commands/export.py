import os
import json
import re
import click
from click import UsageError, BadArgumentUsage
from collections import OrderedDict
from glob import glob
from typing import List, NamedTuple, Optional, Union, Dict, Iterable, Any

from tqdm import tqdm
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1
from pdf2image import convert_from_path

from pawls.commands.assign import LabelingStatus


def _load_json(filename: str):
    with open(filename, 'r') as fp:
        return json.load(fp)


def _convert_bounds_to_coco_bbox(bounds: Dict[str, Union[int, float]]):
    x1, y1, x2, y2 = bounds["left"], bounds["top"], bounds["right"], bounds["bottom"]
    return x1, y1, x2-x1, y2-y1


def _get_pdf_pages_and_sizes(filename: str):
    """Ref https://stackoverflow.com/a/47686921
    """
    with open(filename, 'rb') as fp:
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        num_pages = resolve1(document.catalog['Pages'])['Count']
        page_sizes = [(int(page.mediabox[2]), int(page.mediabox[3]))
                      for page in PDFPage.create_pages(document)]
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
        """Returns all labeling category names in the config file."
        """
        return [l['text'] for l in self.config['labels']]

    @property
    def relations(self):
        raise NotImplementedError


class AnnotationFiles:

    DEVELOPMENT_USER = "development_user"

    def __init__(self, labeling_folder: str, annotator: str, include_unfinished: bool = True):
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
        return glob(os.path.join(f"{self.labeling_folder}/*/{self.annotator}_annotations.json"))

    def get_finished_annotation_files(self) -> List[str]:

        user_assignment_file = f"{self.labeling_folder}/status/{self.annotator}.json"
        if not os.path.exists(user_assignment_file):
            print("Warning:",
                  f"The user annotation file does not exist: {user_assignment_file}")
            return self.get_all_annotation_files()

        user_assignment = _load_json(user_assignment_file)
        return [
            f"{self.labeling_folder}/{pdf_sha}/{self.annotator}_annotations.json"
            for pdf_sha, assignment in user_assignment.items()
            if assignment['status'] == LabelingStatus.FINISHED
        ]

    def __iter__(self) -> Iterable[Dict]:

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

    @staticmethod
    def get_all_annotators(labeling_folder: str) -> List[str]:
        """Fetch all annotators in the labeling folder, 
        including the default DEVELOPMENT_USER.
        """

        return [AnnotationFiles.DEVELOPMENT_USER] + \
             [os.path.splitext(e)[0] for e in os.listdir(f"{labeling_folder}/status")]


class COCOBuilder:

    class CategoryTemplate(NamedTuple):
        id: int
        name: str
        supercategory: str = None

    class PaperTemplate(NamedTuple):
        id: int
        paper_sha: str
        year: Optional[int]
        title: str
        pages: int

    class ImageTemplate(NamedTuple):
        id: int
        file_name: str
        height: Union[float, int]
        width: Union[float, int]
        paper_id: int
        page_number: int

    class AnnoTemplate(NamedTuple):
        id: int
        bbox: List
        image_id: int
        category_id: int
        area: Union[float, int]

    def __init__(self, categories: List, save_path: str):
        """COCOBuilder generates the coco-format dataset based on 
        source annotation files. 

        It will create a COCO-format annotation json file for every
        annotated page and convert all the labeled pdf pages into 
        images, which is stored in `<save_path>/images/<pdf_sha>_<page no>.jpg`. 

        Args:
            categories (List): 
                All the labeling categories in the dataset
            save_path (str): 
                The folder for saving all the annotation files. 

        Examples::
            >>> anno_files = AnnotationFiles(**configs) # Initialize anno_files based on configs
            >>> coco_builder = COCOBuilder(["title", "abstract"], "export_path")
            >>> coco_builder.build_annotations(anno_files)
            >>> coco_builder.export()
        """
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

    def _create_pdf_page_image_filename(self, paper_sha: str, page_id: int) -> str:
        return f"{paper_sha}_{page_id}.jpg"

    def _create_coco_categories(self, categories: List) -> List[str]:
        return [
            self.CategoryTemplate(idx, category)._asdict()
            for idx, category in enumerate(categories)
        ]

    def add_paper(self, paper_sha: str, 
                        pdf_path: str, 
                        metadata_path: str, 
                        annotation_path: str) -> None:
        """Create the annotation for each paper. 
        """
        paper_metadata = _load_json(metadata_path)
        assert paper_metadata["sha"] == paper_sha

        num_pages, page_sizes = _get_pdf_pages_and_sizes(pdf_path)

        # Add paper information
        paper_id = len(self._papers)  # Start from zero
        paper_info = self.PaperTemplate(
            paper_id,
            paper_sha,
            paper_metadata.get("year"),
            paper_metadata.get("title", ""),
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
                    self.ImageTemplate(
                        id=previous_image_id + len(current_images),
                        file_name=image_filename,
                        height=height,
                        width=width,
                        paper_id=paper_id,
                        page_number=anno['page'],
                    )._asdict()

            if not os.path.exists(f"{self.save_path_image}/{image_filename}"):
                pdf_page_images[anno['page']].resize((width, height)).save(
                    f"{self.save_path_image}/{image_filename}")

            page_image_id = current_images[anno['page']]['id']
            x, y, w, h = _convert_bounds_to_coco_bbox(anno['bounds'])

            current_annotations.append(
                self.AnnoTemplate(
                    id=previous_anno_id + len(current_annotations),
                    bbox=[x, y, w, h],
                    category_id=self._name2catid[anno['label']['text']],
                    image_id=page_image_id,
                    area=w*h,
                )._asdict()
            )

        # After all information collection finishes,
        # add the data to the object storage
        self._papers.append(paper_info._asdict())
        self._images.extend(list(current_images.values()))
        self._annotations.extend(current_annotations)

    def create_combined_json(self) -> Dict[str, Any]:
        return {
            "papers": self._papers,
            "images": self._images,
            "annotations": self._annotations,
            "categories": self._categories,
        }

    def build_annotations(self, anno_files: AnnotationFiles) -> None:

        pbar = tqdm(anno_files)
        for anno_file in pbar:
            pbar.set_description(
                f"Working on {anno_file['paper_sha'][:10]}...")
            self.add_paper(**anno_file)

    def export(self, annotation_name="annotations.json") -> None:

        with open(f"{self.save_path}/{annotation_name}", "w") as fp:

            json.dump(self.create_combined_json(), fp)


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=click.File('r'))
@click.argument("output", type=click.Path(file_okay=False))
@click.option(
    "--annotator",
    "-u",
    multiple=True,
    help="Export annotations of the specified annotator.",
)
@click.option(
    "--include-unfinished",
    "-i",
    is_flag=True,
    help="A flag to export all annotation by the specified annotator including unfinished ones.",
)
def export(
    path: click.Path,
    config: click.File,
    output: click.Path,
    annotator: List,
    include_unfinished: bool = False,
):
    """
    Export the COCO annotations for an annotation project.

    To export all annotations of a project of all annotators, use:
        `pawls export <labeling_folder> <labeling_config> <output_path>`

    To export only finished annotations of from specified annotators, e.g. markn and shannons, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn -u shannons`.

    To export all annotations of from a given annotator, use:
        `pawls export <labeling_folder> <labeling_config> <output_path> -u markn --include-unfinished`.
    """

    config = LabelingConfiguration(config)
    
    all_annotators = AnnotationFiles.get_all_annotators(path)
    
    if len(annotator) == 0:
        annotator = all_annotators
        print(f"Export annotations from all available annotators {all_annotators}")
    else:
        print(f"Export annotations from annotators {annotator}")

    for anno in annotator:

        output_folder = output if len(annotator) == 1 else f"{output}/{anno}"

        anno_files = AnnotationFiles(path, anno, include_unfinished)
        coco_builder = COCOBuilder(config.categories, output_folder)

        coco_builder.build_annotations(anno_files)
        coco_builder.export()

        print(f"Successfully exported {len(anno_files)} annotations of annotator {anno} to {output}.")