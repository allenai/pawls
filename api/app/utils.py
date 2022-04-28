import logging
from pythonjsonlogger import jsonlogger
from aiofiles import open as aiopen
from typing import Union
import hashlib

from fastapi import UploadFile
from pathlib import Path

import shutil

logger = logging.getLogger(__file__)

async def async_save_received_file_to_disk(upload_file: UploadFile,
                                           dest_dir: Union[str, Path],
                                           dest_filename: str = None) -> Path:
    dest_filename = dest_filename or upload_file.filename
    dest_path = Path(dest_dir) / dest_filename

    async with aiopen(dest_path, 'wb') as f:
        content = True
        while content:
            content = await upload_file.read(1024)
            await f.write(content)

    return dest_path


def hash_file(path: Union[str, Path]) -> str:
    block_size = 65536

    file_hash = hashlib.sha256()
    with open(path, 'rb') as fp:
        fb = fp.read(block_size)
        while len(fb) > 0:
            file_hash.update(fb)
            fb = fp.read(block_size)

    return str(file_hash.hexdigest())


def save_received_file_to_disk(upload_file: UploadFile,
                               dest_dir: Union[str, Path],
                               dest_filename: str = None) -> Path:
    dest_filename = dest_filename or upload_file.filename
    dest_path = Path(dest_dir) / dest_filename

    with open(dest_path, 'wb') as f:
        f.write(upload_file.read())

    return dest_path


def move_file(src: Union[str, Path],
              dst: Union[str, Path],
              mkdirs: bool = True) -> Path:
    src, dst = map(Path, (src, dst))
    if src.exists():
        if mkdirs:
            dst.parent.mkdir(exist_ok=True)
        return shutil.move(src, dst)
    else:
        raise FileNotFoundError(f'{src} is not a valid path')


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