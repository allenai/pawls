from typing import List, Optional
import logging
import os
import json
import glob

from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.responses import FileResponse

from app import pdf_structure
from app.metadata import PaperMetadata
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
pre_serve.maybe_download_pdfs(configuration)

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

    metadata = os.path.join(configuration.output_directory, sha, f"{sha}.json")
    exists = os.path.exists(metadata)

    if exists:
        return PaperMetadata(**json.load(metadata))
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
def get_labels() -> List[str]:
    """
    Get the labels used for annotation for this app.
    """
    return configuration.labels


@app.get("/api/annotation/allocation")
def get_allocation(x_auth_request_email: str = Header(None)) -> List[str]:
    """
    Get the allocated pdfs for this user. We use the X-Auth-Request-Email
    header to identify the user, which needs to correlate with the users
    present in the annotators.json config file.
    """

    if x_auth_request_email is None:
        raise HTTPException(status_code=401, detail="Not authenticated for annotation.")

    allocation = annotators.allocations.get(x_auth_request_email, None)
    if allocation is None:
        raise HTTPException(status_code=404, detail="No annotations allocated!")

    return allocation
