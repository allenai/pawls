from pythonjsonlogger import jsonlogger

from fastapi import UploadFile
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil


def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path


class StackdriverJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom log JSON log formatter that adds the severity member, allowing
    end users to filter logs by the level of the log message emitted.

    TODO: Parse request logs and add fields for each request element (user-agent
    processing time, etc)

    TODO:Add a timestamp that's used in place of Stackdriver's records (which
    reflect the time the log was written to Stackdriver, I think).
    """

    def add_fields(self, log_record, record, message_dict):
        super(StackdriverJsonFormatter, self).add_fields(
            log_record, record, message_dict
        )
        log_record["severity"] = record.levelname
