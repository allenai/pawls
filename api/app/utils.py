import logging
from pythonjsonlogger import jsonlogger
from aiofiles import open as aiopen
from aiofiles.os import wrap
from aiofiles.tempfile import NamedTemporaryFile

from fastapi import UploadFile
from pathlib import Path
import shutil

copyfileobj = wrap(shutil.copyfileobj)

logger = logging.getLogger(__file__)

async def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix

        async with NamedTemporaryFile(delete=False, suffix=suffix, mode='wb') as tmp:
            content = True
            while content:
                content = await upload_file.read(1024)
                await tmp.write(content)
            # await copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)

        logger.debug(f'Uploaded to {tmp_path}')

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
