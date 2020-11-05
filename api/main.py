from typing import List, Optional, Dict
import logging
import os
import json
import glob

from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder

from app import pdf_structure
from app.metadata import PaperMetadata
from app.annotations import Annotation, RelationGroup, PdfAnnotation
from app.utils import StackdriverJsonFormatter
from app import pre_serve

IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev")

CONFIGURATION_FILE = os.getenv(
    "PAWLS_CONFIGURATION_FILE", "/usr/local/src/skiff/app/api/config/configuration.json"
)

ANNOTATORS_FILE = os.getenv(
    "PAWLS_ANNOTATORS_FILE", "/usr/local/src/skiff/app/api/config/annotators.json"
)

handlers = None

if IN_PRODUCTION == "prod":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StackdriverJsonFormatter())
    handlers = [json_handler]

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", default=logging.INFO), handlers=handlers
)
logger = logging.getLogger("uvicorn")

# boto3 logging is _super_ verbose.
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("nose").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)

# The annotation app requires a bit of set up.
configuration = pre_serve.load_configuration(CONFIGURATION_FILE)
annotators = pre_serve.load_annotators(ANNOTATORS_FILE)

app = FastAPI()


@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar, and the Kubernetes health check, require
    that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return {}


@app.get("/api/doc/{sha}")
def get_metadata(sha: str) -> PaperMetadata:

    metadata = os.path.join(configuration.output_directory, sha, "metadata.json")
    exists = os.path.exists(metadata)

    if exists:
        return json.load(open(metadata))
    else:
        raise HTTPException(404, detail=f"Metadata not found for pdf: {sha}")


@app.get("/api/doc/{sha}/pdf")
async def get_pdf(sha: str):
    """
    Fetches a PDF.

    sha: str
        The sha of the pdf to return.
    """
    pdf = os.path.join(configuration.output_directory, sha, f"{sha}.pdf")
    pdf_exists = os.path.exists(pdf)
    if not pdf_exists:
        raise HTTPException(status_code=404, detail=f"pdf {sha} not found.")

    return FileResponse(pdf, media_type="application/pdf")


@app.get("/api/doc/{sha}/annotations")
def get_annotations(sha: str) -> PdfAnnotation:
    annotations = os.path.join(configuration.output_directory, sha, "annotations.json")
    exists = os.path.exists(annotations)

    if exists:
        return json.load(open(annotations))
    else:
        return {"annotations": [], "relations": []}


@app.post("/api/doc/{sha}/annotations")
def save_annotations(
    sha: str,
    annotations: List[Annotation],
    relations: List[RelationGroup]
):
    annotations_path = os.path.join(configuration.output_directory, sha, "annotations.json")

    json_annotations = [jsonable_encoder(a) for a in annotations]
    json_relations = [jsonable_encoder(r) for r in relations]

    json.dump({
        "annotations": json_annotations,
        "relations": json_relations
    }, open(annotations_path, "w+"))
    return {}


@app.get("/api/docs")
def list_downloaded_pdfs() -> List[str]:
    """
    List the currently downloaded pdfs.
    """
    # TODO(Mark): Guard against metadata not being present also.
    pdfs = glob.glob(f"{configuration.output_directory}/*/*.pdf")
    return [p.split("/")[-2] for p in pdfs]


@app.get("/api/doc/{sha}/tokens")
def get_tokens(
    sha: str,
    sources: Optional[List[str]] = Query(["all"]),
    pages: Optional[List[str]] = Query(None),
):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    sources: List[str] (default = "all")
        The annotation sources to fetch.
        This allows fetching of specific annotations.
    pages: Optional[List[str]], (default = None)
        Optionally provide pdf pages to filter by.
    """
    response = pdf_structure.get_annotations(sha, token_sources=sources,)
    if pages is not None:
        response = pdf_structure.filter_token_source_for_pages(response, pages)

    return response


@app.get("/api/doc/{sha}/elements")
def get_elements(
    sha: str,
    sources: Optional[List[str]] = Query(["all"]),
    pages: Optional[List[str]] = Query(None),
):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    source: str (default = "all")
        The annotation sources to fetch.
        This allows fetching of specific annotations.
    pages: Optional[List[str]], (default = None)
        Optionally provide pdf pages to filter by.
    """
    response = pdf_structure.get_annotations(sha, text_element_sources=sources)

    if pages is not None:
        response = pdf_structure.filter_text_elements_for_pages(response, pages)
    return response


@app.get("/api/doc/{sha}/regions")
def get_regions(
    sha: str,
    sources: Optional[List[str]] = Query(["all"]),
    pages: Optional[List[str]] = Query(None),
):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    source: str (default = "all")
        The annotation sources to fetch.
        This allows fetching of specific annotations.
    pages: Optional[List[str]], (default = None)
        Optionally provide pdf pages to filter by.
    """
    response = pdf_structure.get_annotations(sha, region_sources=sources,)
    if pages is not None:
        response = pdf_structure.filter_regions_for_pages(response, pages)
    return response


@app.get("/api/annotation/labels")
def get_labels() -> List[Dict[str, str]]:
    """
    Get the labels used for annotation for this app.
    """
    return configuration.labels

@app.get("/api/annotation/relations")
def get_relations() -> List[Dict[str, str]]:
    """
    Get the relations used for annotation for this app.
    """
    return configuration.relations


@app.get("/api/annotation/allocation")
def get_allocation(x_auth_request_email: str = Header(None)) -> List[str]:
    """
    Get the allocated pdfs for this user. We use the X-Auth-Request-Email
    header to identify the user, which needs to correlate with the users
    present in the annotators.json config file.
    """

    # In development, the app isn't passed the x_auth_request_email header,
    # meaning this would always fail. Instead, to smooth local development,
    # we always return all pdfs, essentially short-circuiting the allocation
    # mechanism.
    if x_auth_request_email is None:
        return configuration.pdfs

    allocation = annotators.allocations.get(x_auth_request_email, None)

    # If there are no annotators configured, assume that all pdfs
    # are allocated to everyone.
    if not annotators.annotators and allocation is None:
        return configuration.pdfs

    elif allocation is None:
        raise HTTPException(status_code=404, detail="No annotations allocated!")

    return allocation


@app.get("/api/annotation/allocation/metadata")
def get_allocation_metadata(x_auth_request_email: str = Header(None)) -> List[PaperMetadata]:
    """
    Get the allocated pdfs for this user. We use the X-Auth-Request-Email
    header to identify the user, which needs to correlate with the users
    present in the annotators.json config file.
    """
    return [get_metadata(x) for x in get_allocation(x_auth_request_email)]
