import os
from glob import glob
import click
from typing import Tuple

import pandas as pd
from tabulate import tabulate

from pawls.commands.utils import load_json, get_pdf_pages_and_sizes


def get_labeling_status(target_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame]:

    all_json_records = glob(f"{target_dir}/status/*.json")

    all_record = []
    for record in all_json_records:
        name = os.path.splitext(os.path.basename(record))[0]
        all_annotations = load_json(record)
        cur_record = pd.DataFrame(all_annotations).T
        cur_record['annotator'] = name
        all_record.append(cur_record)

    all_record = pd.concat(all_record)
    pdf_pages = {sha: get_pdf_pages_and_sizes(
        f"{target_dir}/{sha}/{sha}.pdf")[0] for sha in set(all_record.index)}
    all_record = all_record.reset_index()
    all_record['page_num'] = all_record['index'].map(pdf_pages)

    all_record['junk_or_finished'] = all_record['finished'] | all_record['junk']
    # used for calculating the unfinished tasks

    all_record['valid_page_num'] = all_record.apply(
        lambda row: row['page_num'] if row['finished'] else 0, axis=1)
    all_record['valid_annotations'] = all_record.apply(
        lambda row: row['annotations'] if row['finished'] else 0, axis=1)

    status = (all_record
              .groupby('annotator')
              .agg(
                  {"index":             ["count"],
                   "finished":          ["sum"],
                   "valid_annotations": ["sum", "max", "min"],
                   "junk":              ["sum"],
                   "junk_or_finished":  ["sum"],
                   "valid_page_num":    ["sum"],
                   })
              )

    status.columns = status.columns.map('_'.join)
    status = status.rename(columns={"index_count": "total_tasks",
                                    "finished_sum": "total_finished",
                                    "junk_sum": "total_junks",
                                    "junk_or_finished_sum": "junk_or_finished",
                                    "valid_page_num_sum": "page_num",
                                    "valid_annotations_sum": "anno_sum",
                                    "valid_annotations_max": "anno_max"})

    status['total_unfinished'] = \
        status['total_tasks'] - status['junk_or_finished']

    status["avg_anno_per_page"] = \
        status["anno_sum"] / status["page_num"]
    display_status = status[["total_tasks", "total_finished", "avg_anno_per_page",
                             "page_num", "anno_sum", "anno_max"]].copy()

    display_status.loc["AGGREGATION", :] = display_status.sum()
    display_status.loc["AGGREGATION", "avg_anno_per_page"] = \
        (display_status.loc["AGGREGATION", "anno_sum"] /
         display_status.loc["AGGREGATION", "page_num"])

    return display_status.fillna(0.), all_record.rename(columns={"index": "sha"})


@click.command(context_settings={"help_option_names": ["--help", "-h"]})
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--output",
    help="Path to save the export data",
    type=click.Path()
)
def status(
    path: click.Path,
    output: click.Path,
):
    """
    Checking the labeling status for some annotation project

    To check the labeling status for some PAWLS annotation folder, use:
        `pawls status <labeling_folder>`

    To save the labeling record table for some PAWLS annotation folder, use:
        `pawls status <labeling_folder> --output record.csv`
    """

    labeling_status, all_record = get_labeling_status(path)
    print(tabulate(labeling_status, headers='keys', tablefmt='psql'))

    if output is not None:
        all_record.to_csv(output, index=None)
        print(f"Saved the annotation record table to {output}")
