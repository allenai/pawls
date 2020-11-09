from typing import NamedTuple, List, Dict
import json


class Configuration(NamedTuple):
    """
    General configuration for the annotation tool.

    output_directory: str, required.
        The directory where the pdfs, metadata and
        annotation output will be stored.
    labels: List[Dict[str, str]], required.
        The labels in use for annotation.
    relations: List[Dict[str, str]], required.
        The relations in use for annotation.
    """

    output_directory: str
    labels: List[Dict[str, str]]
    relations: List[Dict[str, str]]


def load_configuration(filepath: str) -> Configuration:

    blob = json.load(open(filepath))
    return Configuration(**blob)
