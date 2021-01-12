import json
from typing import List
import requests

from pawls.preprocessors.model import Page


def fetch_grobid_structure(pdf_file: str, grobid_host: str = "http://localhost:8070"):
    files = {
        "input": (pdf_file, open(pdf_file, "rb"), "application/pdf", {"Expires": "0"})
    }
    url = "{}/api/processPdfStructure".format(grobid_host)
    resp = requests.post(url, files=files)
    if resp.status_code == 200:
        return json.loads(resp.text)
    else:
        raise Exception("Grobid returned status code {}".format(resp.status_code))


def parse_annotations(grobid_structure) -> List[Page]:
    pages = []
    for grobid_page in grobid_structure["tokens"]["pages"]:
        tokens = []
        for token in grobid_page["tokens"]:
            tokens.append(
                dict(
                    text=token["text"],
                    x=token["x"],
                    y=token["y"],
                    width=token["width"],
                    height=token["height"],
                )
            )
        page = dict(
            page=dict(
                width=grobid_page["page"]["width"],
                height=grobid_page["page"]["height"],
                index=grobid_page["page"]["pageNumber"] - 1,
            ),
            tokens=tokens,
        )
        pages.append(page)

    return pages

def process_grobid(
    pdf_file: str,
    grobid_host: str = "http://localhost:8070"
):
    """
    Integration for importing annotations from grobid.
    Depends on a grobid API built from our fork https://github.com/allenai/grobid.
    Fetches a PDF by sha, sends it to the Grobid API and returns them.

    pdf_file: str
        The path to the pdf file to process.
    grobid_host: str (optional, default="http://localhost:8070")
        The forked grobid API which we use to produce the annotations.
    """
    grobid_structure = fetch_grobid_structure(pdf_file, grobid_host)
    annotations = parse_annotations(grobid_structure)

    return annotations
