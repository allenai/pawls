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


def print_results(calculation_method_msg, df: pd.DataFrame):
    cleaned_table = df[sorted(df.columns)].loc[sorted(df.columns)]
    print(calculation_method_msg)
    print("-" * 45)
    print(
        "The (i,j)-th element in the table is calculated by treating the annotations from\n"
        "i as the 'ground-truth's, and those from j are considered as 'predictions'."
    )
    print(
        tabulate(
            cleaned_table,
            headers="keys",
            tablefmt="psql",
        )
    )
    print("\n")
    return cleaned_table


class PythonLiteralOption(click.Option):
    """Used for parsing list-like stings from the input.

    A technique adapted from https://stackoverflow.com/a/47730333
    """

    def type_cast_value(self, ctx, value):
        try:
            return [ele.strip() for ele in value.split(",")]
        except:
            raise click.BadParameter(value)


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


class COCOEvaluator:

    COCO_METRICS = ["AP", "AP50", "AP75", "APs", "APm", "APl"]

    def __init__(self, coco_save_path: str, class_names: List[str] = None):

        all_cocos = {}
        annotators = []
        for userfile in sorted(glob(f"{coco_save_path}/*.json")):
            with HiddenPrints():
                username = userfile.split("/")[-1].replace(".json", "")
                annotators.append(username)
                all_cocos[username] = COCO(userfile)

        # A hack to make use of the current COCOEval API
        for coco in all_cocos.values():
            for ele in coco.dataset["annotations"]:
                ele["score"] = 1

        self.all_cocos = all_cocos
        self.annotators = annotators

        self.class_names = class_names or [
            val["name"] for _, val in all_cocos[annotators[0]].cats.items()
        ]

    def calculate_scores_for_two_cocos(
        self, coco1: COCO, coco2: COCO, class_names: List[str]
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
            for idx, metric in enumerate(self.COCO_METRICS)
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

    def calculate_ap_scores(self) -> Tuple[Dict, Dict]:

        coco_results = defaultdict(dict)
        coco_category_results = defaultdict(dict)

        for name1, coco1 in self.all_cocos.items():
            for name2, coco2 in self.all_cocos.items():

                image_ids = get_mutually_annotated_image_ids(coco1, coco2)
                coco1 = filter_annotation_with_image_ids(coco1, image_ids)
                coco2 = filter_annotation_with_image_ids(coco2, image_ids)

                results, results_per_category = self.calculate_scores_for_two_cocos(
                    coco1, coco2, self.class_names
                )
                coco_results[name1][name2] = results
                coco_category_results[name1][name2] = results_per_category

        return coco_results, coco_category_results

    def show_results(self, results: Dict, metric_names: List[str] = None):
        """Show COCO Eval results for the given metric names.

        Args:
            results (Dict):
                The coco_results dict generated by `COCOEvaluator.calculate_ap_scores`.

            metric_names (List[str], optional):
                Metric report of the specified `metric_names` will be displayed.
                If not set, all metrics in `COCOEvaluator.COCO_METRICS` will be displayed.
        """
        if metric_names is None:
            metric_names = self.COCO_METRICS

        cleaned_tables = {}

        for metric_name in metric_names:
            df = pd.DataFrame(results).applymap(
                lambda ele: ele.get(metric_name) if not pd.isna(ele) else ele
            )
            cleaned_table = print_results(
                f"Inter-annotator agreement based on {metric_name} scores.", df
            )
            cleaned_tables[metric_name] = cleaned_table

        return cleaned_tables

    def show_category_results(self, results: Dict, class_names: List[str] = None):
        """Show COCO Eval results for the given class_names.

        Args:
            results (Dict):
                The coco_category_results dict generated by `COCOEvaluator.calculate_ap_scores`.

            class_names (List[str], optional):
                Metric report of the specified `class_names` will be displayed.
                If not set, all classes in `self.class_names` will be displayed.
        """
        if class_names is None:
            class_names = self.class_names

        cleaned_tables = {}

        for class_name in class_names:
            df = pd.DataFrame(results).applymap(
                lambda ele: ele.get(class_name) if not pd.isna(ele) else ele
            )

            cleaned_table = print_results(
                f"Inter-annotator agreement of the {class_name} class based on AP scores.",
                df,
            )
            cleaned_tables[class_name] = cleaned_table

        return cleaned_table


class TokenEvaluator:

    PDF_FEATURES_IN_SAVED_TABLES = ["pdf", "page_index", "index", "text"]

    def __init__(self, token_save_path: str):

        self.df = pd.read_csv(token_save_path)
        self.annotators = list(
            self.df.columns[len(self.PDF_FEATURES_IN_SAVED_TABLES) :]
        )
        # Assuming all users are stored in email address

    def calculate_scores_for_two_annotators(
        self, annotator_gt: str, annotator_pred: str
    ):

        cur_df = self.df[[annotator_gt, annotator_pred]].fillna(-1)
        acc = (cur_df[annotator_gt] == cur_df[annotator_pred]).mean()

        return acc

    def calculate_token_accuracy(self):
        table = defaultdict(dict)

        for i, annotator_gt in enumerate(self.annotators):
            for j, annotator_pred in enumerate(self.annotators):

                if j <= i:  # Skip the diagonal
                    continue

                # The token_acc table is symmetric
                table[annotator_pred][annotator_gt] = table[annotator_gt][
                    annotator_pred
                ] = self.calculate_scores_for_two_annotators(
                    annotator_gt, annotator_pred
                )

        return table

    @staticmethod
    def show_results(results: Dict):

        df = pd.DataFrame(results)

        calculation_method_msg = (
            "The token accuracy is calculated by simply comparing"
            "the compatibility of tokens labels agasin two annotators."
        )

        cleaned_table = print_results(calculation_method_msg, df)

        return cleaned_table


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.argument("config", type=str)
@click.option(
    "--annotator",
    "-u",
    multiple=True,
    help="Export annotations of the specified annotator.",
)
@click.option(
    "--textual-categories",
    cls=PythonLiteralOption,
    help="The annotations of textual categories will be evaluated based on token accuracy.",
)
@click.option(
    "--non-textual-categories",
    cls=PythonLiteralOption,
    help="The annotations of non-textual categories will be evaluated based on AP scores based on box overlapping.",
)
@click.option(
    "--include-unfinished",
    "-i",
    is_flag=True,
    help="A flag to export all annotation by the specified annotator including unfinished ones.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="A flag to show detailed reports.",
)
@click.option(
    "--save",
    type=click.Path(),
    help="If set, PAWLS will save the reports in the given folder.",
)
@click.pass_context
def metric(
    ctx,
    path: click.Path,
    config: str,
    annotator: List,
    textual_categories: List,
    non_textual_categories: List,
    include_unfinished: bool = False,
    verbose: bool = False,
    save: click.Path = None,
):
    """Calculate the inter-annotator agreement for the annotation project for both textual-categories

    Usage:

    Run evaluation for textual-categories cat1 and cat2, and for non-textual-categories cat3 and cat4:

        pawls metric <labeling_folder> <labeling_config> --textual-categories cat1,cat2 --non-textual-categories cat3,cat4


    Specifying annotators for evaluation, and include any unfinished annotations:

        pawls metric <labeling_folder> <labeling_config> -u annotator1 -u annotator2 --textual-categories cat1,cat2 --non-textual-categories cat3,cat4 --include-unfinished

    Generating detailed reports:

        pawls metric <labeling_folder> <labeling_config> --textual-categories cat1,cat2 --non-textual-categories cat3,cat4 --verbose

    """

    if save is not None:
        save = str(save)
        if not os.path.exists(save):
            os.makedirs(save)

    invoke_export = lambda tempdir, format, categories: ctx.invoke(
        export,
        path=path,
        config=config,
        output=tempdir,
        format=format,
        annotator=annotator,
        categories=categories,
        include_unfinished=include_unfinished,
        export_images=False,
    )

    if len(non_textual_categories) > 0:
        print(
            f"Generating Accuracy report for non-textual categories {non_textual_categories}"
        )

        with tempfile.TemporaryDirectory() as tempdir:

            invoke_export(
                tempdir=tempdir, format="coco", categories=non_textual_categories
            )

            coco_eval = COCOEvaluator(tempdir)
            coco_results, coco_category_results = coco_eval.calculate_ap_scores()

            if verbose:
                save_table = coco_eval.show_results(coco_results)
                coco_eval.show_category_results(coco_category_results)
            else:
                save_table = coco_eval.show_results(coco_results, ["AP"])

            if save is not None:
                save_table["AP"].to_csv(f"{save}/block-eval.csv")

    if len(textual_categories) > 0:
        print(f"Generating Accuracy report for textual categories {textual_categories}")

        with tempfile.TemporaryDirectory() as tempdir:

            tempdir = os.path.join(tempdir, "annotation.csv")

            invoke_export(
                tempdir=tempdir, format="token", categories=textual_categories
            )

            token_eval = TokenEvaluator(tempdir)
            token_results = token_eval.calculate_token_accuracy()

            save_table = token_eval.show_results(token_results)

            if save is not None:
                save_table.to_csv(f"{save}/textual-eval.csv")