import os 
import json
from glob import glob

from tqdm import tqdm
import layoutparser as lp
from pdf2image import convert_from_path

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--annotation_folder', type=str)
parser.add_argument('--save_path', type=str)



def run_prediction(pdf_filename):

    pdf_data = []
    paper_images = convert_from_path(pdf_filename)

    for idx, image in enumerate(paper_images):
        width, height = image.size
        
        layout = model.detect(image)
        
        block_data = [block.coordinates[:2] + (block.width, block.height, block.type,) for block in layout]
        
        pdf_data.append({
            "page": {"height": height, "width": width, "index": idx},
            "blocks": block_data
        })

    return pdf_data

if __name__ == "__main__":
    args = parser.parse_args()

    model = lp.Detectron2LayoutModel(
        "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
        extra_config=[
            "MODEL.ROI_HEADS.SCORE_THRESH_TEST",
            0.55,
            "MODEL.ROI_HEADS.NMS_THRESH_TEST",
            0.4,
        ],
        label_map={0: "Paragraph", 1: "Title", 2: "ListItem", 3: "Table", 4: "Figure"},
    )

    all_pdf_data = {}
    for pdf_filename in tqdm(sorted(glob(f"{args.annotation_folder}/*/*.pdf"))):
        pdf_data = run_prediction(pdf_filename)
        all_pdf_data[os.path.basename(pdf_filename)] = pdf_data
    

    with open(args.save_path, 'w') as fp:
        json.dump(all_pdf_data, fp)