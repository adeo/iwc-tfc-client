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
        requester = getattr(requests, method.lower())
        if path.startswith("/"):
            url = "/".join([self._host, path])
        else:
            url = "/".join([self._host, self._base_url, path])

        response = requester(
            url=url, headers=self._headers, **kwargs
        )

        response_json = response.json()
        if method in ["get", "post", "patch", "put"]:
            if response_json:
                if "data" in response_json:
                    return response_json["data"], response_json.get("meta"), response_json.get("links"),
                elif "errors" in response_json:
                    message = "TFE API return errors:"
                    message += str(response_json)
        elif method in ["delete"] and response.status_code < 400:
            return True

        if not message and response.status_code >= 400:
            message = "Error status code: {}".format(response.status_code)
        raise Exception("TFE API return errors:\n{}".format(message))

    def get_paginated(self, page_size=20, page_number=1, *args, **kwargs):
        params = dict()
        if page_size:
            params["page[size]"] = page_size
        if page_number:
            params["page[number]"] = page_number
        return self.get_list(params=params, *args, **kwargs)

    def get_filtered(self, workspace=None, organization=None, *args, **kwargs):
        params = dict()
        if workspace:
            params["filter[workspace][name]"] = workspace
        if organization:
            params["filter[organization][name]"] = organization
        return self.get_list(params=params, *args, **kwargs)

    def get_list(self, params=None, *args, **kwargs):
        if not params:
            params = dict()

        data, meta, links = self._call(method="get", params=params, **kwargs)

        if isinstance(data, Iterable):
            while True:
                for data_item in data:
                    yield data_item

                if meta and "pagination" in meta:
                    params["page[number]"] = meta["pagination"].get("next-page")
                    if params["page[number]"]:
                        data, meta, links = self._call(
                            method="get", params=params, **kwargs
                        )
                        continue

                break
        else:
            raise Exception("data is not a list nor a mapping")

    def get_one(self, *args, **kwargs):
        data, meta, links = self._call(method="get", **kwargs)
        if isinstance(data, Mapping):
            return data
        else:
            raise Exception("data haven't exactly one element ({} found)".format(len(data)))

    def put(self, *args, **kwargs):
        return self._call(method="put", **kwargs)

    def post(self, *args, **kwargs):
        return self._call(method="post", **kwargs)

    def patch(self, *args, **kwargs):
        return self._call(method="patch", **kwargs)

    def delete(self, *args, **kwargs):
        return self._call(method="delete", **kwargs)
