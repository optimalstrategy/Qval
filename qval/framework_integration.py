import logging
import os
from typing import Union, Dict
from importlib import import_module


class _EnvironSettings(object):
    """
    Lookups attribute calls in os.environ.
    """

    def __getattr__(self, item):
        item = os.environ.get(item)
        # Support `hasattr()`
        if item is None:
            raise AttributeError
        return item


class DummyRequest(object):
    """
    DummyRequest. Used for compatibility with frameworks.
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


def get_module() -> Union[_EnvironSettings, "Module"]:
    """
    Attempts to load settings module.
    If none of the supported env variables are defined, returns `_EnvironSettings()` object.
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
    Imports object using the given path.

    :param path: path to an object, e.g. my.module.func_1
    :return: loaded symbol
    """
    # Path is already a symbol
    if not isinstance(path, str):
        return path
    _mod, _symbol = path.rsplit(".", maxsplit=1)
    return getattr(import_module(_mod), _symbol)


# Check if DRF is installed
try:
    from rest_framework.request import Request as _Request
    from rest_framework.exceptions import APIException
    from rest_framework.status import (
        HTTP_400_BAD_REQUEST,
        HTTP_500_INTERNAL_SERVER_ERROR,
    )

    Request = _Request
    REST_FRAMEWORK = True
except ImportError:
    REST_FRAMEWORK = False

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


# Check if Django is installed
try:
    from django.http import HttpRequest, JsonResponse

    # Exit if DRF is installed
    if REST_FRAMEWORK:
        raise ImportError

    Request = HttpRequest

    class HandleAPIExceptionDjango(object):
        def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request):
            return self.get_response(request)

        def process_exception(self, _: Request, exception: Exception):
            if isinstance(exception, APIException):
                detail = exception.detail
                if isinstance(detail, str):
                    detail = {"error": detail}
                return JsonResponse(detail, status=exception.status_code)

    if hasattr(module, "MIDDLEWARE"):
        module.MIDDLEWARE.append("qval.framework_integration.HandleAPIExceptionDjango")
    else:
        logging.warning(
            "Unable to add APIException middleware to the MIDDLEWARE list. "
            "Django does not support APIException handling without DRF integration. "
            "Define DJANGO_SETTINGS_MODULE or add 'qval.framework_integration.HandleAPIExceptionDjango' "
            "to the MIDDLEWARE list."
        )
except ImportError:
    pass


# Check if custom wrapper is provided
if hasattr(module, "QVAL_MAKE_REQUEST_WRAPPER"):
    _make_request = load_symbol(module.QVAL_MAKE_REQUEST_WRAPPER)
else:

    def _make_request(f):
        """
        Wraps default `utils.make_request()` function. Does nothing.
        """
        return f


def setup_flask_error_handlers(app: "flask.Flask"):
    """
    Setups error handler for APIException.

    :param app: flask app
    :return: None
    """
    from flask import jsonify

    @app.errorhandler(APIException)
    def handle_api_exception(error: APIException):
        response = error.detail
        if isinstance(response, str):
            response = {"error": response}
        response = jsonify(response)
        response.status_code = error.status_code
        return response
