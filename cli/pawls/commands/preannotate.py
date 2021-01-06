import os
import json
import logging
from glob import glob
from typing import List, NamedTuple, Union, Dict, Iterable, Any

import click
from tqdm import tqdm

from pawls.commands.utils import LabelingConfiguration, load_json, AnnotationFolder
from pawls.preprocessors.model import *

logger = logging.getLogger(__name__)

PADDING_FOR_SEARCHING_TOKEN_INSIDE_BOX = {"top": 3, "left": 3, "bottom": 3, "right": 3}
PADDING_FOR_RECTIFYING_BLOCK_BOX = {"top": 2, "left": 2, "bottom": 2, "right": 2}


class ModelPredictions:
    """A class for loading model predictions.

    It supports loading predictions directly from a JSON file with the following format:

        {"<name-of-the>.pdf":
                [
                    {
                        "page": {"height": xx, "width": xx, "index": 0},
                        "blocks": [
                            [x, y, w, h, "category"]
                        ]
                    },
                    ....
                ],
        }

    Or you could load predictions from a folder of json files, each with the name of
    <corresponding-pdf-name>.json. And the json format is:

        [
            {
                "page": {"height": xx, "width": xx, "index": 0},
                "blocks": [
                    [x, y, w, h, "category"]
                ]
            },
            ....
        ],

    """

    def __init__(self, pred_file: str):

        if os.path.isfile(pred_file):
            self.pdf_preds = load_json(pred_file)
        elif os.path.isdir(pred_file):
            self.pdf_preds = self.load_directory(pred_file)

    def load_directory(self, pred_dir: str) -> Dict[str, Dict]:

        pdf_preds = {}

        for pred_json in glob(f"{pred_dir}/*.json"):

            filename = os.path.basename(pred_json).replace(".json", ".pdf")
            self.pdf_preds[filename] = load_json(pred_json)

        return pdf_preds

    @property
    def all_pdfs(self) -> List[str]:
        """Obtain all pdfs in the ModelPredictions"""
        return list(self.pdf_preds.keys())

    def get_pdf_annotations_per_page(self, pdf_name):

        pdf_pred = self.pdf_preds[pdf_name]

        for page_pred in pdf_pred:

            # Create a pseudo "page", where tokens are actually blocks.
            yield Page(
                page=PageInfo(**page_pred["page"]),
                tokens=self.load_page_blocks(page_pred["blocks"]),
            )

    @staticmethod
    def load_page_blocks(boxes: List[Any]) -> List[Block]:
        return [
            Block(x=x, y=y, width=w, height=h, label=label)
            for (x, y, w, h, label) in boxes
        ]


def find_token_data(all_token_data, index):

    for token_data in all_token_data:
        if token_data.page.index == index:
            return token_data

    return None


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=click.File("r"))
@click.argument("pred_file", type=click.Path(file_okay=True))
@click.option(
    "--annotator",
    "-u",
    # multiple=True,
    help="Preannotate for the specified annotator.",
)
def preannotate(
    path: click.Path, config: click.File, pred_file: click.Path, annotator: List
):
    """
    Preannotate the PDFs with model prediction results.

    Firstly, you need to generate the region bounding box predictions using some models.
    And it should be stored in a format that's compatible with the ModelPredictions format.

    We've provided a exemplar script for generating predictions for PDF files in <>.

    You also need to preprocess the PDFs in the <labeling_folder> use the `pawls preprocess` command.

    To prepopulate predictions for PDFs in the <labeling_folder> for some annotator, you could use:
        pawls preannoate <labeling_folder> <labeling_config> <pred_file> -u markn --allow-overlapping
    """

    anno_folder = AnnotationFolder(path)
    model_pred = ModelPredictions(pred_file)

    config_labels = LabelingConfiguration(config).get_labels()

    assert annotator in anno_folder.all_annotators, f"Invalid Annotator {annotator}"

    for pdf_name in tqdm(model_pred.all_pdfs):

        if pdf_name not in anno_folder.all_pdfs:
            logger.warning(f"The {pdf_name} is not in the annotation folder. Skipped")

        source_token_data = anno_folder.get_pdf_tokens(pdf_name)
        annotation_file = anno_folder.create_annotation_file(pdf_name, annotator)

        anno_count = 0
        for page_blocks in model_pred.get_pdf_annotations_per_page(pdf_name):

            page_index = page_blocks.page.index
            page_tokens = find_token_data(source_token_data, page_index)

            if page_tokens is None:
                logger.warning(
                    f"There's no token data for page {page_index} in {pdf_name}. Skipped"
                )
                continue

            page_blocks.scale_like(page_tokens)  # Ensure they have the same size

            for block_id, block in enumerate(page_blocks.tokens):

                if block.label not in config_labels:
                    logger.warning(
                        f"The {block_id}-th block in page {page_index} of {pdf_name} has invalid labels. Skipped"
                    )
                    continue

                contained_tokens = page_tokens.filter_tokens_by(
                    block, soft_margin=PADDING_FOR_SEARCHING_TOKEN_INSIDE_BOX
                )

                token_indices = contained_tokens.keys()
                contained_tokens = contained_tokens.values()

                # Rectify the block based on the contained tokens
                if len(contained_tokens) >= 1:
                    rectified_block = union_boxes(contained_tokens)
                else:
                    rectified_block = block.copy()
                rectified_block.pad(**PADDING_FOR_RECTIFYING_BLOCK_BOX)

                annotation_file.add_annotation(
                    page_index=page_index,
                    label=config_labels[block.label],
                    bounds=rectified_block.as_bounds(),
                    token_indices=token_indices,
                )
                anno_count += 1

        annotation_file.save()
        logger.info(f"Successfully stored {anno_count} annotations for {pdf_name}.")
