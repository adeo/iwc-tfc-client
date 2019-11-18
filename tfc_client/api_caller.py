from collections.abc import Iterable, Mapping
from typing import Dict, Generator, Union

import requests

from .exception import APIException


class APIResponse(object):
    def __init__(self, response: Mapping):
        self.data = response.get("data", [])
        self.meta = response.get("meta", [])
        self.links = response.get("links", [])
        self.included = response.get("included", [])
        self.errors = response.get("errors", [])

    def __str__(self):
        if self.data:
            if isinstance(self.data, Iterable):
                return f"Data array with {len(self.data)} elements"
        elif self.errors:
            rval = list()
            for error in self.errors:
                if isinstance(error, Mapping):
                    error_elements = list()
                    for key, value in error.items():
                        if key == "source":
                            error_elements.append(
                                f". Please check: {value.get('pointer')}"
                            )
                        else:
                            error_elements.append(f"{key}: '{value}'")
                    rval.append(" ".join(error_elements))
                elif isinstance(error, str):
                    rval.append(error)
            return ", ".join(rval)


class APICaller(object):
    def __init__(self, host: str, base_url: str, headers: Mapping = None):
        self._host = host
        self._base_url = base_url
        self._headers = headers

    def _call(
        self, method: str = "get", path: str = "/", *args, **kwargs
    ) -> Union[APIResponse, bool]:
        message = ""
        requester = getattr(requests, method.lower())
        if path.startswith("/"):
            url = "/".join([self._host, path])
        else:
            url = "/".join([self._host, self._base_url, path])

        response = requester(url=url, headers=self._headers, *args, **kwargs)

        if response.status_code < 400:
            if method in ["get", "post", "patch", "put"]:
                response_json = response.json()
                if response_json and "data" in response_json:
                    return APIResponse(response_json)
                else:
                    return True
            elif method in ["delete"]:
                return True
        else:
            raise APIException(f"APIError code: {response.status_code}", response)

    @staticmethod
    def _dict_to_params(object_name: str, object_content: Mapping):
        filters = {}
        for object_type, content in object_content.items():
            for field_name, field_value in content.items():
                filters[f"{object_name}[{object_type}][{field_name}]"] = field_value
        return filters

    def get_list(
        self,
        params: Dict[str, str] = None,
        page_number=1,
        page_size=20,
        search: str = None,
        filters: Mapping = None,
        include: str = None,
        sort: str = None,
        *args,
        **kwargs,
    ) -> Generator[Union[APIResponse, bool], None, None]:
        if not params:
            params = dict()
        if filters:
            params.update(self._dict_to_params("filter", filters))

        if page_size:
            params["page[size]"] = page_size
        if page_number:
            params["page[number]"] = page_number
        if search:
            params["search[name]"] = search
        if include:
            params["include"] = include
        if sort:
            params["sort"] = sort

        api_response = self._call(method="get", params=params, **kwargs)

        if isinstance(api_response, APIResponse):
            while True:
                yield api_response

                if (
                    api_response.meta  # type: ignore
                    and "pagination" in api_response.meta  # type: ignore
                ):
                    params["page[number]"] = api_response.meta[  # type: ignore
                        "pagination"
                    ].get("next-page")
                    if params["page[number]"]:
                        api_response = self._call(method="get", params=params, **kwargs)
                        continue

                break
        else:
            raise TypeError("api_response is not an APIResponse instance")

    def get_raw(self, path: str, *args, **kwargs) -> str:
        response = requests.get(path)
        if response.status_code < 400:
            return response.text
        else:
            raise APIException("Error: {}".format(response.status_code), response)

    def get(self, *args, **kwargs) -> Union[APIResponse, bool]:
        return self._call(method="get", **kwargs)

    def put(self, *args, **kwargs) -> Union[APIResponse, bool]:
        return self._call(method="put", **kwargs)

    def post(self, *args, **kwargs) -> Union[APIResponse, bool]:
        return self._call(method="post", **kwargs)

    def patch(self, *args, **kwargs) -> Union[APIResponse, bool]:
        return self._call(method="patch", **kwargs)

    def delete(self, *args, **kwargs) -> Union[APIResponse, bool]:
        return self._call(method="delete", **kwargs)
