from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

import requests


class APICaller(object):
    def __init__(self, host, base_url, headers=None):
        self._host = host
        self._base_url = base_url
        self._headers = headers

    def _call(self, method="get", path="/", *args, **kwargs):
        message = ""
        requester = getattr(requests, method.lower())
        if path.startswith("/"):
            url = "/".join([self._host, path])
        else:
            url = "/".join([self._host, self._base_url, path])

        response = requester(url=url, headers=self._headers, *args, **kwargs)

        if method in ["get", "post", "patch", "put"]:
            response_json = response.json()
            if response_json:
                if "data" in response_json:
                    # TODO : Create a APIResponse object instead of returning a tuple
                    return (
                        response_json["data"],
                        response_json.get("meta"),
                        response_json.get("links"),
                        response_json.get("included"),
                    )
                elif "errors" in response_json:
                    message = f"TFE API return errors {response.status_code}:"
                    message += str(response_json)
            if response.status_code < 400:
                return True
        elif method in ["delete"] and response.status_code < 400:
            return True

        if not message and response.status_code >= 400:
            message = "Error status code: {}".format(response.status_code)
            message += response.data
        raise Exception()

    @staticmethod
    def _dict_to_params(object_name, object_content):
        filters = {}
        for object_type, content in object_content.items():
            for field_name, field_value in content.items():
                filters[f"{object_name}[{object_type}][{field_name}]"] = field_value
        return filters

    def get_list(
        self,
        params=None,
        page_number=1,
        page_size=20,
        filters=None,
        include=None,
        *args,
        **kwargs,
    ):
        if not params:
            params = dict()
        if filters:
            params.extend(self._dict_to_params("filter", filters))

        if page_size:
            params["page[size]"] = page_size
        if page_number:
            params["page[number]"] = page_number
        if include:
            params["include"] = include

        data, meta, links, included = self._call(method="get", params=params, **kwargs)

        if isinstance(data, Iterable):
            while True:
                yield data, meta, links, included

                if meta and "pagination" in meta:
                    params["page[number]"] = meta["pagination"].get("next-page")
                    if params["page[number]"]:
                        data, meta, links, included = self._call(
                            method="get", params=params, **kwargs
                        )
                        continue

                break
        else:
            raise Exception("data is not a list")

    def get_raw(self, path, *args, **kwargs):
        response = requests.get(path)
        if response.status_code < 400:
            return response.text

    def get(self, *args, **kwargs):
        return self._call(method="get", **kwargs)

    def put(self, *args, **kwargs):
        return self._call(method="put", **kwargs)

    def post(self, *args, **kwargs):
        return self._call(method="post", **kwargs)

    def patch(self, *args, **kwargs):
        return self._call(method="patch", **kwargs)

    def delete(self, *args, **kwargs):
        return self._call(method="delete", **kwargs)
