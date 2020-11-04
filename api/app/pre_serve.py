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
    pdfs: List[str], required.
        The pdfs that you want to annotate. This can be updated,
        and new pdfs will be _added_ to the annotation set. Removing
        pdfs from this list once the app has been started with them
        will not remove them from the annotation.
    preprocessors: List[str], optional (default = None)
        Optional pre-processing steps to apply to pdfs. Currently,
        the only supported option is "grobid".
    """

    output_directory: str
    labels: List[Dict[str, str]]
    relations: List[Dict[str, str]]
    pdfs: List[str]
    preprocessors: List[str] = None


class Annotators(NamedTuple):
    """
    Configuration for Annotators.

    annotators: List[str], required.
        A list of gmail emails for annotators.
        Currently these must be ai2 emails.
    allocations: Dict[str, List[str]], required.
        A mapping from annotator emails to lists of pdf shas
        to which they are assigned.
    """

    annotators: List[str]
    allocations: Dict[str, List[str]]


def load_configuration(filepath: str) -> Configuration:

    blob = json.load(open(filepath))
    return Configuration(**blob)


def load_annotators(filepath) -> Annotators:

    blob = json.load(open(filepath))
    return Annotators(**blob)
