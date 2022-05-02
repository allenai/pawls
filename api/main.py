import tempfile
from typing import List, Optional, Dict
import logging
import os
from pathlib import Path

from fastapi import (
    FastAPI, HTTPException, Header, Response, Body, File, UploadFile
)
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder

from app.storage import StorageManager, UsersManager
from app.metadata import PaperStatus, Allocation
from app.annotations import Annotation, RelationGroup, PdfAnnotation
from app.utils import (
    StackdriverJsonFormatter,
    async_save_received_file_to_disk,
    move_file,
    hash_file
)
from app.pdfplumber import process_pdfplumber
from app import pre_serve

CONFIGURATION_FILE = Path(
    os.getenv("PAWLS_CONFIGURATION_FILE",
              "/usr/local/src/skiff/app/api/config/configuration.json")
)

# The annotation app requires a bit of set up.
configuration = pre_serve.load_configuration(CONFIGURATION_FILE)

storage_manager = StorageManager(protocol=configuration.protocol,
                                 root=configuration.output_directory,
                                 **configuration.storage_options)
users_manager = UsersManager(configuration.users_file)

handlers = None

if configuration.in_production == "prod":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StackdriverJsonFormatter())
    handlers = [json_handler]

logging.basicConfig(level=os.environ.get("LOG_LEVEL", default=logging.INFO),
                    handlers=handlers)

# boto3 logging is _super_ verbose.
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("nose").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
logging.getLogger("pdfminer").setLevel(logging.CRITICAL)
logging.getLogger("fsspec").setLevel(logging.CRITICAL)
logging.getLogger("s3fs").setLevel(logging.CRITICAL)
logging.getLogger("aiobotocore").setLevel(logging.CRITICAL)

logger = logging.getLogger("uvicorn")

app = FastAPI()


def get_user_from_header(user_email: Optional[str]) -> Optional[str]:
    """
    Call this function with the X-Auth-Request-Email header value. This must
    include an "@" in its value.

    * In production, this is provided by Skiff after the user authenticates.
    * In development, it is provided in the NGINX proxy configuration file local.conf.

    If the value isn't well formed, or the user isn't allowed, an exception is
    thrown.
    """
    if "@" not in user_email:
        raise HTTPException(403, "Forbidden")

    if not users_manager.is_valid_user(user_email):
        raise HTTPException(403, "Forbidden")

    return user_email


@app.get("/", status_code=204)
def read_root():
    """
    Skiff's sonar, and the Kubernetes health check, require
    that the server returns a 2XX response from it's
    root URL, so it can tell the service is ready for requests.
    """
    return Response(status_code=204)


@app.get("/api/doc/{sha}/pdf")
async def get_pdf(sha: str):
    """
    Fetches a PDF.

    sha: str
        The sha of the pdf to return.
    """
    file_like = storage_manager.read_pdf_file_reader(sha)
    if file_like is not None:
        return StreamingResponse(file_like(), media_type="application/pdf")
    else:
        raise HTTPException(status_code=404, detail=f"pdf {sha} not found.")


@app.get("/api/doc/{sha}/title")
async def get_pdf_title(sha: str) -> Optional[str]:
    """
    Fetches a PDF's title.

    sha: str
        The sha of the pdf title to return.
    """
    data = storage_manager.read_pdf_metadata()
    return data.get(sha, None)


@app.post("/api/doc/{sha}/comments")
def set_pdf_comments(
    sha: str, comments: str = Body(...), x_auth_request_email: str = Header(None)
):
    user = get_user_from_header(x_auth_request_email)

    storage_manager.write_user_status(
        user=user, sha=sha, data={"comments": comments}
    )

    return {}


@app.get("/api/doc/{sha}/junk")
def get_pdf_junk(sha: str,
                     x_auth_request_email: str = Header(None)):

    user = get_user_from_header(x_auth_request_email)
    status = storage_manager.read_user_status(user=user)
    return (status or {}).get(sha, {}).get('junk', False)


@app.post("/api/doc/{sha}/junk")
def set_pdf_junk(sha: str,
                 junk: bool = Body(...),
                 x_auth_request_email: str = Header(None)
):
    user = get_user_from_header(x_auth_request_email)
    storage_manager.write_user_status(
        user=user, sha=sha, data={"junk": junk}
    )
    return {}


@app.get("/api/doc/{sha}/finished")
def get_pdf_finished(sha: str,
                     x_auth_request_email: str = Header(None)):

    user = get_user_from_header(x_auth_request_email)
    status = storage_manager.read_user_status(user=user)
    return (status or {}).get(sha, {}).get('finished', False)


