import os
import logging
from importlib import import_module
from typing import Union, Dict


class DummyRequest(object):
    """
    DummyRequest. Used for compatibility with DRF.
    """

    def __init__(self, params: Dict[str, str]):
        self.GET = params
        self.body = "<DummyRequest: no body>"

    @property
    def query_params(self) -> Dict[str, str]:
        """
        More semantically correct name for request.GET.
        """
        return self.GET


def get_module():
    """
    Returns module that contains settings or None
    """
    module = os.environ.get("DJANGO_SETTINGS_MODULE", None) or os.environ.get(
        "SETTINGS_MODULE", None
    )
    return module if module is None else import_module(module.replace(".py", ""))


try:
    from rest_framework.request import Request as _Request
    from rest_framework.exceptions import APIException
    from rest_framework.status import (
        HTTP_400_BAD_REQUEST,
        HTTP_500_INTERNAL_SERVER_ERROR,
    )

    REQUEST_CLASS = _Request
except ImportError:
    logging.warning("Django Rest Framework is not installed, falling back to mocks.")

    # Define missing symbols
    class APIException(Exception):
        def __init__(self, detail: Union[dict, str]):
            self.detail = detail
            self.status_code = HTTP_500_INTERNAL_SERVER_ERROR
            super().__init__(detail)

    HTTP_400_BAD_REQUEST = 400
    HTTP_500_INTERNAL_SERVER_ERROR = 500

    # Define alias for compatibility
    module = get_module()
    if hasattr(module, "QVAL_REQUEST_CLASS"):
        REQUEST_CLASS = module.QVAL_REQUEST_CLASS
    else:
        REQUEST_CLASS = DummyRequest


Request = REQUEST_CLASS
