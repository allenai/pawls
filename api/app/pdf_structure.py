from typing import List
import os

from fastapi import HTTPException

from pdfstructure.client.v1.api.default_api import DefaultApi
from pdfstructure.client.v1.configuration import Configuration
from pdfstructure.client.v1.api_client import ApiClient
from pdfstructure.client.v1 import models as model

from app.patch import to_dict_patch

IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev")

# HACK: The OpenAPI generator used to generate the Python client
# for the pdf structure service has a bug which means it cannot
# deserialize itself properly if it has nested container types.
# This fixes it, so we are monkeypatching the one class we need.
# See: https://github.com/allenai/s2-pdf-structure-service/issues/11

model.TextElementTypes.to_dict = to_dict_patch
model.RegionTypes.to_dict = to_dict_patch

PDF_STRUCTURE_CLIENT = DefaultApi(
    ApiClient(
        Configuration(
            host=f"http://pdf-structure-{IN_PRODUCTION}.us-west-2.elasticbeanstalk.com"
        )
    )
)


class Config:
    """
    Configuration for anything related to pdfs. We wrap this up in a class
    so that it's easier to test.

    PDF_STORE_PATH: str
        Where the raw pdfs are stored for annotation. In production, this uses
        Skiff Files.
    """

    PDF_STORE_PATH: str = "/skiff_files/apps/pawls/pdfs/"


# TODO(Mark): Wrap this in a LRU cache.
def _get_annotations(sha: str) -> model.PdfAnnotations:
    return PDF_STRUCTURE_CLIENT.get_annotations(sha)


def filter_token_source_for_pages(token_source_response, pages: List[int]):
    """
    Given a JSON response from `get_annotations`, this function filters
    the response to contain only token source information from the specified
    pages.

    token_source_response:
        The return value from `get_annotations()`
    pages: List[int]
        The pages to select.
    """
    response = {"tokens": {"sources": {}}}

    for source, data in token_source_response["tokens"]["sources"].items():

        new = data.copy()
        new["pages"] = [data["pages"][page] for page in pages]
        response["tokens"]["sources"][source] = new

    return response


def filter_text_elements_for_pages(text_element_response, pages: List[int]):
    """
    Given a JSON response from `get_annotations`, this function filters
    the response to contain only text element information from the specified
    pages.

    text_element_response:
        The return value from `get_annotations()`
    pages: List[int]
        The pages to select.
    """
    response = {"text_elements": {"sources": {}}}

    for source, data in text_element_response["text_elements"]["sources"].items():

        new = data.copy()

        for element_type, element_data in data["types"].items():

            new["types"][element_type] = [
                item for item in element_data if item["start"]["page"] in pages
            ]

        response["text_elements"]["sources"][source] = new

    return response


def filter_regions_for_pages(regions_response, pages: List[int]):
    """
    Given a JSON response from `get_annotations`, this function filters
    the response to contain only region information from the specified
    pages.

    token_source_response:
        The return value from `get_annotations()`
    pages: List[int]
        The pages to select.
    """
    response = {"regions": {"sources": {}}}

    for source, data in regions_response["regions"]["sources"].items():

        new = data.copy()

        for element_type, element_data in data["types"].items():

            new["types"][element_type] = [
                item for item in element_data if item["page"]["index"] in pages
            ]

        response["regions"]["sources"][source] = new

    return response


def get_annotations(
    sha: str,
    token_sources: List[str] = None,
    text_element_sources: List[str] = None,
    region_sources: List[str] = None,
):

    full_annotations = _get_annotations(sha)
    response = {}

    if token_sources:
        if full_annotations.tokens is None:
            raise HTTPException(
                status_code=404, detail=f"Non-existent token annotations for sha {sha}"
            )

        # Short circuit logic for all annotations.
        if "all" in token_sources:
            response["tokens"] = full_annotations.tokens.to_dict()
        else:
            response["tokens"] = {"sources": {}}
            for source in token_sources:
                data = full_annotations.tokens.sources.get(source, None)
                if data is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Non-existent token source f{source} for sha {sha}",
                    )

                response["tokens"]["sources"][source] = data.to_dict()

    if text_element_sources:
        if full_annotations.text_elements is None:
            raise HTTPException(
                status_code=404,
                detail=f"Non-existent text element annotations for sha {sha}",
            )

        # Short circuit logic for all annotations.
        if "all" in text_element_sources:
            response["text_elements"] = full_annotations.text_elements.to_dict()

        else:
            response["text_elements"] = {"sources": {}}
            for source in text_element_sources:
                data = full_annotations.text_elements.sources.get(source, None)
                if data is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Non-existent text element source f{source} for sha {sha}",
                    )

                response["text_elements"]["sources"][source] = data.to_dict()

    if region_sources:
        if full_annotations.regions is None:
            raise HTTPException(
                status_code=404, detail=f"Non-existent region annotations for sha {sha}"
            )

        # Short circuit logic for all annotations.
        if "all" in region_sources:
            response["regions"] = full_annotations.regions.to_dict()

        else:
            response["regions"] = {"sources": {}}
            for source in region_sources:
                data = full_annotations.regions.sources.get(source, None)
                if data is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Non-existent region source f{source} for sha {sha}",
                    )

                response["regions"]["sources"][source] = data.to_dict()

    return response
