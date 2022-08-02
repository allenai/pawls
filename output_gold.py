import json
import logging
import os
from dataclasses import asdict, dataclass
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


def nesting_fn(sha: str) -> str:
    return f"annotations_alyssa/completed_nesting/{sha}.txt"


with open(status_fn(), encoding="utf-8") as f:
    status = json.loads(f.read())

SHAS = {sha for sha, item in status.items() if item["finished"]}


logger = logging.getLogger("output_gold")
logger.setLevel(logging.DEBUG)
_console_log = logging.StreamHandler()
_console_log.setLevel(logging.DEBUG)
_console_fmt = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s - %(message)s")
_console_log.setFormatter(_console_fmt)
logger.addHandler(_console_log)


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


@dataclass
class ConsolidatedAnnotation:
    """Generated after joining across annotation relations"""

    id: int
    underlying_ids: List[str]
    page: int
    text: str
    tokens: List[Token]


@dataclass
class Nesting:
    id: int
    level: int
    text: str


@dataclass
class NestingRelation:
    parent: Nesting
    child: Nesting


# Check each label overlaps with something in the txt file
# If ID is found then compare text
# If ID is not found then emit warning


def parse_nesting(n: str) -> Nesting:
    parts = n.strip().split(" ")

    try:
        if parts[0].startswith("-"):
            level = len(parts[0])
            _id = int(parts[1])
            text = " ".join(parts[2:])
        else:
            level = 0
            _id = int(parts[0])
            text = " ".join(parts[1:])

        return Nesting(id=_id, level=level, text=text)
    except Exception as ex:
        logger.warning("Nesting parse exception: %s on line '%s'", ex, n)
        raise ex


def debug_page(sha: str, section: ConsolidatedAnnotation):
    boxes = [
        (t.box.x, t.box.y, t.box.x + t.box.width, t.box.y + t.box.height)
        for t in section.tokens
    ]

    with pp.open(pdf_fn(sha)) as pdf:
        im = pdf.pages[section.page].to_image()
        im.draw_rects(boxes)

        fn = f"debug/{sha}-page-{section.page}-{section.id}.png"
        logger.debug(f"Output {fn}")
        im.save(fn)


for sha in SHAS:
    if not os.path.exists(nesting_fn(sha)):
        logger.info("Skipping %s (nesting not found)!", sha)
        continue

    logger.debug("Processing %s", sha)

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
            logger.warning("Manual review required for %s\n%s", sha, annot)

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
    # shutil.copy(pdf_fn(sha), f"./annotations_alyssa/pdfs/{sha}.pdf")

    # with open(f"./annotations_alyssa/txts/{sha}.txt", "w", encoding="utf-8") as f:
    sections_by_id: Dict[str, ConsolidatedAnnotation] = {}

    for _id, annot in id_to_annot.items():
        if _id in consumed_for_relations:
            continue

        underlying_ids = [_id]

        if _id in relations:
            tokens = []

            for target_id in relations[_id]:
                consumed_for_relations.add(target_id)
                underlying_ids.append(_id)

                tokens.extend(id_to_annot[target_id].tokens)

        else:
            tokens = annot.tokens

        sections_by_id[curr_id] = ConsolidatedAnnotation(
            id=curr_id,
            page=annot.page,
            underlying_ids=underlying_ids,
            text=" ".join(map(lambda t: t.text, tokens)),
            tokens=tokens,
        )

        curr_id += 1

    # 2) Load the indentations with their parents
    with open(nesting_fn(sha), encoding="utf-8") as f:
        nestings = [parse_nesting(l) for l in f if len(l.strip()) > 0]

    # 3) Validate nestings vs expected
    nestings_by_id: Dict[int, Nesting] = {n.id: n for n in nestings}
    skip_ids = set()

    for _id, section in sections_by_id.items():
        nesting = nestings_by_id.get(_id)

        if nesting is None:
            debug_page(sha, section)
            logger.warning("No nesting match for %s: {%s}", sha, section)
            # Remove from sections so we don't output it later
            skip_ids.add(_id)
            continue

        if nesting.text != section.text:
            import pdb

            pdb.set_trace()
            raise ValueError(
                f"Nesting '{nesting.text}' does not match section '{section.text}'!"
            )

    logger.info("Found %i nestings for %s", len(nestings), sha)

    stack = []
    pairs = []

    # 4) Build the parent-child relations
    if len(nestings) > 0:
        prev = nestings[0]
        if prev.level != 0:
            raise f"Invalid starting level for PDF: {sha}!"

        for nesting in nestings[1:]:
            if nesting.level > prev.level:
                stack.append(prev)

            elif len(stack) > 0 and nesting.level == stack[-1].level:
                stack.pop()

            if nesting.level > 0:
                result = NestingRelation(parent=stack[-1], child=nesting)
                pairs.append(result)

            prev = nesting

    blob = {
        "structure": structure,
        "sections": {
            k: asdict(v) for k, v in sections_by_id.items() if k not in skip_ids
        },
        "relations": [asdict(n) for n in pairs],
    }

    with open(
        f"./annotations_alyssa/completed_gold/{sha}.json", "w", encoding="utf-8"
    ) as f:
        f.write(json.dumps(blob, indent=2))
