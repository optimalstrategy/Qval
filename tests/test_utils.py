import os
import pytest

from qval.utils import get_request_params, load_symbol
from tests.crossframework import builder

symbol = lambda x, y: x + y
QVAL_LOGGERS = lambda name: lambda v: f"[{name}]: {v}"


def test_get_request_params_rejects_invalid_objects():
    objects = [object(), {}, [], ()]

    for obj in objects:
        with pytest.raises(AttributeError):
            get_request_params(obj)


def test_get_request_params_accepts_supported_requests():
    for request in builder.iterbuild({"test": "request"}):
        assert isinstance(get_request_params(request), dict)


def test_load_symbol():
    func = load_symbol("tests.test_utils.symbol")
    assert func(30, 12) == 42

    func = load_symbol(symbol)
    assert func is symbol
    assert func(30, 12) == 42


@pytest.fixture()
def envvar():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_utils"
    yield None
    del os.environ["DJANGO_SETTINGS_MODULE"]
