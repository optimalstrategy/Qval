import os
from importlib import reload, import_module

import pytest


@pytest.fixture()
def isolation():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_make_request_wrapper"
    yield None
    del os.environ["DJANGO_SETTINGS_MODULE"]


def test_make_request_wrapper(isolation):
    _ = reload(import_module("qval.framework_integration"))
    make_request = reload(import_module("qval.utils")).make_request
    r = {"param": "value"}
    _ = make_request(r)
    assert make_request.__list__[0] == r


def make_request_wrapper(f):
    def wrapper(request):
        wrapper.__list__.append(request)
        return f(request)

    wrapper.__list__ = []
    return wrapper


QVAL_MAKE_REQUEST_WRAPPER = make_request_wrapper
