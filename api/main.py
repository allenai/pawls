from typing import List, Optional, Dict
import logging
import os
import json

from fastapi import FastAPI

from app.utils import StackdriverJsonFormatter

handlers = None
if os.getenv("IN_PRODUCTION", "dev") == "prod":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StackdriverJsonFormatter())
    handlers = [json_handler]

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', default=logging.INFO),
    handlers=handlers
)
logger = logging.getLogger("uvicorn")


app = FastAPI(root_path="/api")

@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar, and the Kubernetes health check, require that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return {}