@app.post("/api/doc/{sha}/finished")
def set_pdf_finished(sha: str,
                     finished: bool = Body( ... ),
                     x_auth_request_email: str = Header(None)):

    user = get_user_from_header(x_auth_request_email)
    storage_manager.write_user_status(
        user=user, sha=sha, data={"finished": finished}
    )
    return {}


@app.get("/api/doc/{sha}/annotations")
def get_annotations(
    sha: str, x_auth_request_email: str = Header(None)
) -> PdfAnnotation:
    user = get_user_from_header(x_auth_request_email)
    return storage_manager.read_user_annotations(user=user, sha=sha)


@app.post("/api/doc/{sha}/annotations")
def save_annotations(
    sha: str,
    annotations: List[Annotation],
    relations: List[RelationGroup],
    x_auth_request_email: str = Header(None),
):
    # Update the annotations in the annotation json file.
    user = get_user_from_header(x_auth_request_email)

    storage_manager.write_user_annotations(
        user=user,
        sha=sha,
        annotations=[jsonable_encoder(a) for a in annotations],
        relations=[jsonable_encoder(r) for r in relations]
    )

    return {}


@app.get("/api/doc/{sha}/tokens")
def get_tokens(sha: str):
    """
    sha: str
        PDF sha to retrieve tokens for.
    """
    pdf_tokens = storage_manager.get_pdf_structure(sha)
    if pdf_tokens is None:
        raise HTTPException(status_code=404, detail="No tokens for pdf.")

    return pdf_tokens


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
def get_allocation_info(x_auth_request_email: str = Header(None)) -> Allocation:
    user = get_user_from_header(x_auth_request_email)
    status = storage_manager.read_user_status(user)

    if status is None:
        hasAllocatedPapers = False
        if configuration.allow_unassigned_users_to_see_everything:
            # If the user doesn't have allocated papers, they can see
            # all the PDFs but they can't save anything.
            papers = [PaperStatus.empty(sha, sha) for sha
                      in storage_manager.get_all_pdf_shas()]
        else:
            papers = []
    else:
        hasAllocatedPapers = True
        papers = [PaperStatus(**paper_status)
                  for paper_status in status.values()]

    response = Allocation(papers=papers,
                          hasAllocatedPapers=hasAllocatedPapers)

    logger.info({'user': user, 'response': response.dict()})

    return response


@app.get("/api/debug")
def get_debug(x_auth_request_email: str = Header(None)):
    response = {'email': x_auth_request_email}
    try:
        response['user'] = get_user_from_header(x_auth_request_email)
        response['status'] = storage_manager.read_user_status(response['user'])
    except Exception:
        response['status'] = None
        response['status'] = None

    return JSONResponse(response)


@app.get('/api/user')
def is_authorized(x_auth_request_email: str = Header(None)):
    # cheap endpoint to call to check if we can show a UI to
    # a user or not.

    try:
        user = get_user_from_header(x_auth_request_email)
        return JSONResponse(content={'email': x_auth_request_email,
                                     'user': user},
                            status_code=200)
    except Exception:
        return JSONResponse(content={'email': x_auth_request_email,
                                     'user': ''},
                            status_code=403)


@app.post("/api/upload")
async def upload_paper_ui(file: UploadFile = File(...),
                          x_auth_request_email: str = Header(None)):

    user = get_user_from_header(x_auth_request_email)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        logger.info(tmpdir)

        # get file, save to temp location, get hash
        file_name = file.filename
        tmp_fp = await async_save_received_file_to_disk(
            upload_file=file, dest_dir=tmpdir, dest_filename='tmp.pdf'
        )
        sha = hash_file(tmp_fp)

        # check if paper does not exist
        if sha not in storage_manager.read_pdf_metadata():

            # move newly received pdf to the right directory structure
            sha_fp = move_file(src=tmp_fp, dst=(tmpdir / sha / f'{sha}.pdf'))

            # this processes the pdf with pdfplumber
            process_pdfplumber(file_path=sha_fp)

            # move the entire directory to the target destination
            dst = storage_manager.add_pdf_dir(tmpdir / sha)

            # add the metadata for this pdf to the global metadata
            storage_manager.write_pdf_metadata({sha: file_name})
        else:
            dst = storage_manager.root / sha

    # create a user and add this paper to the user
    # (user will be create if they don't exist in the system)
    storage_manager.write_user_status(
        user=user,
        sha=sha,
        create_if_missing=True,
        data={"name": file_name}
    )

    response = {'user': user,
                'pdf_hash': sha,
                'file': str(file_name),
                'storage': str(dst)}
    logger.info(f'/api/upload', response)
    return JSONResponse(content=response, status_code=200)
