from typing import List, Optional, Dict
import logging
import os
import json
import glob

from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder

from app import pdf_structure
from app.metadata import PaperMetadata, PaperInfo, PaperStatus
from app.annotations import Annotation, RelationGroup, PdfAnnotation
from app.utils import StackdriverJsonFormatter
from app import pre_serve

IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev")
DEVELOPMENT_USER = "development_user"

CONFIGURATION_FILE = os.getenv(
    "PAWLS_CONFIGURATION_FILE", "/usr/local/src/skiff/app/api/config/configuration.json"
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

app = FastAPI()


def get_user_from_header(header: Optional[str]) -> Optional[str]:
    """
    In development (i.e locally, when not deployed to the skiff cluster)
    the X-Auth-Request-Email header is not present. In development,
    we use the `development_user` role instead. If we are in production
    and there is no header, we return None so calling functions can
    handle the web response appropriately.
    """
    if header is None and IN_PRODUCTION == "dev":
        return DEVELOPMENT_USER
    elif header is None:
        return None
    else:
        return header.split("@")[0]


def all_pdf_shas() -> List[str]:
    pdfs = glob.glob(f"{configuration.output_directory}/*/*.pdf")
    return [p.split("/")[-2] for p in pdfs]


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


@app.post("/api/doc/{sha}/status")
def set_pdf_status(
    sha: str,
    status: PaperStatus,
    x_auth_request_email: str = Header(None)
):
    user = get_user_from_header(x_auth_request_email)
    if user is None:
        raise HTTPException(403, "Invalid user email header.")

    status_path = os.path.join(configuration.output_directory, "status", f"{user}.json")
    exists = os.path.exists(status_path)
    if not exists and IN_PRODUCTION == "dev":
        with open(status_path, "w+") as new:
            blob = {
                sha: PaperStatus.empty() for sha in all_pdf_shas()
            }
            json.dump(jsonable_encoder(blob), new)
    elif not exists:
        raise HTTPException(status_code=404, detail="No annotations allocated!")

    with open(status_path, "r+") as st:
        status_json = json.load(st)
        status_json[sha] = jsonable_encoder(status)
        st.seek(0)
        json.dump(status_json, st)


@app.get("/api/doc/{sha}/annotations")
def get_annotations(
    sha: str,
    x_auth_request_email: str = Header(None)
) -> PdfAnnotation:
    user = get_user_from_header(x_auth_request_email)
    if user is None:
        raise HTTPException(403, "Invalid user email header.")
    annotations = os.path.join(configuration.output_directory, sha, f"{user}_annotations.json")
    exists = os.path.exists(annotations)

    if exists:
        return json.load(open(annotations))
    else:
        return {"annotations": [], "relations": []}


@app.post("/api/doc/{sha}/annotations")
def save_annotations(
    sha: str,
    annotations: List[Annotation],
    relations: List[RelationGroup],
    x_auth_request_email: str = Header(None)
):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    annotations: List[Annotation]
        A json blob of the annotations to save.
    relations: List[RelationGroup]
        A json blob of the relations between the annotations to save.
    x_auth_request_email: str
        This is a header sent with the requests which specifies the user login.
        For local development, this will be None, because the authentication
        is controlled by the Skiff Kubernetes cluster.
    """

    user = get_user_from_header(x_auth_request_email)
    if user is None:
        raise HTTPException(403, "Invalid user email header.")
    annotations_path = os.path.join(configuration.output_directory, sha, f"{user}_annotations.json")
    json_annotations = [jsonable_encoder(a) for a in annotations]
    json_relations = [jsonable_encoder(r) for r in relations]

    json.dump({
        "annotations": json_annotations,
        "relations": json_relations
    }, open(annotations_path, "w+"))
    return {}


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


@app.get("/api/annotation/allocation/info")
def get_allocation_info(x_auth_request_email: str = Header(None)) -> List[PaperInfo]:

    # In development, the app isn't passed the x_auth_request_email header,
    # meaning this would always fail. Instead, to smooth local development,
    # we always return all pdfs, essentially short-circuiting the allocation
    # mechanism.
    user = get_user_from_header(x_auth_request_email)
    if user is None:
        raise HTTPException(403, "Invalid user email header.")

    status_dir_exists = os.path.exists(os.path.join(configuration.output_directory, "status"))
    if user == DEVELOPMENT_USER or not status_dir_exists:
        all_pdfs = all_pdf_shas()
        response = []
        for sha in all_pdfs:
            response.append(
                PaperInfo(
                    metadata=PaperMetadata(**get_metadata(sha)),
                    status=PaperStatus.empty(),
                    sha=sha
                )
            )
        return response

    status_path = os.path.join(configuration.output_directory, "status", f"{user}.json")
    if not os.path.exists(status_path):
        raise HTTPException(status_code=404, detail="No annotations allocated!")

    status_json = json.load(open(status_path))

    response = []

    for sha, status in status_json.items():
        response.append(
                PaperInfo(
                    metadata=PaperMetadata(**get_metadata(sha)),
                    status=PaperStatus(**status),
                    sha=sha
                )
        )

    return response
