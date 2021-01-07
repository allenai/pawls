import os
import sys
import tempfile
from glob import glob
from copy import deepcopy
from collections import defaultdict
from typing import List, NamedTuple, Union, Dict, Any, Set, Tuple

import click
import pandas as pd
import numpy as np
from tabulate import tabulate
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

from pawls.commands.export import export

METRICS = ["AP", "AP50", "AP75", "APs", "APm", "APl"]


class HiddenPrints:
    """Used for hiding unnecessary prints of COCO Eval
    A trick learned from https://stackoverflow.com/a/45669280
    """

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def get_unique_image_ids(coco: COCO) -> Set[int]:
    return set([anno["image_id"] for anno in coco.dataset["annotations"]])


def get_mutually_annotated_image_ids(coco1: COCO, coco2: COCO) -> Set[int]:
    return get_unique_image_ids(coco1).intersection(get_unique_image_ids(coco2))


def filter_annotation_with_image_ids(coco: COCO, image_ids: Set[int]) -> COCO:
    coco = deepcopy(coco)
    coco.dataset["annotations"] = [
        anno for anno in coco.dataset["annotations"] if anno["image_id"] in image_ids
    ]
    coco.dataset["images"] = [
        image for image in coco.dataset["images"] if image["id"] in image_ids
    ]
    return coco


def calculate_scores_for_two_cocos(
    coco1: COCO, coco2: COCO, class_names: List[str]
) -> Tuple[Dict, Dict]:

    coco_eval = COCOeval(coco1, coco2, iouType="bbox")
    with HiddenPrints():
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()

    results = {
        metric: float(
            coco_eval.stats[idx] * 100 if coco_eval.stats[idx] >= 0 else "nan"
        )
        for idx, metric in enumerate(METRICS)
    }
    precisions = coco_eval.eval["precision"]

    results_per_category = []
    for idx, name in enumerate(class_names):
        # area range index 0: all area ranges
        # max dets index -1: typically 100 per image
        precision = precisions[:, :, idx, 0, -1]
        precision = precision[precision > -1]
        ap = np.mean(precision) if precision.size else float("nan")
        results_per_category.append(("{}".format(name), float(ap * 100)))

    results_per_category = {name: ap for name, ap in results_per_category}
    return results, results_per_category


def show_results(results:Dict, metric_names:List[str]=METRICS):
    for metric_name in metric_names:
        df = pd.DataFrame(results).applymap(
            lambda ele: ele.get(metric_name) if not pd.isna(ele) else ele
        )
        print(f"Inter-annotator agreement based on {metric_name} scores.")
        print("-" * 45)
        print(
            "The (i,j)-th element in the table is calculated by treating the annotations from\n"
            "i as the 'ground-truth's, and those from j are considered as 'predictions'."
        )
        print(
            tabulate(
                df[sorted(df.columns)].loc[sorted(df.columns)],
                headers="keys",
                tablefmt="psql",
            )
        )

def show_category_results(results:Dict, class_names:List[str]):
    for class_name in class_names:
        df = pd.DataFrame(results).applymap(
            lambda ele: ele.get(class_name) if not pd.isna(ele) else ele
        )
        print(f"Inter-annotator agreement of the {class_name} class based on AP scores.")
        print("-" * 45)
        print(
            "The (i,j)-th element in the table is calculated by treating the annotations from\n"
            "i as the 'ground-truth's, and those from j are considered as 'predictions'."
        )
        print(
            tabulate(
                df[sorted(df.columns)].loc[sorted(df.columns)],
                headers="keys",
                tablefmt="psql",
            )
        )


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=click.File("r"))
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
@click.option(
    "--show-detailed",
    is_flag=True,
    help="A flag to show detailed reports",
)
@click.pass_context
def metric(
    ctx,
    path: click.Path,
    config: click.File,
    annotator: List,
    include_unfinished: bool = False,
    show_detailed: bool = False,
):
    """Calculate the inter-annotator agreement for the annotation project

    To get a simple report for annotator A and B, use:

        `pawls metric <labeling_folder> <labeling_config> -u <annotator-A> -u <annotator-B>`

    To get a detailed report for all annotators, use:

        `pawls metric <labeling_folder> <labeling_config> -u <annotator_name> --show-detailed`
    """

    with tempfile.TemporaryDirectory() as tempdir:
        
        ctx.invoke(
            export,
            path=path,
            config=config,
            output=tempdir,
            annotator=annotator,
            include_unfinished=include_unfinished,
            not_export_images=True,
        )

        all_cocos = {}
        for username in sorted(glob(f"{tempdir}/*.json")):
            with HiddenPrints():
                all_cocos[username.split("/")[-1][:-5]] = COCO(username)

        for coco in all_cocos.values():
            for ele in coco.dataset['annotations']:
                ele['score'] = 1

        coco_results = defaultdict(dict)
        coco_results_per_category = defaultdict(dict)
        class_names = [
            val["name"] for _, val in all_cocos["development_user"].cats.items()
        ]

        print("\n")
        for name1, coco1 in all_cocos.items():
            for name2, coco2 in all_cocos.items():

                image_ids = get_mutually_annotated_image_ids(coco1, coco2)
                coco1 = filter_annotation_with_image_ids(coco1, image_ids)
                coco2 = filter_annotation_with_image_ids(coco2, image_ids)

                results, results_per_category = calculate_scores_for_two_cocos(
                    coco1, coco2, class_names
                )
                coco_results[name1][name2] = results
                coco_results_per_category[name1][name2] = results_per_category

        if not show_detailed:
            show_results(coco_results, ["AP"])
        else:
            show_results(coco_results, METRICS)
            show_category_results(coco_results_per_category, class_names)
