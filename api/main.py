from typing import List, Optional
import logging
import os

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse

from app import pdf_structure
from app.utils import StackdriverJsonFormatter, bulk_fetch_pdfs_for_s2_ids


IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev")

handlers = None

if IN_PRODUCTION == "prod":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StackdriverJsonFormatter())
    handlers = [json_handler]

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", default=logging.INFO), handlers=handlers
)
logger = logging.getLogger("uvicorn")


app = FastAPI()


@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar, and the Kubernetes health check, require
    that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return {}


@app.get("/api/pdf/{sha}")
async def get_pdf(sha: str, download: bool = False):
    """
    Fetches a PDF. If the pdf doesn't exist in the PDF file store,
    it is downloaded from S3 if the `download` query parameter is passed.

    sha: str
        The sha of the pdf to return.
    download: bool (default = False)
        Whether or not to download the pdf from S3 if it
        is not present locally.
    """
    pdf = os.path.join(pdf_structure.Config.PDF_STORE_PATH, f"{sha}.pdf")
    pdf_exists = os.path.exists(pdf)
    if not pdf_exists and download:

        result = bulk_fetch_pdfs_for_s2_ids([sha], Config.PDF_STORE_PATH)

        if sha in result["not_found"]:
            raise HTTPException(status_code=404, detail=f"pdf {sha} not found.")

        if sha in result["error"]:
            raise HTTPException(status_code=404, detail=f"An error occured whilst fetching {sha}.")

    elif not pdf_exists:
        raise HTTPException(status_code=404, detail=f"pdf {sha} not found.")

    return FileResponse(pdf, media_type="application/pdf")


@app.get("/api/tokens/{sha}")
def get_tokens(
    sha: str,
    sources: Optional[List[str]] = Query(["all"]),
    pages: Optional[List[str]] = Query(None)
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


@app.get("/api/elements/{sha}")
def get_elements(
    sha: str,
    sources: Optional[List[str]] = Query(["all"]),
    pages: Optional[List[str]] = Query(None)
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


@app.get("/api/regions/{sha}")
def get_regions(
    sha: str,
    sources: Optional[List[str]] = Query(["all"]),
    pages: Optional[List[str]] = Query(None)
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
