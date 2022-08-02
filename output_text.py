import json
import shutil
from dataclasses import dataclass
from typing import Dict, List, OrderedDict

import pdfplumber as pp

EMAIL = "alyssa.j.page@gmail.com"


def struct_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/pdf_structure.json"


def annots_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/{EMAIL}_annotations.json"


def pdf_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/{sha}.pdf"


def status_fn() -> str:
    return f"annotations_alyssa/sections-annotation/status/{EMAIL}.json"


with open(status_fn(), encoding="utf-8") as f:
    status = json.loads(f.read())

completed_items = []
skip_shas = set([])

for sha, item in status.items():
    if item["finished"] and sha not in skip_shas:
        completed_items.append(sha)


@dataclass
class Box:
    x: float
    y: float
    width: float
    height: float


@dataclass
class Relation:
    target_ids: List[str]


@dataclass
class Token:
    text: str
    box: Box


@dataclass
class Annotation:
    id: str
    page: int
    label: str
    tokens: List[Token]


completed_items = ["376c3d068c61292bd4f74e4499104ff8856d8d56"]

for sha in completed_items:
    with open(struct_fn(sha), encoding="utf-8") as f:
        structure = json.loads(f.read())

    page_to_tokens: Dict[int, List[str]] = {}

    for s in structure:
        page, tokens = s["page"], s["tokens"]
        page_to_tokens[page["index"]] = [
            Token(text=t["text"], box=Box(t["x"], t["y"], t["width"], t["height"]))
            for t in tokens
        ]

    with open(annots_fn(sha), encoding="utf-8") as f:
        annots = json.loads(f.read())

    id_to_annot: Dict[str, Annotation] = OrderedDict()

    for annot in annots["annotations"]:

        # Custom bounding box (manual annotation)
        if not annot["tokens"]:
            with pp.open(pdf_fn(sha)) as pdf:
                target_page = pdf.pages[annot["page"]]
                target_box = (
                    annot["bounds"]["left"],
                    annot["bounds"]["top"],
                    annot["bounds"]["right"],
                    annot["bounds"]["bottom"],
                )
                target_words = target_page.crop(target_box).extract_words(x_tolerance=2)

                annot_tokens = [
                    Token(
                        text=t["text"],
                        box=Box(
                            t["x0"], t["top"], t["x1"] - t["x0"], t["bottom"] - t["top"]
                        ),
                    )
                    for t in target_words
                ]

        else:
            annot_tokens = [
                page_to_tokens[t["pageIndex"]][t["tokenIndex"]] for t in annot["tokens"]
            ]

        id_to_annot[annot["id"]] = Annotation(
            id=annot["id"],
            page=annot["page"],
            label=annot["label"]["text"],
            tokens=annot_tokens,
        )

    relations: Dict[str, List[str]] = {}

    for relation in annots["relations"]:
        for target_id in relation["targetIds"]:
            relations[target_id] = relation["targetIds"]

    # Skip these items b/c we already consumed them in a relationship
    consumed_for_relations = set()

    curr_id: int = 0

    # Move PDF for easy zipping later
    shutil.copy(pdf_fn(sha), f"./annotations_alyssa/pdfs/{sha}.pdf")

    with open(f"./annotations_alyssa/txts/{sha}.txt", "w", encoding="utf-8") as f:

        for _id, annot in id_to_annot.items():
            if _id in consumed_for_relations:
                continue

            if _id in relations:
                tokens = []

                for target_id in relations[_id]:
                    consumed_for_relations.add(target_id)
                    tokens.extend(id_to_annot[target_id].tokens)

            else:
                tokens = annot.tokens

            f.write(str(curr_id))
            f.write(" ")
            f.write(" ".join(map(lambda t: t.text, tokens)))
            f.write("\n")

            curr_id += 1
