from typing import List
import os
import six

from fastapi import HTTPException

from pdfstructure.client.v1.api.default_api import DefaultApi
from pdfstructure.client.v1.configuration import Configuration
from pdfstructure.client.v1.api_client import ApiClient
from pdfstructure.client.v1 import models as model

IN_PRODUCTION = os.getenv("IN_PRODUCTION", "dev")

# HACK: The OpenAPI generator used to generate the Python client
# for the pdf structure service has a bug which means it cannot
# deserialize itself properly if it has nested container types.
# This fixes it, so we are monkeypatching the one class we need.
# See: https://github.com/allenai/s2-pdf-structure-service/issues/11


def to_dict_patch(self):
    """Returns the model properties as a dict"""

    def handle_list(item):

        ret = []
        for i in item:
            if hasattr(i, "to_dict"):
                ret.append(i.to_dict())
            else:
                ret.append(i)
        return ret

    def handle_dict(item):
        key, value = item

        if hasattr(value, "to_dict"):
            return (key, value.to_dict())
        elif isinstance(value, list):
            return (key, handle_list(value))
        else:
            return item

    result = {}
    for attr, _ in six.iteritems(self.openapi_types):
        value = getattr(self, attr)
        if isinstance(value, list):
            result[attr] = list(
                map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
            )
        elif hasattr(value, "to_dict"):
            result[attr] = value.to_dict()
        elif isinstance(value, dict):
            result[attr] = dict(map(handle_dict, value.items()))
        else:
            result[attr] = value

    return result


model.TextElementTypes.to_dict = to_dict_patch

pdf_structure_client = DefaultApi(
    ApiClient(
        Configuration(
            host=f"http://pdf-structure-{IN_PRODUCTION}.us-west-2.elasticbeanstalk.com"
        )
    )
)


# TODO(Mark): Wrap this in a LRU cache.
def _get_annotations(sha: str) -> model.PdfAnnotations:
    return pdf_structure_client.get_annotations(sha)


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
