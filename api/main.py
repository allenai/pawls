from typing import List, Optional, Dict
import logging
import os
import json

from fastapi import FastAPI, HTTPException

from pdfstructure.client.v1.api.default_api import DefaultApi
from pdfstructure.client.v1.configuration import Configuration
from pdfstructure.client.v1.api_client import ApiClient
from pdfstructure.client.v1 import models as model


from app.utils import StackdriverJsonFormatter

IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev") 

handlers = None
if  IN_PRODUCTION == "prod":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StackdriverJsonFormatter())
    handlers = [json_handler]

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', default=logging.INFO),
    handlers=handlers
)
logger = logging.getLogger("uvicorn")



pdf_structure_client = DefaultApi(ApiClient(Configuration(host=f"http://pdf-structure-{IN_PRODUCTION}.us-west-2.elasticbeanstalk.com")))


app = FastAPI(root_path="/api")

@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar, and the Kubernetes health check, require that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return {}


@app.get("/tokens/{sha}")
def get_tokens(sha: str, source: Optional[str] = "all"):
    """

    sha: str
        PDF sha to retrieve from the PDF structure service.
    source: str (default = "all")
        The comma separated string of annotation sources to fetch. This allows fetching of specific annotations.

    """
    annotations = pdf_structure_client.get_annotations(sha, token_sources=source)

    tokens = annotations.get("tokens", None)
    if tokens is None:
        raise HttpException(status_code=404, detail=f"No PDF found for {sha}, or invalid source ({source})")

    return tokens["tokens"]["sources"].to_dict()

@app.get("/elements/{sha}")
def get_text_elements(sha: str, source= "all"):
    pass

@app.get("/region/{sha}")
def get_region(sha: str, source= "all"):
    pass

