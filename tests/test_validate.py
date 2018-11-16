import pytest
from qval import validate, APIException, InvalidQueryParamException
from qval.framework_integration import (
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_400_BAD_REQUEST,
)


def test_params_processed():
    dct = {"num": "42", "double": "2.79", "string": "some string"}
    with validate(dct, num=int, double=float) as p:
        assert p.num == 42
        assert p.double == 2.79
        assert p.string == "some string"


def test_params_omitted():
    dct = {"num": "42", "string": "some string"}
    # Disable auto-detection of parameters (box_all)
    params = validate(dct, num=int, box_all=False)
    with pytest.raises(APIException) as e, params as p:
        assert p.num == 42
        assert p.string == "some string"
    assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_missing_param_throws_error():
    dct = {"param1": "whatever", "param2": "6.66"}
    params = validate(dct, param1=None, param2=float, param3=int)
    with pytest.raises(InvalidQueryParamException) as e, params:
        pass
    assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_validator_factory():
    currency2f = lambda x: float(x[:-1])
    r = {
        "price": "43.5$",
        "n_items": "1",
        "meta": "info",
        "num": 10,
        "num2": 5,
        "token": "0123456789",
    }
    params = (
        validate(
            r, price=currency2f, n_items=int, num=int, num2=int
        ).positive(  # `n_items` must be greater than zero
            "n_items"
        )
        # `num` must be equal to 10
        .eq("num", 10)
        # `num2` must be less than 10
        .lt("num2", 10)
        # Len of `token` must be equal to 10
        .check("token", lambda x: len(x) == 10)
        # The same check as above, but using `transform`
        .eq("token", 10, transform=len)
    )
    with params as p:
        assert {43.5, 1, "info", 10, 5, "0123456789"} == set(p.__dct__.values())


def test_validation_fails():
    currency2f = lambda x: float(x[:-1])
    r = {
        "price": "43.5$",
        "n_items": "0",
        "meta": "info",
        "num": -10,
        "num2": 20,
        "token": "012345678",
    }
    params = (
        validate(
            r, price=currency2f, n_items=int, num=int, num2=int
        ).positive(  # `n_items` must be greater than zero
            "n_items"
        )
        # `num` must be equal to 10
        .eq("num", 10)
        # `num2` must be less than 10
        .lt("num2", 10)
        # Len of `token` must be equal to 10
        .check("token", lambda x: len(x) == 10)
        # The same check as above, but using `transform`
        .eq("token", 10, transform=len)
    )
    with pytest.raises(InvalidQueryParamException) as e, params:
        pass
    assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_exception_handled_in_outside_context():
    """
    See `QueryParamValidator._validate()` and `test_supported_errors_handled()` for more info.
    """
    # Random exception.
    def f(_):
        raise IOError

    r = {"param": "value"}
    with pytest.raises(APIException) as e, validate(r, param=f):
        pass
    assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_supported_errors_handled():
    """
    Only TypeError, ValueError and KeyError that occurred during the validation
    are handled as expected. Any error thrown inside of the context will raise APIError.
    See `test_unsupported_errors_handled()`.
    """

    def exc_factory(exc):
        def f(_):
            raise exc

        return f

    r = {"param": "value"}
    for exc in (TypeError, ValueError, KeyError):
        with pytest.raises(InvalidQueryParamException) as e, validate(
            r, param=exc_factory(exc)
        ):
            pass
        assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_unsupported_errors_handled():
    supported_exceptions = (TypeError, ValueError, KeyError)
    random_exceptions = (IOError, BrokenPipeError, ConnectionError, BufferError)
    r = {"param": "value"}
    for exc in supported_exceptions + random_exceptions:
        with pytest.raises(APIException) as e, validate(r):
            raise exc
        assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
