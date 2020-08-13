from typing import List, Optional, Dict
import logging
import os
import json

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


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
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])


@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar requires that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return {}
