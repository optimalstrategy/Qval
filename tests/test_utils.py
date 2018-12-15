import os
from io import StringIO
import pytest

from qval.utils import get_request_params, log, load_symbol
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


def test_log_detect_loggers(envvar):
    logger = log.detect_loggers(silent=True)

    assert len(logger.factories) == 1
    assert callable(logger.factories[0])

    msg = logger.factories[0]("test")("message")
    assert msg == f"[test]: message"


def test_log_add_loggers():
    buf = StringIO()
    logger = log.detect_loggers()

    logger.add_logger(lambda name: lambda v: buf.write(f"[{name}]: {v}\n"))
    logger.dump("test", "info", "message")

    assert buf.getvalue() == "[test]: message\n"


def test_logging_switch():
    buf = StringIO()
    logger = log.detect_loggers()
    assert logger.is_enabled
    logger.enable()

    logger.add_logger(lambda name: lambda v: buf.write(f"[{name}]: {v}\n"))
    logger.dump("test", "info", "message")
    assert logger.is_enabled
    assert buf.getvalue() == "[test]: message\n"

    logger.disable()
    logger.dump("test", "info", "message")
    assert not logger.is_enabled
    assert buf.getvalue() == "[test]: message\n"


def test_log_errors_handling():
    logger = log.detect_loggers()

    logger.clear()
    logger.add_logger(lambda _: object())

    with pytest.raises(TypeError) as e:
        logger.dump(__file__, "message")
    assert e.type is TypeError
    logger.clear()

    # int("string") raises ValueError.
    # Any errors except the TypeError should be ignored.
    logger.add_logger(lambda _: lambda *__: int("string"))
    logger.dump(__file__, "message")
