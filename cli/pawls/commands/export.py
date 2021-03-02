import os
import json
from typing import List, NamedTuple, Union, Dict, Any

import click
import pandas as pd
from tqdm import tqdm
from pdf2image import convert_from_path

from pawls.commands.utils import (
    load_json,
    get_pdf_sha,
    get_pdf_pages_and_sizes,
    LabelingConfiguration,
    AnnotationFolder,
    AnnotationFiles,
)
from pawls.preprocessors.model import *

ALL_SUPPORTED_EXPORT_TYPE = ["coco", "token"]


def _convert_bounds_to_coco_bbox(bounds: Dict[str, Union[int, float]]):
    x1, y1, x2, y2 = bounds["left"], bounds["top"], bounds["right"], bounds["bottom"]
    return x1, y1, x2 - x1, y2 - y1


def find_tokens_in_anno_block(
    anno: Dict, page_token_data: List[Page]
) -> List[Tuple[int, int]]:
    """Given the annotated block, and page tokens, search for tokens within that block.
    Used for searching text from free-form annotations.
    TODO: This function ideally should be done in the UI rather than the cli. We need to
    update this function in the future. 

    Returns:
        List[Tuple[int, int]]: [description]
    """
    tokens = page_token_data[anno["page"]].filter_tokens_by(
        Block.from_annotation(anno), soft_margin=dict(left=2, top=2, bottom=2, right=2)
    )
    return [(anno["page"], tid) for tid in tokens.keys()]


class COCOBuilder:
    class CategoryTemplate(NamedTuple):
        id: int
        name: str
        supercategory: str = None

    class PaperTemplate(NamedTuple):
        id: int
        paper_sha: str
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
        iscrowd: bool = False

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

    def get_image_data(self, paper_sha: str, page_id: int):
        """Find the image data with the given paper_sha and page_id."""
        filename = self._create_pdf_page_image_filename(paper_sha, page_id)
        for data in self._images:
            if data["file_name"] == filename:
                return data

    def _create_pdf_page_image_filename(self, paper_sha: str, page_id: int) -> str:
        return f"{paper_sha}_{page_id}.jpg"

    def _create_coco_categories(self, categories: List) -> List[str]:
        return [
            self.CategoryTemplate(idx, category)._asdict()
            for idx, category in enumerate(categories)
        ]

    def create_paper_data(
        self, annotation_folder: AnnotationFolder, save_images: bool = True
    ):

        _papers = []
        _images = []
        pbar = tqdm(annotation_folder.all_pdf_paths)
        for pdf_path in pbar:
            paper_sha = get_pdf_sha(pdf_path)
            pbar.set_description(f"Working on {paper_sha[:10]}...")

            num_pages, page_sizes = get_pdf_pages_and_sizes(pdf_path)
            pdf_page_images = convert_from_path(pdf_path)

            # Add paper information
            paper_id = len(_papers)  # Start from zero
            paper_info = self.PaperTemplate(
                paper_id,
                paper_sha,
                pages=num_pages,
            )

            current_images = []
            previous_image_id = len(_images)  # Start from zero

            for page_id, page_size in enumerate(page_sizes):
                image_filename = self._create_pdf_page_image_filename(
                    paper_sha, page_id
                )
                width, height = page_size
                current_images.append(
                    self.ImageTemplate(
                        id=previous_image_id + len(current_images),
                        file_name=image_filename,
                        height=height,
                        width=width,
                        paper_id=paper_id,
                        page_number=page_id,
                    )._asdict()
                )
                if save_images and not os.path.exists(
                    f"{self.save_path_image}/{image_filename}"
                ):
                    pdf_page_images[page_id].resize((width, height)).save(
                        f"{self.save_path_image}/{image_filename}"
                    )

            _papers.append(paper_info._asdict())
            _images.extend(current_images)

        self._papers = _papers
        self._images = _images

    def create_annotation_for_annotator(self, anno_files: AnnotationFiles) -> None:
        """Create the annotations for the given annotation files"""

        _annotations = []
        anno_id = 0
        pbar = tqdm(anno_files)
        for anno_file in pbar:

            paper_sha = anno_file["paper_sha"]

            pbar.set_description(f"Working on {paper_sha[:10]}...")
            pawls_annotations = load_json(anno_file["annotation_path"])["annotations"]

            for anno in pawls_annotations:
                page_id = anno["page"]
                category = anno["label"]["text"]

                # Skip if current category is not in the specified categories
                cat_id = self._name2catid.get(category, None)
                if cat_id is None:
                    continue

                image_data = self.get_image_data(paper_sha, page_id)
                width, height = image_data["width"], image_data["height"]

                x, y, w, h = _convert_bounds_to_coco_bbox(anno["bounds"])

                _annotations.append(
                    self.AnnoTemplate(
                        id=anno_id,
                        bbox=[x, y, w, h],
                        category_id=cat_id,
                        image_id=image_data["id"],
                        area=w * h,
                    )._asdict()
                )
                anno_id += 1

        return _annotations

    def create_combined_json_for_annotations(
        self, annotations: List[Dict]
    ) -> Dict[str, Any]:
        return {
            "papers": self._papers,
            "images": self._images,
            "annotations": annotations,
            "categories": self._categories,
        }

    def build_annotations(self, anno_files: AnnotationFiles) -> None:

        annotations = self.create_annotation_for_annotator(anno_files)
        coco_json = self.create_combined_json_for_annotations(annotations)
        self.export(coco_json, f"{anno_files.annotator}.json")

    def export(self, coco_json: Dict, annotation_name="annotations.json") -> None:

        with open(f"{self.save_path}/{annotation_name}", "w") as fp:

            json.dump(coco_json, fp)


