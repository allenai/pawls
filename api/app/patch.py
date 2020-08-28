import six

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
