from typing import List, Optional, Dict
import logging
import os
import json
from base64 import b64encode

from fastapi import FastAPI, Query, Response
from fastapi.responses import FileResponse

from app.pdf_structure import get_annotations
from app.utils import StackdriverJsonFormatter


IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev") 

handlers = None

if IN_PRODUCTION == "prod":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StackdriverJsonFormatter())
    handlers = [json_handler]

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', default=logging.INFO),
    handlers=handlers
)
logger = logging.getLogger("uvicorn")


app = FastAPI()


@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar, and the Kubernetes health check, require that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return {}


@app.get("/api/pdf/{sha}")
def get_pdf(sha: str):

    return FileResponse("/skiff_files/")




@app.get("/api/tokens/{sha}")
def get_tokens(sha: str, sources: Optional[List[str]] = Query(["all"])):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    sources: List[str] (default = "all")
        The annotation sources to fetch. This allows fetching of specific annotations.
    """
    response = get_annotations(
        sha, 
        token_sources=sources,
    )
    return response

@app.get("/api/elements/{sha}")
def get_elements(sha: str, sources: Optional[List[str]] = Query(["all"])):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    source: str (default = "all")
        The annotation sources to fetch. This allows fetching of specific annotations.
    """
    response = get_annotations(
        sha, 
        text_element_sources=sources
    )
    return Response(content=json.dumps(response), media_type="application/json")


@app.get("/api/regions/{sha}")
def get_regions(sha: str, sources: Optional[List[str]] = Query(["all"])):
    """
    sha: str
        PDF sha to retrieve from the PDF structure service.
    source: str (default = "all")
        The annotation sources to fetch. This allows fetching of specific annotations.
    """
    response = get_annotations(
        sha, 
        region_sources=sources,
    )
    return response
