"""This script uses a Mask RCNN model for generating block layouts
for PDF files in the `annotation_folder`.

Usage:
    python generate_pdf_layouts.py --annotation_folder  ../skiff_files/apps/pawls/papers --save_path anno.json

The generated `anno.json` file could be used for `pawls preannotate`.

You might need to install the layout-parser library for running the Mask RCNN
layout detection model. See https://github.com/layout-Parser/layout-parser#installation
"""

import os
import json
from glob import glob
from typing import List

from tqdm import tqdm
import layoutparser as lp
from pdf2image import convert_from_path

import argparse

DEFAULT_MODEL_CONFIG = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config"
DEFAULT_MODEL_WEIGHTS = None  # downloaded automatically from zoo
DEFAULT_MODEL_LABEL_MAP = {
    0: "Paragraph",
    1: "Title",
    2: "ListItem",
    3: "Table",
    4: "Figure",
}

parser = argparse.ArgumentParser()
parser.add_argument("--annotation_folder", type=str, required=True)
parser.add_argument("--save_path", type=str, required=True)
parser.add_argument("--config_path", type=str, required=False)
parser.add_argument("--model_path", type=str, required=False)
parser.add_argument("--label_map_path", type=str, required=False)


def run_prediction(pdf_filename: str) -> List:
    """It returns a list of block predictions.
    Each item corresponds to a page in the pdf file:
        [
            {
                "page": {"height": xx, "width": xx, "index": 0},
                "blocks": [
                    [x, y, w, h, "category"]
                ]
            },
            ....
        ]
    """
    pdf_data = []
    paper_images = convert_from_path(pdf_filename)

    for idx, image in enumerate(paper_images):
        width, height = image.size

        layout = model.detect(image)

        block_data = [
            block.coordinates[:2]
            + (
                block.width,
                block.height,
                block.type,
            )
            for block in layout
        ]

        pdf_data.append(
            {
                "page": {"height": height, "width": width, "index": idx},
                "blocks": block_data,
            }
        )

    return pdf_data


if __name__ == "__main__":
    args = parser.parse_args()

    config_path = DEFAULT_MODEL_CONFIG
    if args.config_path:
        config_path = args.config_path

    model_path = DEFAULT_MODEL_WEIGHTS
    if args.model_path:
        model_path = args.model_path

    label_map = DEFAULT_MODEL_LABEL_MAP
    if args.label_map_path:
        with open(args.label_map_path) as in_file:
            label_map = json.load(in_file)

    model = lp.Detectron2LayoutModel(
        config_path=config_path,
        model_path=model_path,
        extra_config=[
            "MODEL.ROI_HEADS.SCORE_THRESH_TEST",
            0.55,
            "MODEL.ROI_HEADS.NMS_THRESH_TEST",
            0.4,
        ],
        label_map=label_map,
    )

    all_pdf_data = {}
    for pdf_filename in tqdm(
        sorted(glob(f"{args.annotation_folder}/**/*.pdf", recursive=True))
    ):
        pdf_data = run_prediction(pdf_filename)
        all_pdf_data[os.path.basename(pdf_filename)] = pdf_data

    with open(args.save_path, "w") as fp:
        json.dump(all_pdf_data, fp)
