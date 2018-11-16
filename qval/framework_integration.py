import os
import json
import logging
import functools
from typing import Union, Dict
from importlib import import_module


class _EnvironSettings(object):
    """
    Lookups attribute calls in the environment.
    """
    def __getattr__(self, item):
        item = os.environ.get(item)
        # Support `hasattr()`
        if item is None:
            raise AttributeError
        return item


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

Request = DummyRequest


def get_module():
    """
    Returns module containing app settings.
    """
    module = None
    modules = ["DJANGO_SETTINGS_MODULE", "SETTINGS_MODULE"]
    for module in map(os.environ.get, modules):
        if module is not None:
            module = module.replace(".py", "").replace("/", ".")
            break
    return _EnvironSettings() if module is None else import_module(module)

module = get_module()


def load_symbol(path: Union[object, str]):
    """
    Import symbol using provided path.

    :param path: path to an object, e.g. my.module.func_1
    :return: loaded symbol
    """
    # Path is a symbol
    if not isinstance(path, str):
        return path
    _mod, _symbol = path.rsplit('.', maxsplit=1)
    return getattr(import_module(_mod), _symbol)


try:
    from rest_framework.request import Request as _Request
    from rest_framework.exceptions import APIException
    from rest_framework.status import (
        HTTP_400_BAD_REQUEST,
        HTTP_500_INTERNAL_SERVER_ERROR,
    )

    Request = _Request
except ImportError:
    # Define missing symbols
    class APIException(Exception):

        def __init__(self, detail: Union[dict, str]):
            self.detail = detail
            self.status_code = HTTP_500_INTERNAL_SERVER_ERROR
            super().__init__(detail)

    HTTP_400_BAD_REQUEST = 400
    HTTP_500_INTERNAL_SERVER_ERROR = 500

    if hasattr(module, "QVAL_REQUEST_CLASS"):
        Request = load_symbol(module.QVAL_REQUEST_CLASS)


if hasattr(module, "QVAL_MAKE_REQUEST_WRAPPER"):
    _make_request = load_symbol(module.QVAL_MAKE_REQUEST_WRAPPER)
else:
    def _make_request(f):
        """
        Wraps default `utils.make_request()` function. Does nothing.
        """
        @functools.wraps(f)
        def wrapper(request):
            return f(request)
        return wrapper


def setup_flask_error_handlers(app: "flask.Flask"):
    """
    Setups error handler for APIException.

    :param app: flask app
    :return: None
    """
    from flask import jsonify

    def handle_api_exception(error: APIException):
        response = error.detail
        if isinstance(response, str):
            response = {"error": response}
        response = jsonify(response)
        response.status_code = error.status_code
        return response

    app.errorhandler(APIException)(handle_api_exception)
