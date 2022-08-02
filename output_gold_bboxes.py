import json
import logging
import shutil
from dataclasses import asdict, dataclass
from typing import Dict, List, OrderedDict

EMAIL = "alyssa.j.page@gmail.com"
BASEDIR = "./annotations_alyssa/sections-annotation"


def struct_fn(sha: str) -> str:
    return f"{BASEDIR}/{sha}/pdf_structure.json"


def annots_fn(sha: str) -> str:
    return f"{BASEDIR}/{sha}/{EMAIL}_annotations.json"


def pdf_fn(sha: str) -> str:
    return f"{BASEDIR}/{sha}/{sha}.pdf"


def status_fn() -> str:
    return f"{BASEDIR}/status/{EMAIL}.json"


def gold_fn(sha: str) -> str:
    return f"./annotations_alyssa/gold/{sha}_annotated_boxes.json"


SHAS = set()

with open(status_fn(), encoding="utf-8") as f:
    for sha, item in json.loads(f.read()).items():
        if item["finished"]:
            SHAS.add(sha)


@dataclass
class Box:
    left: float
    top: float
    right: float
    bottom: float


@dataclass
class Relation:
    target_ids: List[str]


@dataclass
class Token:
    text: str
    box: Box


@dataclass
class Char:
    text: str
    box: Box


@dataclass
class Annotation:
    id: str
    page: int
    label: str
    tokens: List[Token]


for sha in SHAS:
    with open(struct_fn(sha), encoding="utf-8") as f:
        structure = json.loads(f.read())

    page_to_tokens: Dict[int, List[Token]] = {}

    for s in structure:
        page, tokens = s["page"], s["tokens"]
        page_to_tokens[page["index"]] = [
            Token(
                text=t["text"],
                box=Box(
                    left=t["x"],
                    top=t["y"],
                    right=t["x"] + t["width"],
                    bottom=t["y"] + t["height"],
                ),
            )
            for t in tokens
        ]

    with open(annots_fn(sha), encoding="utf-8") as f:
        annots = json.loads(f.read())

    id_to_annot: Dict[str, Annotation] = OrderedDict()

    for annot in annots["annotations"]:

        # FIXME: Custom bounding box (manual annotation)
        if not annot["tokens"]:
            logging.warning("Found manual annotation box on %s!\n%s", sha, annot)

        else:
            # Pull tokens directly from the PDF structure
            annot_tokens = [
                page_to_tokens[t["pageIndex"]][t["tokenIndex"]] for t in annot["tokens"]
            ]

            # Attempt to get chars from the underlying PDF with annotation box
            # Matches are not exact so not providing character-level for gold set
            # annot_chars = []

            # page = pdf.pages[annot["page"]]
            # crop = page.within_bbox(
            #    (
            #        annot["bounds"]["left"],
            #        annot["bounds"]["top"],
            #        annot["bounds"]["right"],
            #        annot["bounds"]["bottom"],
            #    )
            # )

            # assert_tokens = "".join(t.text for t in annot_tokens)

            # for idx, c in enumerate(crop.chars):
            #    # Drop extra characters at end of bounding box
            #    if idx == len(assert_tokens):
            #        break

            #    # Skip all space chars
            #    if len(c["text"].strip()) == 0:
            #        continue

            #    annot_chars.append(
            #        Char(
            #            text=c["text"],
            #            box=Box(
            #                left=c["x0"],
            #                top=c["top"],
            #                right=c["x1"],
            #                bottom=c["bottom"],
            #            ),
            #        )
            #    )

            # assert_chars = "".join(c.text for c in annot_chars)

            # if assert_tokens != assert_chars:
            #    logging.warning(
            #        "Expected tokens '%s' to equal '%s'",
            #        assert_tokens,
            #        assert_chars,
            #    )

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

    # Move PDF for upload alongside annotations
    shutil.copy(pdf_fn(sha), f"./annotations_alyssa/gold/{sha}.pdf")

    # Skip these items b/c we already consumed them in a relationship
    consumed_for_relations = set()
    result = []

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

        result.append(
            {
                "page": annot.page,
                "tokens": [asdict(t) for t in annot.tokens],
            }
        )

    with open(gold_fn(sha), "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2))
