import json
import requests

from pdfstructure.client.v1 import models
from pdfstructure.client.v1.api.default_api import DefaultApi
from pdfstructure.client.v1.configuration import Configuration
from pdfstructure.client.v1.api_client import ApiClient
from pdfstructure.client.v1.exceptions import ApiException


def fetch_grobid_structure(
    pdf_file: str, grobid_host: str = "http://localhost:8070"
) -> models.PdfAnnotations:
    files = {
        "input": (pdf_file, open(pdf_file, "rb"), "application/pdf", {"Expires": "0"})
    }
    url = "{}/api/processPdfStructure".format(grobid_host)
    resp = requests.post(url, files=files)
    if resp.status_code == 200:
        return json.loads(resp.text)
    else:
        raise Exception("Grobid returned status code {}".format(resp.status_code))


def parse_annotations(grobid_structure, source="grobid_test") -> models.PdfAnnotations:
    pages = []
    for grobid_page in grobid_structure["tokens"]["pages"]:
        tokens = []
        for token in grobid_page["tokens"]:
            tokens.append(
                models.PageToken(
                    text=token["text"],
                    x=token["x"],
                    y=token["y"],
                    width=token["width"],
                    height=token["height"],
                    style_name=token["styleName"],
                )
            )
        page = models.PageTokens(
            page=models.PdfPage(
                width=grobid_page["page"]["width"],
                height=grobid_page["page"]["height"],
                index=grobid_page["page"]["pageNumber"] - 1,
            ),
            tokens=tokens,
        )
        pages.append(page)

    styles = {}
    for style_name, grobid_style in grobid_structure["tokens"]["styles"].items():
        font_style = None
        if grobid_style.get("superscript", False):
            font_style = "superscript"
        elif grobid_style.get("subscript", False):
            font_style = "subscript"
        font_name = grobid_style["fontName"]
        i = font_name.find("+")
        if i >= 0:
            font_name = font_name[i + 1 :]
        i = font_name.find("-")
        if i >= 0:
            font_name = font_name[:i]
        color_hex_string = grobid_style.get("fontColor")
        color = int(color_hex_string.replace("#", ""), 16)
        style = models.TokenStyle(
            size=grobid_style["fontSize"],
            font_style=font_style,
            color=color,
            family=font_name,
        )
        styles[style_name] = style

    token_data = models.PdfTokens(pages=pages, styles=styles)

    # Given the index of a token in the document overall
    # Return the page index plus the offset within that page
    def offset_of_token(token_index):
        for i, p in enumerate(pages):
            if token_index <= len(p.tokens):
                return models.Offset(page=i, token=token_index)
            else:
                token_index -= len(p.tokens)

    def text_of_span(left, right):
        text = []
        for p in pages:
            token_count = len(p.tokens)
            if left >= 0 and left < token_count:
                text += [t.text for t in p.tokens[left : min(right, token_count)]]
            elif right >= 0 and right < token_count:
                text += [t.text for t in p.tokens[max(left, 0) : right]]
            left -= token_count
            right -= token_count
            if left < 0 and right < 0:
                break
        return text

    token_sources = models.TokenSources(sources={source: token_data})

    element_types = models.TextElementTypes(token_source=source, types={})
    for element_type, grobid_elements in grobid_structure["elements"][
        "elementTypes"
    ].items():
        if element_type == "<symbol>":
            continue
        element_type = element_type.replace("<", "").replace(">", "")
        elements = []
        for grobid_el in grobid_elements:
            tags = [models.Tag(name=k, value=v) for k, v in grobid_el["tags"].items()]
            if not grobid_el["spans"]:
                continue
            first_span = grobid_el["spans"][0]

            has_dehyphenized_text = (
                len([s for s in grobid_el["spans"] if s.get("dehyphenizedText")]) > 0
            )
            if has_dehyphenized_text:
                text = []
                for s in grobid_el["spans"]:
                    if s.get("dehyphenizedText"):
                        text += s["dehyphenizedText"]
                    else:
                        text += text_of_span(s["left"], s["right"])

                el = models.TextElement(
                    start=offset_of_token(first_span["left"]), text=text, tags=tags
                )
            else:
                spans = []

                def append_span(span):
                    if span.start != span.end:
                        spans.append(span)

                for s in grobid_el["spans"]:
                    start = offset_of_token(s["left"])
                    end = offset_of_token(s["right"])
                    if start.page == end.page:
                        append_span(models.Span(start=start, end=end))
                    else:
                        append_span(
                            models.Span(
                                start=start,
                                end=models.Offset(
                                    page=start.page, token=len(pages[start.page].tokens)
                                ),
                            )
                        )
                        append_span(
                            models.Span(
                                start=models.Offset(page=end.page, token=0), end=end
                            )
                        )
                el = models.TextElement(
                    start=offset_of_token(first_span["left"]), spans=spans, tags=tags
                )
            elements.append(el)

        element_types.types[element_type] = elements

    annotations = models.PdfAnnotations(
        tokens=token_sources,
        text_elements=models.TextElementSources(sources={source: element_types}),
    )
    return annotations


def process_grobid(
    sha: str,
    pdf_file: str,
    grobid_host: str = "http://s2-grobid-tokens.us-west-2.elasticbeanstalk.com",
    source: str = "grobid",
    env: str = "dev",
):
    """
    Integration for importing annotations from grobid.
    Depends on a grobid API built from our fork https://github.com/allenai/grobid.
    Fetches a PDF by sha, sends it to the Grobid API and inserts the resulting annotations
    Does nothing if Grobid annotations already exist for that PDF.

    sha: str
        The s2 sha for a pdf.
    pdf_file: str
        The path to the pdf file to process.
    grobid_host: str (optional, default = http://s2-grobid-tokens.us-west-2.elasticbeanstalk.com)
        The forked grobid API which we use to produce the annotations.
    source: str (optional, default = "grobid")
        The source name to use for inserting into the pdf structure service.
    env: str (optional, default = "dev")
        Whether to insert pdfs into the development
        or production version of the pdf structure service.
    """
    client = DefaultApi(
        ApiClient(
            Configuration(
                host=f"http://pdf-structure-{env}.us-west-2.elasticbeanstalk.com"
            )
        )
    )

    grobid_structure = fetch_grobid_structure(pdf_file, grobid_host)
    annotations = parse_annotations(grobid_structure, source)
    existing_annotations = client.get_annotations(
        sha, text_element_data="none", token_data="none"
    )

    if existing_annotations.tokens and source in existing_annotations.tokens.sources:
        return True

    try:
        client.add_annotations(sha, annotations)
        return True
    except ApiException as e:
        print(f"{sha} could not be downloaded due to {e}")
        return False