class TokenTableBuilder:
    def __init__(self, categories, save_path: str):

        self.categories = categories
        self.save_path = save_path

    def create_paper_data(self, annotation_folder: AnnotationFolder):

        all_page_token_df = {}
        all_page_token_data = {}

        for pdf in annotation_folder.all_pdfs:
            all_page_tokens = annotation_folder.get_pdf_tokens(pdf)
            # Get page token data
            page_token_dfs = []
            for page_tokens in all_page_tokens:
                token_data = [
                    (page_tokens.page.index, idx, token.text)
                    for idx, token in enumerate(page_tokens.tokens)
                ]
                df = pd.DataFrame(token_data, columns=["page_index", "index", "text"])
                df = df.set_index(["page_index", "index"])
                page_token_dfs.append(df)

            page_token_dfs = pd.concat(page_token_dfs)

            all_page_token_df[get_pdf_sha(pdf)] = page_token_dfs
            all_page_token_data[get_pdf_sha(pdf)] = all_page_tokens

        self.all_page_token_df = all_page_token_df
        self.all_page_token_data = all_page_token_data

    def create_annotation_for_annotator(self, anno_files: AnnotationFiles) -> None:

        # Firstly initialize the annotation tables with the annotator name
        annotator = anno_files.annotator
        for token_data in self.all_page_token_df.values():
            token_data[annotator] = None

        pbar = tqdm(anno_files)

        for anno_file in pbar:
            paper_sha = anno_file["paper_sha"]
            df = self.all_page_token_df[paper_sha]
            page_token_data = self.all_page_token_data[paper_sha]

            pawls_annotations = load_json(anno_file["annotation_path"])["annotations"]
            for anno in pawls_annotations:

                # Skip if current category is not in the specified categories
                label = anno["label"]["text"]
                if label not in self.categories:
                    continue

                # Try to find the tokens if they are in free-form annotation mode
                if anno["tokens"] is None:
                    anno_token_indices = find_tokens_in_anno_block(
                        anno, page_token_data
                    )

                    if len(anno_token_indices) == 0:
                        continue

                else:
                    anno_token_indices = [
                        (ele["pageIndex"], ele["tokenIndex"]) for ele in anno["tokens"]
                    ]

                df.loc[anno_token_indices, annotator] = label

    def export(self):

        for pdf, df in self.all_page_token_df.items():
            df["pdf"] = pdf

        df = (
            pd.concat(self.all_page_token_df.values())
            .reset_index()
            .set_index(["pdf", "page_index", "index"])
        )

        df.to_csv(self.save_path)
        return df


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=str)
@click.argument("output", type=click.Path(file_okay=True))
@click.argument("format", type=click.Path(file_okay=False))
@click.option(
    "--annotator",
    "-u",
    multiple=True,
    help="Export annotations of the specified annotator.",
)
@click.option(
    "--categories",
    "-c",
    multiple=True,
    help="Export specified categories in the annotations.",
)
@click.option(
    "--include-unfinished",
    "-i",
    is_flag=True,
    help="A flag to export all annotation by the specified annotator including unfinished ones.",
)
@click.option(
    "--export-images/--no-export-images",
    default=True,
    help="A flag to not to export images of PDFs",
)
def export(
    path: click.Path,
    config: click.File,
    output: click.Path,
    format: str,
    annotator: List,
    categories: List,
    include_unfinished: bool = False,
    export_images: bool = True,
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

    assert (
        format in ALL_SUPPORTED_EXPORT_TYPE
    ), f"Invalid export format {format}. Should be one of {ALL_SUPPORTED_EXPORT_TYPE}."
    print(f"Export the annotations to the {format} format.")

    config = LabelingConfiguration(config)
    annotation_folder = AnnotationFolder(path)

    if len(annotator) == 0:
        all_annotators = annotation_folder.all_annotators
        print(f"Export annotations from all available annotators {all_annotators}")
    else:
        all_annotators = annotator

    if len(categories) == 0:
        categories = config.categories
        print(f"Export annotations from all available categories {categories}")
    else:
        print(f"Export annotations from the following categories {categories}")
        
    if format == "coco":

        coco_builder = COCOBuilder(categories, output)
        print(f"Creating paper data for annotation folder {annotation_folder.path}")
        coco_builder.create_paper_data(annotation_folder, save_images=export_images)

        for annotator in all_annotators:
            print(f"Export annotations from annotators {annotator}")

            anno_files = AnnotationFiles(path, annotator, include_unfinished)

            coco_builder.build_annotations(anno_files)

            print(
                f"Successfully exported {len(anno_files)} annotations of annotator {annotator} to {output}."
            )

    elif format == "token":

        if not output.endswith(".csv"):
            output = f"{output}.csv"
        token_builder = TokenTableBuilder(categories, output)

        print(f"Creating paper data for annotation folder {annotation_folder.path}")
        token_builder.create_paper_data(annotation_folder)

        for annotator in all_annotators:

            # print(f"Export annotations from annotators {annotator}")
            anno_files = AnnotationFiles(path, annotator, include_unfinished)
            token_builder.create_annotation_for_annotator(anno_files)

        df = token_builder.export()
        print(
            f"Successfully exported annotations for {len(df)} tokens from annotators {all_annotators} to {output}."
        )