import json
import shutil
from dataclasses import dataclass
from typing import Dict, List, OrderedDict

import pdfplumber as pp

# 65b57ad4b975975b6d87fd4d147817ca1da2fc9e
# 9b9f2d31890a33d57eaad959bcc5f51b463df162

EMAIL = "alyssa.j.page@gmail.com"


def struct_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/pdf_structure.json"


def annots_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/alyssa.j.page@gmail.com_annotations.json"


def pdf_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/{sha}.pdf"


with open(
    "annotations_alyssa/sections-annotation/status/alyssa.j.page@gmail.com.json",
    encoding="utf-8",
) as f:
    status = json.loads(f.read())

completed_items = []
skip_shas = set(
    [
        "65b57ad4b975975b6d87fd4d147817ca1da2fc9e",
        "9b9f2d31890a33d57eaad959bcc5f51b463df162",
        "001534ec4e6d656722fddc81ba532779cea76875",
        "04a178c02ea7a0ee41550bcf750ab9690b799698",
        "050035080b5d6a2b11b127d0b9868c1d35a872d9",
        "09624d32cc4492dbd68706df020137ddf47d4554",
        "09c1bf59a0521a1533daa25fc38cebbc11541fbe",
        "0ae6f69b8ea34117ba7083c293405ddaba5b8f2b",
        "0b3c4723c5e5b34c1f512721900e542cb654d83a",
        "0c2093a26725d423654baa4f009e6c919cb8ca1e",
        "0c69b1e916476bbdd8b1b38bbb1aa877709a0f28",
        "0c974b236c8c2a3ed2c881866b546f14f3749005",
        "0cb52d6f316ab715e4d5898812153d1a81415463",
        "0cd1148b4a875a0ee6c0a4999a7e8f07e66ecbfe",
        "0ef3cc828e4ab9589107c5d0f1f20c31b4fb3b23",
        "0fbfea6bf315e9609bd2baf28c145b6390f8de1c",
        "105d22748b95384edd4fc0bcd07ee481d1611098",
        "10c8efb5a0cec40740e71ce20927950bc7f12807",
        "13b879be58bc89fd3abf945c83b18844022decc5",
        "158d4215081464510a5681a4442c087284e746ce",
        "1910ae59b83730acd2c82b2a0c52a8fe5563ce1a",
        "1959008518878ddb875062fa5a7079790a830a98",
        "1d6c94d1e742003cc7deb3fa6e12392225472dfa",
        "204a768859ad2f8ed85a9913cbb3c8e89f32285a",
        "20fdafb68d0e69d193527a9a1cbe64e7e69a3798",
        "21f95b703430a802b80c36ecd34dc30e73df59c4",
        "249623fe957042eebff9e95c16d0e33ff25037e3",
        "249d9a37789b0163e004973f1ed9b4daaea0e26a",
        "24be27b62e0355cf15182913cf3f1e4e0e17d4df",
        "264388650dec372765e74ac7f93c58ad056a6ba7",
        "268f9017be73961f9aa4f364e90af609f0dac4ca",
        "26ed89bff49545f8c6ddfd05ba9a9c59c926d322",
        "26edeff1028a4f11adc21ee2501a624219b1c969",
        "28d439b0f1fa2394a9a50cd251cf575a1a569391",
        "2ab6cd06b36cd42ddfa4f98427d8011f19eb8a1d",
        "2c33f2aed89a7b04c2509b897e5fcccccdb2b7b6",
        "2d76d1a18bec9f887e400905781041c311087a3e",
        "2dff68593de2607b05aa57f91861014bc71ae228",
        "2e4281cf4d1565971450f7a96c87e961a7ca648b",
        "2e6b8bcbc0d3434a4edc233466b5b3fa42e6d5aa",
        "2fb4de3d12a46dadbbd10d0d6410d645d14444c2",
        "304e2a42e897aa728d394e2d1e60ea26f4f1c101",
        "311a185718716b56d9a3dff3bd4a96d2bab1a19a",
        "335ab0ef648562cf9c35ffb25b0169fd14327502",
        "33c8f4ed9c1f247b97506f964ae06d49f9b2b7d2",
        # "348a852a6cd58d1500aa81789b4fc1e8452a087e", Re-doing this one
        "36909e01d9f51870068521562e107289aeb5bd34",
        "36ac62e68d60d79e572d635e86725ee92bb5f43a",
        "376c3d068c61292bd4f74e4499104ff8856d8d56",
        "38223d930125c139670402c99bb10ab2ae0ab94f",
    ]
)

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

    # Move PDF for eazy zipping later
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
