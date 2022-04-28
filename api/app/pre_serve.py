import logging
import os
from pathlib import Path
from typing import NamedTuple, List, Dict, Union
import json

logger = logging.getLogger('uvicorn')


class Configuration(NamedTuple):
    """
    General configuration for the annotation tool.

    output_directory: str, required.
        The directory where the pdfs and
        annotation output will be stored.
    labels: List[Dict[str, str]], required.
        The labels in use for annotation.
    relations: List[Dict[str, str]], required.
        The relations in use for annotation.
    users_file: Name str, required
        Filename where list of allowed users is specified.
    allow_unassigned_users_to_see_everything:  bool, required
        If True, users who have no papers assigned can see
        all papers that have been uploaded.
    """

    output_directory: str
    # "file" for local, "s3" for s3
    protocol: str
    labels: List[Dict[str, str]]
    relations: List[Dict[str, str]]
    users_file: str
    allow_unassigned_users_to_see_everything: bool
    in_production: bool
    storage_options: dict = {}


def load_configuration(path: Union[str, Path]) -> Configuration:
    path = Path(path)

    logger.info(f'Reading config from {path}')

    try:
        in_production = os.getenv("IN_PRODUCTION", "dev") == 'prod'

        with open(path, 'r', encoding='utf-8') as f:
            blob = json.load(f)

        if not in_production:
            # overrides for dev in local containers
            users_file = path.parent / 'allowed_users_local_development.txt'
            blob.update(dict(users_file=users_file))

        config = Configuration(in_production=in_production, **blob)

        logger.info(f'parsed config: {config}')
        return config
    except TypeError as e:
        raise TypeError(f"Error loading configuration file {path}, "
                        f"maybe you're missing a required field? "
                        f"Exception string: {e}") from e
    except Exception as e:
        raise type(e)(f"Error loading configuration file {path}") from e
